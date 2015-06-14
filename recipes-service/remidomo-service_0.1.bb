DESCRIPTION = "The Remidomo system service to interact with hardware"
SUMMARY = "Remidomo daemon"
LICENSE = "CC-BY-NC-3.0"
PR = "r0"

RDEPENDS_${PN} = "bash python python-modules python-misc python-sqlite3 python-pifacedigitalio python-pifacecommon"

LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/CC-BY-NC-3.0;md5=da665b47544b8cf138600d9e2aeefadd"

SRC_URI = "file://remidomo \
           file://remidomo.py \
           file://config.py \
           file://orders.py \
           file://executor.py \
           file://rfx_listener.py \
           file://xpl_msg.py \
           file://database.py \
           file://remidomo-default-config.xml \
	  "

FILES_${PN} += "${bindir}/remidomo.py \
                ${sysconfdir}/init.d/remidomo \
                ${libdir}/remidomo/service/orders.py \
                ${libdir}/remidomo/service/config.py \
                ${libdir}/remidomo/service/executor.py \
                ${libdir}/remidomo/service/rfx_listener.py \
                ${libdir}/remidomo/service/xpl_msg.py \
                ${libdir}/remidomo/service/database.py \
                ${sysconfdir}/remidomo.xml \
               "

S = "${WORKDIR}"

inherit allarch

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

    install -d ${D}/${bindir}
    sed -e "s,##REMIDOMO_VERSION##,${PV},g" \
        ${WORKDIR}/remidomo.py > ${D}${bindir}/remidomo.py
    chmod 0755 ${D}${bindir}/remidomo.py

    install -d ${D}/${sysconfdir}
    install -m 0666 ${WORKDIR}/remidomo-default-config.xml ${D}/${sysconfdir}/remidomo.xml

    install -d ${D}/${libdir}/remidomo/service
    install -m 0644 ${WORKDIR}/config.py ${D}/${libdir}/remidomo/service
    install -m 0644 ${WORKDIR}/orders.py ${D}/${libdir}/remidomo/service
    install -m 0644 ${WORKDIR}/executor.py ${D}/${libdir}/remidomo/service
    install -m 0644 ${WORKDIR}/rfx_listener.py ${D}/${libdir}/remidomo/service
    install -m 0644 ${WORKDIR}/xpl_msg.py ${D}/${libdir}/remidomo/service
}

