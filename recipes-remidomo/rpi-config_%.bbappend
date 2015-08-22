do_deploy_append() {
    echo "dtparam=spi=on" >>${DEPLOYDIR}/bcm2835-bootfiles/config.txt
    echo "arm_freq_min=300" >>${DEPLOYDIR}/bcm2835-bootfiles/config.txt
    echo "core_freq_min=250" >>${DEPLOYDIR}/bcm2835-bootfiles/config.txt
}
