SUMMARY = "Common functions for interacting with PiFace products"
HOMEPAGE = "http://pifacecommon.readthedocs.org/"
SECTION = "devel/python"
LICENSE = "GPLv3"
LIC_FILES_CHKSUM = "file://COPYING;md5=d32239bcb673463ab874e80d47fae504"

SRCNAME = "pifacecommon"

SRC_URI = "git://github.com/piface/pifacecommon.git;protocol=http;tag=v${PV}"

S = "${WORKDIR}/git"

inherit setuptools
