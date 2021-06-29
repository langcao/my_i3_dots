reply_action () {echo reply_action}
forward_action () {echo forward_action}
handle_dismiss () {echo	handle_dismiss}

ACTION=$(dunstify --action="default,Reply" --action="forwardAction,Forward" "Message Received")

case "$ACTION" in
"default")
    reply_action
    ;;
"forwardAction")
    forward_action
    ;;
"2")
    handle_dismiss
    ;;
esac