export DefaultImModule=fcitx
export GTK_IM_MODULE=fcitx
export QT_IM_MODULE=fcitx
export XMODIFIERS="@im=fcitx"
cat $HOME/.config/fcitx/profile | sed 's/:True/\&\n/g' | grep \& | sed 's/[,\&]//g' | sed 's/.*=//' > /tmp/fcitx_methods

# dbus-update-activation-environment --sysemd --all

if [ -d /etc/X11/xinit/xinitrc.d ]; then
  for f in /etc/X11/xinit/xinitrc.d/*; do
    [ -x "$f" ] && . "$f"
  done
  unset f
fi

#syndaemon -d -i 0.5 -t -K -R
xmodmap ~/.Xmodmap
xrdb -merge ~/.Xresources
xset -b
exec i3
