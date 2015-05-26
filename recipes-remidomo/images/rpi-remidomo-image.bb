require recipes-core/images/rpi-basic-image.bb

IMAGE_INSTALL += "remidomo-service remidomo-web apache2"

IMAGE_LINGUAS = "fr-fr en-us"

