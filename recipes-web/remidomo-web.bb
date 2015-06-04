DESCRIPTION = "The Remidomo web server"
SUMMARY = "Remidomo web server"
LICENSE = "CC-BY-NC-3.0"
PR = "r0"

RDEPENDS_${PN} = "bash python python-django python-modules python-misc python-flup"

LIC_FILES_CHKSUM = "file://${COMMON_LICENSE_DIR}/CC-BY-NC-3.0;md5=da665b47544b8cf138600d9e2aeefadd"

SRC_URI = "file://manage.py \
           file://remidomo/static/images \
           file://remidomo/static/css \
           file://remidomo/static/js \
           file://remidomo/static/js/images \
           file://remidomo/templates/*.html \
           file://remidomo/*.py \
           file://remidomo/chauffage/*.py \
           file://remidomo/chauffage/templates/*.html \
           file://fastcgi \
          "

FILES_${PN} += "${libdir}/remidomo/web/manage.py \
                ${libdir}/remidomo/web/remidomo/static/images \
                ${libdir}/remidomo/web/remidomo/static/css \
                ${libdir}/remidomo/web/remidomo/static/js \
                ${libdir}/remidomo/web/remidomo/static/js/images \
                ${libdir}/remidomo/web/remidomo/static/admin \
                ${libdir}/remidomo/web/remidomo/templates/*.html \
                ${libdir}/remidomo/web/remidomo/*.py \
                ${libdir}/remidomo/web/remidomo/chauffage/*.py \
                ${libdir}/remidomo/web/remidomo/chauffage/templates/*.html \
                ${sysconfdir}/nginx/nginx.conf \
                ${sysconfdir}/init.d/fastcgi \
               "

S = "${WORKDIR}"

inherit allarch

INITSCRIPT_PACKAGES = "${PN}"
INITSCRIPT_NAME = "fastcgi"
INITSCRIPT_PARAMS = "defaults"

inherit update-rc.d

python do_fetch() {
    if bb.data.getVar('DJANGO_ADMIN_PASSWORD', d, False) is None:
        bb.error('Please provide DJANGO_ADMIN_PASSWORD variable, for example in local.conf')
}

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

    sed -e "s,##ADMIN_PASSWORD##,${DJANGO_ADMIN_PASSWORD}," \
            ${WORKDIR}/fastcgi > ${D}/${sysconfdir}/init.d/fastcgi
    chmod 0755 ${D}/${sysconfdir}/init.d/fastcgi

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
    install -d ${D}/${libdir}/remidomo/web/remidomo/static/js
    install -m 0644 ${WORKDIR}/remidomo/static/js/*.css ${D}/${libdir}/remidomo/web/remidomo/static/js
    install -m 0644 ${WORKDIR}/remidomo/static/js/*.js ${D}/${libdir}/remidomo/web/remidomo/static/js
    install -d ${D}/${libdir}/remidomo/web/remidomo/static/js/images
    install -m 0644 ${WORKDIR}/remidomo/static/js/images/* ${D}/${libdir}/remidomo/web/remidomo/static/js/images
    install -d ${D}/${libdir}/remidomo/web/remidomo/templates
    install -m 0644 ${WORKDIR}/remidomo/templates/* ${D}/${libdir}/remidomo/web/remidomo/templates

    # Install app(s)
    install -d ${D}/${libdir}/remidomo/web/remidomo/chauffage
    install -m 0644 ${WORKDIR}/remidomo/chauffage/*.py ${D}/${libdir}/remidomo/web/remidomo/chauffage
    install -d ${D}/${libdir}/remidomo/web/remidomo/chauffage/templates
    install -m 0644 ${WORKDIR}/remidomo/chauffage/templates/* ${D}/${libdir}/remidomo/web/remidomo/chauffage/templates

    # Install admin static files (just symlink)
    ln -s /usr/lib/python2.7/site-packages/django/contrib/admin/static/admin ${D}/${libdir}/remidomo/web/remidomo/static/admin

    # Directory to contain sqlite DB
    install -m 0777 -d ${D}/${localstatedir}/remidomo
}

