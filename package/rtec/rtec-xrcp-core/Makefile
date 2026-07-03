include $(TOPDIR)/rules.mk

PKG_NAME:=rtec-xrcp-core
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_DEPENDS:=nlohmannjson hiredis libssh libuv libyaml-cpp iptables
PKG_LICENSE:=CLOSED

LOCAL_RTEC_XRCP_CORE_SRC?=/home/ahmed/WorkDir/TTE/rtec_xrcp_core

CMAKE_INSTALL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

define Package/rtec-xrcp-core
  SECTION:=rtec
  CATEGORY:=RTEC
  TITLE:=RTEC XRCP core runtime
  DEPENDS:=+libstdcpp +libmodbus +libhiredis +libssh +libuv +libyaml-cpp \
	+libip4tc +libip6tc +libxtables
endef

define Package/rtec-xrcp-core/description
  XRCP core loader, Modbus plugins, and public model ABI header.
endef

define Build/Prepare
	rm -rf $(PKG_BUILD_DIR)
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/CMakeLists.txt \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/ext_modbus \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/ext_redis \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/ext_restapi \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/ext_server \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/inc \
		$(LOCAL_RTEC_XRCP_CORE_SRC)/so-loader \
		$(PKG_BUILD_DIR)/
	$(SED) 's#std::string model_lib_path = "/opt/xrcp/lib";#std::string model_lib_path = std::string(XCRP_INSTALL_PREFIX) + "/models/lib";#' \
		$(PKG_BUILD_DIR)/so-loader/container_manager.cpp
endef

CMAKE_OPTIONS += \
	-DCMAKE_BUILD_TYPE=MinSizeRel \
	-DCMAKE_INSTALL_PREFIX=/usr \
	-DCMAKE_XCRP_INSTALL_PREFIX=/usr/lib/xrcp \
	-DBUILD_TESTS=OFF \
	-DMINIMAL=OFF \
	-DSO_LOADER_MINIMAL=OFF \
	-DBUILD_EXT_MQTT=OFF \
	-DBUILD_EXT_REDIS=ON \
	-DBUILD_EXT_RESTAPI=ON \
	-DNATIVE_OPTIMIZATION=OFF

define Build/InstallDev
	$(call Build/InstallDev/cmake,$(1))
	$(INSTALL_DIR) $(1)/usr/include
	$(INSTALL_DATA) $(PKG_BUILD_DIR)/inc/xrcp_types.h $(1)/usr/include/
endef

define Package/rtec-xrcp-core/install
	$(INSTALL_DIR) $(1)/usr/bin
	$(INSTALL_BIN) $(PKG_INSTALL_DIR)/usr/bin/so-loader $(1)/usr/bin/
	$(INSTALL_DIR) $(1)/usr/lib
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/libxrcp.so* $(1)/usr/lib/
	$(INSTALL_DIR) $(1)/usr/lib/xrcp/plugins
	$(CP) $(PKG_INSTALL_DIR)/usr/plugins/*.so $(1)/usr/lib/xrcp/plugins/
	$(INSTALL_DIR) $(1)/etc/xrcp
	$(INSTALL_CONF) $(PKG_INSTALL_DIR)/usr/config.yaml $(1)/etc/xrcp/
endef

$(eval $(call BuildPackage,rtec-xrcp-core))
