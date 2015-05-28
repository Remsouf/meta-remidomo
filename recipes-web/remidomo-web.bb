DESCRIPTION = "The Remidomo web server"
SUMMARY = "Remidomo web server"
LICENSE = "CC-BY-NC-3.0"
PR = "r0"

RDEPENDS_${PN} = "bash python python-django python-modules python-misc python-flup nginx"

LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/CC-BY-NC-3.0;md5=da665b47544b8cf138600d9e2aeefadd"

SRC_URI = "file://manage.py \
           file://remidomo/static/images \
           file://remidomo/static/css \
           file://remidomo/templates/*.html \
           file://remidomo/*.py \
           file://remidomo/chauffage/*.py \
           file://remidomo/chauffage/templates/*.html \
           file://nginx.conf \
           file://fastcgi \
          "

FILES_${PN} += "${libdir}/remidomo/web/manage.py \
                ${libdir}/remidomo/web/remidomo/static/images \
                ${libdir}/remidomo/web/remidomo/static/css \
                ${libdir}/remidomo/web/remidomo/templates/*.html \
                ${libdir}/remidomo/web/remidomo/*.py \
                ${libdir}/remidomo/web/remidomo/chauffage/*.py \
                ${libdir}/remidomo/web/remidomo/chauffage/templates/*.html \
                ${sysconfdir}/nginx/nginx.conf \
                ${sysconfdir}/init.d/fastcgi \
               "

S = "${WORKDIR}"

INITSCRIPT_PACKAGES = "${PN}"
INITSCRIPT_NAME = "fastcgi"
INITSCRIPT_PARAMS = "defaults"

inherit update-rc.d

do_install() {
    # Create directories and install script
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
    install -m 0755 ${WORKDIR}/fastcgi ${D}/${sysconfdir}/init.d

    # Install Python scripts
    install -d ${D}/${libdir}/remidomo/web
    install -m 0644 ${WORKDIR}/manage.py ${D}/${libdir}/remidomo/web

    # Install project
    install -d ${D}/${libdir}/remidomo/web/remidomo
    install -m 0644 ${WORKDIR}/remidomo/*.py ${D}/${libdir}/remidomo/web/remidomo
    install -d ${D}/${libdir}/remidomo/web/remidomo/static/images
    install -m 0644 ${WORKDIR}/remidomo/static/images/* ${D}/${libdir}/remidomo/web/remidomo/static/images
    install -d ${D}/${libdir}/remidomo/web/remidomo/static/css
    install -m 0644 ${WORKDIR}/remidomo/static/css/* ${D}/${libdir}/remidomo/web/remidomo/static/css
    install -d ${D}/${libdir}/remidomo/web/remidomo/templates
    install -m 0644 ${WORKDIR}/remidomo/templates/* ${D}/${libdir}/remidomo/web/remidomo/templates

    # Install app(s)
    install -d ${D}/${libdir}/remidomo/web/remidomo/chauffage
    install -m 0644 ${WORKDIR}/remidomo/chauffage/*.py ${D}/${libdir}/remidomo/web/remidomo/chauffage
    install -d ${D}/${libdir}/remidomo/web/remidomo/chauffage/templates
    install -m 0644 ${WORKDIR}/remidomo/chauffage/templates/* ${D}/${libdir}/remidomo/web/remidomo/chauffage/templates

    # Overwrite nginx config file
    install -d ${D}/${sysconfdir}/nginx
    install -m 0644 ${WORKDIR}/nginx.conf ${D}/${sysconfdir}/nginx
}

