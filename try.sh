scrot_notification_id=780
notify-send.sh -r $scrot_notification_id -u low 'Scrot gets ready to grab.' 'Select a rectangle area...'

scrot -s "/tmp/screencut_temp.jpg"
if [[ -f "/tmp/screencut_temp.jpg" ]]; then
	if [ -f "/tmp/screen_target" ]; then
		PATH_SEL=$(cat /tmp/screen_target)
	else
		notify-send.sh -r $scrot_notification_id -u low 'Screen image grabbed.' 'Specify a directory...'
		PATH_SEL=$(zenity --file-selection --title=" Choose a directory" --directory)
		if [[ $PATH_SEL ]]; then
			echo $PATH_SEL > /tmp/screen_target
		else
			notify-send.sh -r $scrot_notification_id -u low 'Aborting shot. No image saved.'
		fi
	fi
else
	notify-send.sh -r $scrot_notification_id -u low 'Aborting shot. No image grabbed.'
fi

if [[ $PATH_SEL ]]; then
	notify-send.sh -r $scrot_notification_id -u low 'Screen image grabbed.' 'Specify a filename...'
    GRAB_NAME=$(zenity --entry --title " Specify a filename" --text "$PATH_SEL" --entry-text="figure" --width=400)
    if [[ $GRAB_NAME ]]; then
    	FILENAME="${PATH_SEL}/${GRAB_NAME}.jpg"
    	if [[ -f "$FILENAME" ]]; then
    		GRAB_NAME=$(zenity --entry --title " Specify a filename" --text "$GRAB_NAME.jpg already exists. Overwrite?" --entry-text="$GRAB_NAME" --width=400)
    		if [[ $GRAB_NAME ]]; then
    			FILENAME="${PATH_SEL}/${GRAB_NAME}.jpg"
    			mv /tmp/screencut_temp.jpg "${FILENAME}"
				notify-send.sh -r $scrot_notification_id -u low 'Screen image grabbed.' 'JPG file overwritten.'
				# feh "${FILENAME}"
			else
				notify-send.sh -r $scrot_notification_id -u low 'Aborting shot. No image saved.'
	    	fi
	    else
	    	mv /tmp/screencut_temp.jpg "${FILENAME}"
			notify-send.sh -r $scrot_notification_id -u low 'Screen image grabbed.' 'Grabbed image saved..'
			# feh "${FILENAME}"
    	fi
    else
		notify-send.sh -r $scrot_notification_id -u low 'Aborting shot. No image saved.'
    fi
fi