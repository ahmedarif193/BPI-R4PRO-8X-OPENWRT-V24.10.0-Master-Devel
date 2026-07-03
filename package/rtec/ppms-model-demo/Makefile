include $(TOPDIR)/rules.mk

PKG_NAME:=ppms-model-demo
PKG_VERSION:=1.0
PKG_RELEASE:=1

PKG_BUILD_DIR:=$(BUILD_DIR)/$(PKG_NAME)-$(PKG_VERSION)
PKG_BUILD_DEPENDS:=rtec-xrcp-core protobuf/host python-jinja2/host python-yaml/host
PKG_LICENSE:=CLOSED

LOCAL_PPMS_MODEL_DEMO_SRC?=/home/ahmed/WorkDir/TTE/rtec_yocto/poky/meta-saft-pms/recipes-pms/ppms-model-demo/files

CMAKE_INSTALL:=1

include $(INCLUDE_DIR)/package.mk
include $(INCLUDE_DIR)/cmake.mk

TARGET_CFLAGS += -I$(PKG_BUILD_DIR)/inc/arm_compat
TARGET_CXXFLAGS += -I$(PKG_BUILD_DIR)/inc/arm_compat

define Package/ppms-model-demo
  SECTION:=rtec
  CATEGORY:=RTEC
  TITLE:=PPMS model demo
  DEPENDS:=+rtec-xrcp-core +libstdcpp +protobuf
endef

define Package/ppms-model-demo/description
  PPMS demo model packaged from the Yocto ppms-model-demo recipe files.
endef

define Build/Prepare
	rm -rf $(PKG_BUILD_DIR)
	mkdir -p $(PKG_BUILD_DIR)
	$(CP) $(LOCAL_PPMS_MODEL_DEMO_SRC)/. $(PKG_BUILD_DIR)/
endef

CMAKE_OPTIONS += \
	-DCMAKE_BUILD_TYPE=MinSizeRel \
	-DCMAKE_XCRP_INSTALL_PREFIX=/usr/lib/xrcp/models \
	-DProtobuf_PROTOC_EXECUTABLE=$(STAGING_DIR_HOSTPKG)/bin/protoc

define Build/Compile
	+PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" $(NINJA) -C $(CMAKE_BINARY_DIR)
endef

define Build/Install
	+PATH="$(STAGING_DIR_HOSTPKG)/bin:$$$$PATH" DESTDIR="$(PKG_INSTALL_DIR)" $(NINJA) -C $(CMAKE_BINARY_DIR) install
endef

define Package/ppms-model-demo/install
	$(INSTALL_DIR) $(1)/usr/lib/xrcp/models
	$(CP) $(PKG_INSTALL_DIR)/usr/lib/xrcp/models/*.so $(1)/usr/lib/xrcp/models/
endef

$(eval $(call BuildPackage,ppms-model-demo))
