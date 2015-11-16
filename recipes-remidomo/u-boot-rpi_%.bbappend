FILESEXTRAPATHS_prepend := "${THISDIR}/overrides/${BPN}:"

SRC_URI += "file://0001-Add-linux-compiler-gcc5.patch \
            file://0002-Fix-external-symbol-aliasing.patch"

