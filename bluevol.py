#!/usr/bin/env python3

import dbus
import sys

DBUS_OM_IFACE = 'org.freedesktop.DBus.ObjectManager'
DBUS_PROP_IFACE = 'org.freedesktop.DBus.Properties'
BLUEZ_SERVICE_NAME = 'org.bluez'
BLUEZ_MT_IFACE = 'org.bluez.MediaTransport1'

VOL_STEP = 5

def usage():
  print("""Usage:
    {0}             Show volume
    {0} <value>     Set volume to <value> (0-127)
    {0} inc         Increase volume
    {0} dec         Decrease volume""".format(sys.argv[0]), file=sys.stderr)
  sys.exit(1)

def main():
  if len(sys.argv) > 2:
    usage()

  bus = dbus.SystemBus()

  om = dbus.Interface(bus.get_object(BLUEZ_SERVICE_NAME, '/'), DBUS_OM_IFACE)
  objects = om.GetManagedObjects()
  path = None

  for obj, props in objects.items():
    if BLUEZ_MT_IFACE in props.keys():
      path = obj
      break

  if path is None:
    # print('No device exists', file=sys.stderr)
    print(-1)
    sys.exit(1)

  vol_now = props[BLUEZ_MT_IFACE]['Volume']

  if len(sys.argv) == 2:
    if sys.argv[1] == 'inc':
      vol = vol_now + VOL_STEP
    elif sys.argv[1] == 'dec':
      vol = vol_now - VOL_STEP
    elif sys.argv[1].isdecimal():
      vol = sys.argv[1]
    else:
      usage() 

    print('{} -> {}'.format(vol_now, vol))

    obj = bus.get_object(BLUEZ_SERVICE_NAME, path)
    props = dbus.Interface(obj, DBUS_PROP_IFACE)
    props.Set(BLUEZ_MT_IFACE, 'Volume', dbus.types.UInt16(vol))
  else:
    print(vol_now)

if __name__ == '__main__':
  main()