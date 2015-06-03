require recipes-core/images/rpi-basic-image.bb

IMAGE_INSTALL += "remidomo-service remidomo-web nginx ntp wpa-supplicant"

IMAGE_LINGUAS = "fr-fr en-us"

ROOTFS_PREPROCESS_COMMAND += "check_vars;"
ROOTFS_POSTPROCESS_COMMAND += "set_root_passwd; set_wpa_supplicant;"

python check_vars() {
    for var in ('WIFI_SSID', 'WIFI_PASSWORD'):
        if bb.data.getVar(var, d, False) is None:
            bb.error('Please provide %s variable, for example in local.conf' % var)
}

set_root_passwd() {
   sed 's%^root:[^:]*:%root:$6$TKDN96JD$3kwBhlexeWBZscmVxs6tIbA/VUYIEf9hYCKqryqSjHiTqQdZDSQdPhPi4xPkRkGhBCKY1YIAPQHPsLSGJYNC81:%' \
       < ${IMAGE_ROOTFS}/etc/shadow \
       > ${IMAGE_ROOTFS}/etc/shadow.new;
   mv ${IMAGE_ROOTFS}/etc/shadow.new ${IMAGE_ROOTFS}/etc/shadow ;
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
