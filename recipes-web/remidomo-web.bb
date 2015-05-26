DESCRIPTION = "The Remidomo web server"
SUMMARY = "Remidomo web server"
LICENSE = "CC-BY-NC-3.0"
PR = "r0"

RDEPENDS_${PN} = "bash python python-django python-modules python-misc python-flup"

LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/CC-BY-NC-3.0;md5=da665b47544b8cf138600d9e2aeefadd"

SRC_URI = "file://manage.py \
	   file://remidomo/__init__.py \
	   file://remidomo/urls.py \
           file://remidomo/wsgi.py \
           file://remidomo/settings.py \
           file://remidomo.conf \
          "

FILES_${PN} += "${libdir}/remidomo/web/manage.py \
                ${libdir}/remidomo/web/remidomo/__init__.py \
                ${libdir}/remidomo/web/remidomo/urls.py \
                ${libdir}/remidomo/web/remidomo/wsgi.py \
                ${libdir}/remidomo/web/remidomo/settings.py \
                ${sysconfdir}/nginx/sites-available/remidomo.conf \
               "

S = "${WORKDIR}"

do_install() {
    # Install Python scripts
    install -d ${D}/${libdir}/remidomo/web
    install -m 0644 ${WORKDIR}/manage.py ${D}/${libdir}/remidomo/web

    install -d ${D}/${libdir}/remidomo/web/remidomo
    install -m 0644 ${WORKDIR}/remidomo/__init__.py ${D}/${libdir}/remidomo/web/remidomo
    install -m 0644 ${WORKDIR}/remidomo/urls.py ${D}/${libdir}/remidomo/web/remidomo
    install -m 0644 ${WORKDIR}/remidomo/wsgi.py ${D}/${libdir}/remidomo/web/remidomo
    install -m 0644 ${WORKDIR}/remidomo/settings.py ${D}/${libdir}/remidomo/web/remidomo

    install -d ${D}/${sysconfdir}/nginx/sites-available
    install -m 0644 ${WORKDIR}/remidomo.conf ${D}/${sysconfdir}/nginx/sites-available
    install -d ${D}/${sysconfdir}/nginx/sites-enabled
    ln -s -r ${D}/${sysconfdir}/nginx/sites-available/remidomo.conf ${D}/${sysconfdir}/nginx/sites-enabled/remidomo.conf
}

