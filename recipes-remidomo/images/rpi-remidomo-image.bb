require recipes-core/images/rpi-basic-image.bb

IMAGE_INSTALL += "remidomo-service remidomo-web nginx"

IMAGE_LINGUAS = "fr-fr en-us"

