#!/usr/bin/env python3
# deploy_serial.py - TFTP-deploy the freshly built image to a MediaTek Filogic
# board (BananaPi BPI-R4 family) by driving its U-Boot over the serial console.
#
# What it does:
#   1. stages <board>-initramfs-recovery.itb (+ sysupgrade) into the tftpd root
#   2. breaks into U-Boot with Ctrl-C  (NEVER bare Enter: this U-Boot repeats the
#      last command on an empty Enter, which can run away / hang it)
#   3. sets serverip and runs `boot_tftp`  -> TFTP the recovery and boot it in RAM
#
# Usage:  python3 scripts/deploy_serial.py [board] [action]
#   board  : bananapi_bpi-r4 (default) | bananapi_bpi-r4-poe | bananapi_bpi-r4-pro-8x
#   action : nand-install (default) - TFTP-write bl2+fip+recovery+production to NAND (persistent)
#            | emmc-install - TFTP-write bl2(boot0)+fip+gpt+recovery+production to eMMC (persistent)
#            | tftp-boot  - TFTP-boot the recovery into RAM (non-persistent test)
#            | flash-sd   - dd the sdcard.img to a USB SD reader, then nand-install
#            | sync       - mirror all images to /srv/tftp, no serial
#
# Adjust the CONFIG block for a different tree / TFTP host / serial port.

import os, sys, time, glob, shutil, subprocess
import serial   # pyserial

# ---------------- CONFIG ----------------
WORKDIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))   # .../openwrt
IMG_DIR   = os.path.join(WORKDIR, "bin/targets/mediatek/filogic")
TFTP_DIR  = "/srv/tftp"
SERVER_IP = "192.168.1.254"          # this host (tftpd); was 192.168.1.2
PROMPT    = b"MT7988>"
BAUD      = 115200
# ----------------------------------------

BOARD  = sys.argv[1] if len(sys.argv) > 1 else "bananapi_bpi-r4"
ACTION = sys.argv[2] if len(sys.argv) > 2 else "nand-install"
PFX    = "openwrt-mediatek-filogic-%s-" % BOARD
RECOVERY = PFX + "initramfs-recovery.itb"
SYSUP    = PFX + "squashfs-sysupgrade.itb"

# All TFTP-relevant artifacts a bpi-r4 U-Boot bootmenu may request. Exact names
# (not a glob) so bananapi_bpi-r4 / -poe / -pro-8x never collide. Missing files
# are skipped silently.
SUFFIXES = [
    "initramfs-recovery.itb",   # bootfile      (recovery)         menu: Boot/Load recovery
    "squashfs-sysupgrade.itb",  # bootfile_upg  (production OS)     menu: Load production
    "emmc-preloader.bin",       # bootfile_bl2  (eMMC BL2)          menu: write BL2 to eMMC
    "emmc-preloader-8g.bin",    #               (8 GiB-RAM SKU)
    "emmc-bl31-uboot.fip",      # bootfile_fip  (eMMC FIP)          menu: write FIP to eMMC
    "emmc-gpt.bin",             # GPT           (manual `gpt write`)
    "snand-preloader.bin",      # bootfile_bl2  (SPI-NAND BL2)
    "snand-preloader-8g.bin",
    "snand-bl31-uboot.fip",     # bootfile_fip  (SPI-NAND FIP)
    "snand-factory.bin",        # full NAND factory image (if built)
]

def stage(name):
    src = os.path.join(IMG_DIR, name)
    if not os.path.isfile(src):
        return False
    dst = os.path.join(TFTP_DIR, name)
    shutil.copyfile(src, dst); os.chmod(dst, 0o644)
    print("  + %-58s %10d B" % (name, os.path.getsize(dst))); return True

