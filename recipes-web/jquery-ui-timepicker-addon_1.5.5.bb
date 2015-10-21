DESCRIPTION = "jQuery Timepicker Addon"
SUMMARY = "Adds a timepicker to jQueryUI Datepicker"
HOMEPAGE = "http://trentrichardson.com/examples/timepicker/"

LICENSE = "MIT"
LIC_FILES_CHKSUM = "file://LICENSE-MIT;md5=b8762e3ae9dd561140003de181dda380"

SRC_URI = "git://github.com/trentrichardson/jQuery-Timepicker-Addon.git;tag=v${PV}"

S = "${WORKDIR}/git"

inherit allarch

FILES_${PN} += "${libdir}/remidomo/web/remidomo/static/css/jquery-ui-timepicker-addon.css \
                ${libdir}/remidomo/web/remidomo/static/js/jquery-ui-timepicker-addon.js \
               "

do_install() {
    install -d ${D}/${libdir}/remidomo/web/remidomo/static/css
    install -m 0644 ${S}/dist/jquery-ui-timepicker-addon.css ${D}/${libdir}/remidomo/web/remidomo/static/css

    install -d ${D}/${libdir}/remidomo/web/remidomo/static/js
    install -m 0644 ${S}/dist/jquery-ui-timepicker-addon.js ${D}/${libdir}/remidomo/web/remidomo/static/js
}