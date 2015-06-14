SUMMARY = "The PiFace Digital input/output module."
HOMEPAGE = "http://pifacedigitalio.readthedocs.org/"
SECTION = "devel/python"
LICENSE = "GPLv3"
LIC_FILES_CHKSUM = "file://COPYING;md5=d32239bcb673463ab874e80d47fae504"

SRCNAME = "pifacedigitalio"

SRC_URI = "git://github.com/piface/pifacedigitalio.git;protocol=http;tag=v${PV}"

S = "${WORKDIR}/git"

inherit setuptools
