include $(TOPDIR)/rules.mk

PKG_NAME:=rtec-eess-simulator
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_DEPENDS:=rtec-xrcp-core protobuf/host python-jinja2/host python-yaml/host
PKG_LICENSE:=CLOSED

LOCAL_RTEC_EESS_SIMULATOR_SRC?=/home/ahmed/WorkDir/TTE/rtec_eess_simulator

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

define Package/rtec-eess-simulator
  SECTION:=rtec
  CATEGORY:=RTEC
  TITLE:=RTEC EESS simulator
  DEPENDS:=+rtec-xrcp-core +libstdcpp +python3-light +python3-yaml
endef

define Package/rtec-eess-simulator/description
  EESS simulator models and launch scripts packaged from the Yocto rtec-eess-simulator recipe source.
endef

define Build/Prepare
	rm -rf $(PKG_BUILD_DIR)
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/build_dir \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/config.yaml \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/simlaunch.py \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/validator.py \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/redis_helper.py \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/redis_monitor.py \
		$(LOCAL_RTEC_EESS_SIMULATOR_SRC)/create-minimal-img.sh \
		$(PKG_BUILD_DIR)/
	rm -rf $(PKG_BUILD_DIR)/build_dir/*/b
	rm -f $(PKG_BUILD_DIR)/build_dir/*/install_manifest.txt
	$(SED) "s#ip_address: localhost#ip_address: 127.0.0.1#g; s#broker_host: localhost#broker_host: fd42:96::1#g" \
		$(PKG_BUILD_DIR)/build_dir/*/*.yaml
	$(SED) 's#/\* ip_address \*/ "localhost"#/* ip_address */ "127.0.0.1"#g; s#/\* broker_host \*/ "localhost"#/* broker_host */ "fd42:96::1"#g' \
		$(PKG_BUILD_DIR)/build_dir/*/src_generated/xrcp_defs.cpp
endef

define RtecEessConfigure
	mkdir -p $(PKG_BUILD_DIR)/openwrt-build/$(1)
	( cd $(PKG_BUILD_DIR)/openwrt-build/$(1); \
		PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" \
		CFLAGS="$(TARGET_CFLAGS) $(EXTRA_CFLAGS) $(TARGET_CPPFLAGS) $(EXTRA_CPPFLAGS)" \
		CXXFLAGS="$(TARGET_CXXFLAGS) $(EXTRA_CXXFLAGS) $(TARGET_CPPFLAGS) $(EXTRA_CPPFLAGS)" \
		LDFLAGS="$(TARGET_LDFLAGS) $(EXTRA_LDFLAGS)" \
		cmake \
			-G Ninja \
			--no-warn-unused-cli \
			-DCMAKE_SYSTEM_NAME=Linux \
			-DCMAKE_SYSTEM_VERSION=1 \
			-DCMAKE_SYSTEM_PROCESSOR=$(ARCH) \
			-DCMAKE_BUILD_TYPE=MinSizeRel \
			-DCMAKE_C_FLAGS_RELEASE="-DNDEBUG" \
			-DCMAKE_CXX_FLAGS_RELEASE="-DNDEBUG" \
			-DCMAKE_C_COMPILER="$(CMAKE_C_COMPILER)" \
			-DCMAKE_CXX_COMPILER="$(CMAKE_CXX_COMPILER)" \
			-DCMAKE_ASM_COMPILER="$(CMAKE_C_COMPILER)" \
			-DCMAKE_EXE_LINKER_FLAGS:STRING="$(TARGET_LDFLAGS)" \
			-DCMAKE_MODULE_LINKER_FLAGS:STRING="$(TARGET_LDFLAGS) $(CMAKE_SHARED_LDFLAGS)" \
			-DCMAKE_SHARED_LINKER_FLAGS:STRING="$(TARGET_LDFLAGS) $(CMAKE_SHARED_LDFLAGS)" \
			-DCMAKE_AR="$(CMAKE_AR)" \
			-DCMAKE_NM="$(CMAKE_NM)" \
			-DCMAKE_RANLIB="$(CMAKE_RANLIB)" \
			-DCMAKE_FIND_ROOT_PATH="$(CMAKE_FIND_ROOT_PATH)" \
			-DCMAKE_FIND_ROOT_PATH_MODE_PROGRAM=NEVER \
			-DCMAKE_FIND_ROOT_PATH_MODE_LIBRARY=ONLY \
			-DCMAKE_FIND_ROOT_PATH_MODE_INCLUDE=ONLY \
			-DCMAKE_STRIP=: \
			-DCMAKE_INSTALL_PREFIX=/usr \
			-DCMAKE_PREFIX_PATH=$(STAGING_DIR) \
			-DCMAKE_SKIP_RPATH=TRUE \
			-DCMAKE_XCRP_INSTALL_PREFIX=/usr/lib/xrcp/models \
			$(PKG_BUILD_DIR)/build_dir/$(1) \
	)
endef

define Build/Configure
	$(call RtecEessConfigure,lineup)
	$(call RtecEessConfigure,poc)
endef

define Build/Compile
	+PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" $(NINJA) -C $(PKG_BUILD_DIR)/openwrt-build/lineup
	+PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" $(NINJA) -C $(PKG_BUILD_DIR)/openwrt-build/poc
endef

define Build/Install
	+PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" DESTDIR="$(PKG_INSTALL_DIR)" $(NINJA) -C $(PKG_BUILD_DIR)/openwrt-build/lineup install
	+PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" DESTDIR="$(PKG_INSTALL_DIR)" $(NINJA) -C $(PKG_BUILD_DIR)/openwrt-build/poc install
	$(INSTALL_DIR) $(PKG_INSTALL_DIR)/opt/rtec
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/config.yaml $(PKG_INSTALL_DIR)/opt/rtec/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/simlaunch.py $(PKG_INSTALL_DIR)/opt/rtec/
	$(INSTALL_BIN) $(PKG_BUILD_DIR)/validator.py $(PKG_INSTALL_DIR)/opt/rtec/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/redis_helper.py $(PKG_INSTALL_DIR)/opt/rtec/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/redis_monitor.py $(PKG_INSTALL_DIR)/opt/rtec/
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/create-minimal-img.sh $(PKG_INSTALL_DIR)/opt/rtec/
	$(SED) 's#/opt/xrcp/lib#/usr/lib/xrcp/models/lib#g; s#/opt/xrcp:/opt/xrcp#/usr/lib/xrcp:/usr/lib/xrcp#g' \
		$(PKG_INSTALL_DIR)/opt/rtec/simlaunch.py
endef

define Package/rtec-eess-simulator/install
	$(INSTALL_DIR) $(1)/usr/lib/xrcp/models
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/xrcp/models/*.so $(1)/usr/lib/xrcp/models/
	$(INSTALL_DIR) $(1)/usr/share/rtec/eess-simulator
	$(CP) $(PKG_INSTALL_DIR)/opt/rtec/* $(1)/usr/share/rtec/eess-simulator/
endef

$(eval $(call BuildPackage,rtec-eess-simulator))
