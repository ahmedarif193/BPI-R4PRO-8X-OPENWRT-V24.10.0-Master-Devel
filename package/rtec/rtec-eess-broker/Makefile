include $(TOPDIR)/rules.mk

PKG_NAME:=rtec-eess-broker
PKG_VERSION:=1.0
PKG_RELEASE:=1
PKGARCH:=all
PKG_LICENSE:=CLOSED

include $(INCLUDE_DIR)/package.mk

define Package/rtec-eess-broker
  SECTION:=rtec
  CATEGORY:=RTEC
  TITLE:=RTEC EESS broker image configuration
  DEPENDS:=+dnsmasq +firewall4 +mosquitto-ssl +mosquitto-client-ssl \
	+redis-server +redis-cli +redis-utils \
	+openssl-util +ca-bundle +luci-ssl +luci-theme-openwrt-2020 \
	+ip-full +ip-bridge +tcpdump-mini +ethtool +jq +curl \
	+kmod-ipvlan +kmod-veth +kmod-macvlan
endef

define Package/rtec-eess-broker/description
  First-boot configuration and dependencies for an XRCP EESS broker image.
  The package configures the LAN as 192.168.96.1/fd42:96::1, enables DHCP/DNS,
  Mosquitto with plain and TLS listeners, Redis, firewall rules, and lab tools.
endef

define Build/Compile
endef

define Package/rtec-eess-broker/install
	$(CP) ./files/* $(1)/
endef

$(eval $(call BuildPackage,rtec-eess-broker))
