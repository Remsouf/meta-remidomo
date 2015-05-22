DESCRIPTION = "The Remidomo system service to interact with hardware"
SUMMARY = "Remidomo daemon"
LICENSE = "CC-BY-NC-3.0"
PR = "r0"

RDEPENDS_${PN} = "bash python python-modules python-misc"

LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/CC-BY-NC-3.0;md5=da665b47544b8cf138600d9e2aeefadd"

SRC_URI = "file://remidomo \
	   file://remidomo.py \
	   file://config.py \
	   file://orders.py \
	   file://remidomo-default-config.xml \
	  "

FILES_${PN} += "${bindir}/remidomo.py \
                ${sysconfdir}/init.d/remidomo \
                ${libdir}/remidomo/orders.py \
                ${libdir}/remidomo/config.py \
                ${sysconfdir}/remidomo.xml \
               "

S = "${WORKDIR}"

INITSCRIPT_PACKAGES = "${PN}"
INITSCRIPT_NAME = "remidomo"
INITSCRIPT_PARAMS = "defaults"

inherit update-rc.d

do_install() {
    # Create directories and install scripts
    install -d ${D}/${sysconfdir}/init.d
    install -d ${D}/${sysconfdir}/rcS.d
    install -d ${D}/${sysconfdir}/rc0.d
    install -d ${D}/${sysconfdir}/rc1.d
    install -d ${D}/${sysconfdir}/rc2.d
    install -d ${D}/${sysconfdir}/rc3.d
    install -d ${D}/${sysconfdir}/rc4.d
    install -d ${D}/${sysconfdir}/rc5.d
    install -d ${D}/${sysconfdir}/rc6.d
    install -d ${D}/${sysconfdir}/default
    install -m 0755 ${WORKDIR}/remidomo ${D}/${sysconfdir}/init.d

    install -d ${D}/usr/bin
    install -m 0755 ${WORKDIR}/remidomo.py ${D}/${bindir}

    install -d ${D}/etc
    install -m 0644 ${WORKDIR}/remidomo-default-config.xml ${D}/${sysconfdir}/remidomo.xml

    install -d ${D}/usr/lib/remidomo
    install -m 0644 ${WORKDIR}/config.py ${D}/${libdir}/remidomo
    install -m 0644 ${WORKDIR}/orders.py ${D}/${libdir}/remidomo
}

