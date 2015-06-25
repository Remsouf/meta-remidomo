require recipes-core/images/rpi-basic-image.bb

IMAGE_INSTALL += "remidomo-service remidomo-web nginx ntp wpa-supplicant tzdata cronie swupdate swupdate-www u-boot-rpi"

IMAGE_LINGUAS = "fr-fr en-us"

ROOTFS_PREPROCESS_COMMAND += "check_vars;"
ROOTFS_POSTPROCESS_COMMAND += "set_root_passwd; set_wpa_supplicant; set_crontab; install_update_script; install_uboot_env;"

# Also build an image for live updates
IMAGE_FSTYPES = "swupdate-img sdimg-redund"

inherit swupdate-img
SWDESCRIPTION = "${THISDIR}/sw-description"
UPDATE_SCRIPTS = "${THISDIR}/migrate.sh"

inherit sdcard_image_redund


python check_vars() {
    for var in ('WIFI_SSID', 'WIFI_PASSWORD', 'ROOT_PASSWORD', 'ROUTER_ADDR'):
        if bb.data.getVar(var, d, False) is None:
            bb.error('Please provide %s variable, for example in local.conf' % var)
}

python set_root_passwd() {
    import crypt

    password = bb.data.getVar('ROOT_PASSWORD', d, True)
    rootfs = bb.data.getVar('IMAGE_ROOTFS', d, True)

    # Compute hash
    salt = crypt.mksalt(crypt.METHOD_SHA512)
    hashed = crypt.crypt(password, salt)

    # Patch /etc/shadow file
    conffile = os.path.join(rootfs, 'etc/shadow')
    newfile = '%s.new' % conffile
    with open(conffile, 'r') as ifile, open(newfile, 'w') as ofile:
        for line in ifile:
            fields = line.split(':')
            if fields[0] == 'root':
                fields[1] = hashed
                line = ':'.join(fields)

            ofile.write(line)

    os.remove(conffile)
    os.rename(newfile, conffile)
}

python set_wpa_supplicant() {
    import os

    ssid = bb.data.getVar('WIFI_SSID', d, False)
    password = bb.data.getVar('WIFI_PASSWORD', d, False)
    rootfs = bb.data.getVar('IMAGE_ROOTFS', d, True)

    conffile = os.path.join(rootfs, 'etc/wpa_supplicant.conf')
    with open(conffile, 'w') as f:
        f.write('network={\n')
        f.write('  ssid="%s"\n' % ssid)
        if len(password) != 0:
            f.write('  psk="%s"\n' % password)
        else:
            f.write('  key_mgmt=NONE\n')
        f.write('}\n')
}

set_crontab() {
    sed -e "s,##ROUTER_ADDR##,${ROUTER_ADDR}," \
                ${IMAGE_ROOTFS}/${sysconfdir}/crontab > ${IMAGE_ROOTFS}/${sysconfdir}/crontab.new
    mv ${IMAGE_ROOTFS}/${sysconfdir}/crontab.new ${IMAGE_ROOTFS}/${sysconfdir}/crontab
}

install_update_script() {
    install -d ${IMAGE_ROOTFS}/${bindir}
    install -m 0755 ${THISDIR}/update.sh ${IMAGE_ROOTFS}/${bindir}/update.sh
}

install_uboot_env() {
    install -d ${DEPLOY_DIR_IMAGE}/bcm2835-bootfiles
    mkimage -A arm -O linux -T script -C none -n boot.scr -d ${THISDIR}/u-boot.scr ${DEPLOY_DIR_IMAGE}/bcm2835-bootfiles/boot.scr
}