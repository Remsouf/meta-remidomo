SUMMARY = "Random assortment of WSGI servers"
HOMEPAGE = "http://www.saddi.com/software/flup/"
SECTION = "devel/python"
LICENSE = "BSD"
LIC_FILES_CHKSUM = "file://PKG-INFO;md5=696e79307557359c74a11f55b4c85a36"

SRCNAME = "flup"

SRC_URI = "https://pypi.python.org/packages/source/f/${SRCNAME}/${SRCNAME}-${PV}.tar.gz;name=tarball \
           https://bootstrap.pypa.io/ez_setup.py;name=patch \
	  "

SRC_URI[tarball.md5sum] = "a005b072d144fc0e44b0fa4c5a9ba029"
SRC_URI[tarball.sha256sum] = "6649cf41854ea8782c795cdde64fdf79a90db821533d3652f91d21b0a7f39c79"

SRC_URI[patch.md5sum] = "da46dad94c2cafa335a72dd8b682c3f7"
SRC_URI[patch.sha256sum] = "20a7da79f7fb158857d9c1dc66f2e81f5c88e8c50de4d82e434c7a05146c1b11"

S = "${WORKDIR}/${SRCNAME}-${PV}"

inherit setuptools

do_patch() {
    # Overwrite the obsolete ez_setup.py with the fresh one
    cp ${WORKDIR}/ez_setup.py ${WORKDIR}/${SRCNAME}-${PV}/ez_setup.py
}
