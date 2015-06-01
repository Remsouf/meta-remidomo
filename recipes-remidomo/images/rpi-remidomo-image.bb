require recipes-core/images/rpi-basic-image.bb

IMAGE_INSTALL += "remidomo-service remidomo-web nginx"

IMAGE_LINGUAS = "fr-fr en-us"

ROOTFS_POSTPROCESS_COMMAND += "set_root_passwd;"
set_root_passwd() {
   sed 's%^root:[^:]*:%root:$6$TKDN96JD$3kwBhlexeWBZscmVxs6tIbA/VUYIEf9hYCKqryqSjHiTqQdZDSQdPhPi4xPkRkGhBCKY1YIAPQHPsLSGJYNC81:%' \
       < ${IMAGE_ROOTFS}/etc/shadow \
       > ${IMAGE_ROOTFS}/etc/shadow.new;
   mv ${IMAGE_ROOTFS}/etc/shadow.new ${IMAGE_ROOTFS}/etc/shadow ;
}

