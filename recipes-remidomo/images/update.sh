#!/bin/bash
UPDATE_LOG=/var/log/update.log
UPDATE_FILE=`find /media/usb*/*.swupdate-img`
if [ -z "$UPDATE_FILE" ]; then
    logger "No update file found on media"
else
    logger "About to trigger update with $UPDATE_FILE, logging to $UPDATE_LOG"
    (swupdate -v -i $UPDATE_FILE > $UPDATE_LOG && reboot) & exit
fi
