# Create an archive to be used as update file for swupdate

inherit image_types

# This image depends on the rootfs image
SWU_ROOTFS_TYPE = "ext3.gz"
IMAGE_TYPEDEP_swupdate-img = "${SWU_ROOTFS_TYPE}"

IMAGE_DEPENDS_rpi-sdimg = " \
			virtual/kernel \
			${IMAGE_BOOTLOADER} \
			"

# The archive to create
SWUPDATE_FILE = "${DEPLOY_DIR_IMAGE}/${IMAGE_NAME}.rootfs.swupdate-img"
SWU_WORK_DIR = "${WORKDIR}/swupdate-img"

# File names into the archive
SWDESCRIPTION_NAME = "${@os.path.basename(d.getVar('SWDESCRIPTION', True))}"
ROOTFS_NAME = "${IMAGE_NAME}.rootfs.${SWU_ROOTFS_TYPE}"
KERNEL_NAME = "${KERNEL_IMAGETYPE}${KERNEL_INITRAMFS}-${MACHINE}.bin"

# Contents of the archive
SWDESCRIPTION_FILE = "${SWU_WORK_DIR}/${SWDESCRIPTION_NAME}"
ROOTFS_FILE = "${DEPLOY_DIR_IMAGE}/${ROOTFS_NAME}"
KERNEL_FILE = "${DEPLOY_DIR_IMAGE}/${KERNEL_NAME}"

IMAGE_CMD_swupdate-img () {
    test -n "${SWDESCRIPTION}" || { echo "Please define SWDESCRIPTION !" >&2; exit 1; }

    echo "Creating ${SWDESCRIPTION_FILE} file..."
    mkdir -p ${SWU_WORK_DIR}
    rm -f ${SWU_WORK_DIR}/*
    sed -e "s|#ROOTFS#|${ROOTFS_NAME}|" \
        -e "s|#KERNEL#|${KERNEL_NAME}|" \
        ${SWDESCRIPTION} > ${SWDESCRIPTION_FILE}

    echo "Archiving into ${SWUPDATE_FILE}..."
    FILES="${ROOTFS_FILE} ${KERNEL_FILE} ${UPDATE_SCRIPTS}"
    for i in $FILES; do cp $i ${SWU_WORK_DIR}; done

    cd ${SWU_WORK_DIR}

    # Description file always comes first
    echo ${SWDESCRIPTION_NAME} | cpio -o -H crc -O ${SWUPDATE_FILE}

    find . -not -name ${SWDESCRIPTION_NAME} -type f | cpio -oA -H crc -O ${SWUPDATE_FILE}
}