def flash_sdcard():
    """Find a removable USB disk (SD reader), dd the board's sdcard.img onto it,
    then wait for the user to move the card to the board and reach U-Boot."""
    img = os.path.join(IMG_DIR, PFX + "sdcard.img")
    if not os.path.isfile(img):
        print("!! SD image not found: %s" % img); sys.exit(2)

    def usb_removable(name):
        base = "/sys/block/%s" % name
        try:
            if open(base + "/removable").read().strip() == "1": return True
        except Exception: pass
        try:
            if "usb" in os.path.realpath(base + "/device").lower(): return True
        except Exception: pass
        return False  # refuse fixed/internal disks - never dd a system drive

    def find_sd():
        for name in ("sda", "sdb", "sdc", "sdd"):
            if os.path.isdir("/sys/block/%s" % name) and usb_removable(name):
                return "/dev/" + name, name
        return None, None

    print("\n== Connect the SD card (USB reader) ==")
    dev = name = None; end = time.time() + 180
    while time.time() < end:
        dev, name = find_sd()
        if dev: break
        sys.stdout.write("  waiting for a removable USB disk (e.g. /dev/sda)...\r"); sys.stdout.flush()
        time.sleep(1.5)
    if not dev:
        print("\n!! no removable USB disk appeared -- is the SD reader plugged in?"); sys.exit(2)

    try: model = open("/sys/block/%s/device/model" % name).read().strip()
    except Exception: model = "?"
    try: gib = int(open("/sys/block/%s/size" % name).read().strip()) * 512 / (1024.0 ** 3)
    except Exception: gib = 0.0
    print("\n== target: %s  (%s, %.1f GiB, removable) ==" % (dev, model, gib))
    print("== flashing %s -> %s ==" % (os.path.basename(img), dev))
    cmd = ["dd", "if=" + img, "of=" + dev, "bs=4M", "status=progress", "conv=fsync"]
    if not os.access(dev, os.W_OK): cmd = ["sudo"] + cmd   # block device is root-owned
    if subprocess.run(cmd).returncode != 0:
        print("!! dd failed"); sys.exit(2)
    subprocess.run(["sync"])
    print("== SD card flashed OK -- now move it to the board and power on ==")

print("== board=%s  action=%s ==" % (BOARD, ACTION))
print("== syncing %s TFTP artifacts -> %s ==" % (BOARD, TFTP_DIR))
synced = sum(stage(PFX + suf) for suf in SUFFIXES)
print("  (%d files synced)" % synced)
if not os.path.isfile(os.path.join(TFTP_DIR, RECOVERY)):
    print("!! %s not built in %s -- nothing to deploy" % (RECOVERY, IMG_DIR)); sys.exit(2)

if ACTION == "sync":
    print("== sync-only done =="); sys.exit(0)

if ACTION == "flash-sd":
    flash_sdcard()   # dd the SD card, then block until you're at the U-Boot prompt

# --- connect to U-Boot over serial -------------------------------------------
# Free the port FIRST. If picocom (or any monitor) is still attached to the tty,
# two processes read the same port and pyserial aborts on the first read with
# "device ... returned no data (... multiple access on port?)" -- that was the bug.
subprocess.run(["pkill", "-x", "picocom"], stderr=subprocess.DEVNULL)
time.sleep(0.5)

# Wait for "go": gives you time to swap the SD / reboot and reach the U-Boot prompt.
try:
    input("\n>>> Get the board to the U-Boot '%s' prompt (swap SD / reboot if needed),\n"
          ">>> then press ENTER here to connect and run '%s'... " % (PROMPT.decode(), ACTION))
except EOFError:
    pass

