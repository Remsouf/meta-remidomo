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

SRC_URI[patch.md5sum] = "4f126912e6d9baa3404593ed03009af4"
SRC_URI[patch.sha256sum] = "6c64e5cc867d3f2db5a7bae85e7513df9fc43a055b8463462e8b2c72ab93c223"

S = "${WORKDIR}/${SRCNAME}-${PV}"

inherit setuptools

do_patch() {
    # Overwrite the obsolete ez_setup.py with the fresh one
    cp ${WORKDIR}/ez_setup.py ${WORKDIR}/${SRCNAME}-${PV}/ez_setup.py
}
