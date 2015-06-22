FILESEXTRAPATHS_prepend := "${THISDIR}/overrides/${BPN}:"

SRC_URI += "file://50-update.rules \
            file://10-automount.rules \
           "

do_install_append () {
    install -d ${D}${sysconfdir}/udev/rules.d/
    install -m 0644 ${WORKDIR}/10-automount.rules ${D}${sysconfdir}/udev/rules.d
    install -m 0644 ${WORKDIR}/50-update.rules ${D}${sysconfdir}/udev/rules.d
}