PORT = None
def open_port(wait=60):
    """Search ttyACM*/ttyUSB* (the port re-enumerates on a power-cycle) and open
    it EXCLUSIVELY so nothing can race us on it."""
    global PORT
    end = time.time() + wait; lasterr = "no port found"
    while time.time() < end:
        for p in sorted(glob.glob("/dev/ttyACM*")) + sorted(glob.glob("/dev/ttyUSB*")):
            try:
                s = serial.Serial(p, BAUD, timeout=0.2, rtscts=False, dsrdtr=False, exclusive=True)
                PORT = p; return s
            except Exception as e:
                lasterr = str(e)
        sys.stdout.write("  waiting for a free serial port (is picocom closed?) ...\r"); sys.stdout.flush()
        time.sleep(1.0)
    print("\n!! no usable serial port: %s" % lasterr); sys.exit(2)

print("== searching for serial port ==")
ser = open_port(60)
print("== serial: %s @ %d ==" % (PORT, BAUD))

def emit(b): sys.stdout.write(b.decode("utf-8", "replace")); sys.stdout.flush()

def _reopen():
    global ser
    try: ser.close()
    except Exception: pass
    time.sleep(0.5); ser = open_port(60)

def _read(n):                       # survive board reset / USB re-enumeration
    global ser
    try: return ser.read(n)
    except serial.SerialException: _reopen(); return b""

def _write(data):                   # raw write (no input flush) - for Ctrl-C spam
    global ser
    try: ser.write(data); ser.flush()
    except serial.SerialException: _reopen(); ser.write(data); ser.flush()

def _send(data):                    # flush stale input, then write - for commands
    global ser
    try: ser.reset_input_buffer(); ser.write(data); ser.flush()
    except serial.SerialException: _reopen(); ser.reset_input_buffer(); ser.write(data); ser.flush()

def wait_prompt(t):
    b = b""; end = time.time() + t
    while time.time() < end:
        d = _read(4096)
        if d:
            b += d; emit(d)
            if b.rstrip().endswith(PROMPT):
                time.sleep(0.2); x = _read(8192)
                if x: b += x; emit(x)
                return b, True
    return b, False

def cmd(c, t):
    print("\n>>> %s" % c); _send((c + "\n").encode()); return wait_prompt(t)

# Sync to U-Boot: ASK first (echo) in case we're already at the prompt; only
# Ctrl-C if needed to interrupt a bootdelay=0 autoboot. NEVER bare Enter (this
# U-Boot repeats the last command on an empty Enter).
def echo_sync(t=6):
    _send(b"echo SYNCOK\n")
    b, ok = wait_prompt(t)
    return ok and b"SYNCOK" in b

LINUX_MARKS = [b"Starting kernel", b"Linux version", b"BusyBox", b" login:", b"procd",
               b"root@", b"Please press Enter to activate this console", b"OpenWrt"]

print("== syncing to U-Boot prompt ==")
state = "prompt" if echo_sync(6) else None
if state is None:
    print("== not at prompt; Ctrl-C to break in (power-cycle the board now if it's idle) ==")
    buf = b""; last = 0; end = time.time() + 60
    while time.time() < end:
        now = time.time()
        if now - last > 0.15: _write(b"\x03"); last = now
        d = _read(2048)
        if d:
            emit(d); buf = (buf + d)[-3000:]
            if any(k in buf for k in LINUX_MARKS): state = "linux"; break
            if buf.rstrip().endswith(PROMPT): state = "prompt"; break
    if state == "prompt" and not echo_sync(6): state = None
if state == "linux":
    print("\n!! board is in OpenWrt, not U-Boot -- power-cycle it and re-run."); ser.close(); sys.exit(4)
if state != "prompt":
    print("\n!! never reached U-Boot prompt -- board powered? picocom closed?"); ser.close(); sys.exit(4)

# deploy
cmd("setenv serverip %s" % SERVER_IP, 8)
if ACTION == "tftp-boot":
    cmd("setenv bootfile %s" % RECOVERY, 8)
    print("\n== TFTP-booting the new build into RAM (run boot_tftp) ==")
    _send(b"run boot_tftp\n")
    b = b""; end = time.time() + 90; ok = False
    while time.time() < end:
        d = _read(4096)
        if d:
            b += d; emit(d)
            if any(k in b[-500:] for k in [b"Starting kernel", b"Linux version", b"procd", b"Please press Enter", b"BusyBox"]):
                ok = True; break
    print("\n== DEPLOY %s ==" % ("OK - booting the new build (RAM, non-persistent)" if ok else "UNCERTAIN - check console"))

elif ACTION in ("nand-install", "flash-sd"):
    # bpi-r4 NAND: bl2 @0 (2M), ubi @0x200000 (starts right at 2M -> NO gap, unlike
    # the R4-Pro). TFTP-populate via the firmware's own ubi_* macros (no SD reads).
    print("\n== installing the new build to NAND (persistent) ==")
    o, _k = cmd("nand info", 15)
    if (b"spi-nand" not in o) and (b"NAND" not in o):
        print("\n!! NAND not detected -- aborting, nothing written"); ser.close(); sys.exit(4)
    steps = [
        ("run ubi_format", 90),                                                              # erase+attach ubi
        ("tftpboot $loadaddr %ssnand-preloader.bin && run snand_write_bl2"  % PFX, 90),       # BL2 -> bl2 mtd
        ("tftpboot $loadaddr %ssnand-bl31-uboot.fip && run ubi_write_fip"   % PFX, 90),       # FIP -> ubi vol
        ("run ubi_create_env", 20),                                                          # ubootenv vols
        ("tftpboot $loadaddr %sinitramfs-recovery.itb && run ubi_write_recovery"  % PFX, 180),
        ("tftpboot $loadaddr %ssquashfs-sysupgrade.itb && run ubi_write_production" % PFX, 240),
    ]
    ok = True
    for c, t in steps:
        _o, done = cmd(c, t)
        if not done:
            ok = False; print("\n!! step did not return to prompt: %s" % c); break
    print("\n== NAND-INSTALL %s ==" % ("OK -- set the boot switch to NAND and power-cycle"
                                       if ok else "INCOMPLETE -- check the log above"))

elif ACTION == "emmc-install":
    # eMMC uses a GPT (not UBI). Write BL2->boot0, FIP, GPT, then recovery+production
    # to the GPT partitions -- each TFTP'd directly, so (unlike the menu's option 9)
    # there is NO dependency on a NAND 'emmc_install' volume.
    print("\n== installing the new build to eMMC (persistent) ==")
    o, _k = cmd("mmc partconf 0", 15)
    if any(k in o for k in [b"no mmc", b"not available", b"did not respond", b"Card did not", b"No MMC"]):
        print("\n!! eMMC not detected -- aborting, nothing written"); ser.close(); sys.exit(4)
    cmd("mmc dev 0", 15)
    cmd("mmc bootbus 0 0 0 0", 10)
    steps = [
        ("tftpboot $loadaddr %semmc-preloader.bin && run emmc_write_bl2"  % PFX, 60),   # BL2 -> boot0
        ("tftpboot $loadaddr %semmc-bl31-uboot.fip && run emmc_write_fip" % PFX, 60),   # FIP
        ("tftpboot $loadaddr %semmc-gpt.bin && run emmc_write_hdr"        % PFX, 30),   # GPT -> sector 0
        ("mmc rescan", 15),                                                            # re-read partitions
        ("tftpboot $loadaddr %sinitramfs-recovery.itb && run emmc_write_recovery"  % PFX, 180),
        ("tftpboot $loadaddr %ssquashfs-sysupgrade.itb && run emmc_write_production" % PFX, 240),
    ]
    ok = True
    for c, t in steps:
        _o, done = cmd(c, t)
        if not done:
            ok = False; print("\n!! step did not return to prompt: %s" % c); break
    print("\n== EMMC-INSTALL %s ==" % ("OK -- set the boot switch to eMMC and power-cycle"
                                       if ok else "INCOMPLETE -- check the log above"))
else:
    print("!! unknown action %r" % ACTION)
ser.close()
