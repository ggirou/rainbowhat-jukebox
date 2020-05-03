#!/bin/bash

[ -z $1 ] && echo -e "Usage:\n\t$0 DEVICE_MAC_ADRESS\n\nExample:\n\t$0 78:44:05:96:3D:EE" && exit 1

MAC_ADDRESS=$1
MAC_ADDRESS_=`echo $MAC_ADDRESS | tr ':' '_'`
# a2dp_sink, headset_head_unit, off
PROFIL=a2dp_sink

{
echo agent on
echo default-agent
echo scan on
sleep 20
echo disconnect $MAC_ADDRESS
echo untrust $MAC_ADDRESS
echo remove $MAC_ADDRESS
echo disconnect
sleep 2
echo connect $MAC_ADDRESS
echo trust $MAC_ADDRESS
sleep 2
echo pair $MAC_ADDRESS
sleep 2
echo connect $MAC_ADDRESS
sleep 2
echo scan off
sleep 1
} | bluetoothctl

# defaults.bluealsa.service "org.bluealsa"
cat > ~/.asoundrc <<-EOF
defaults.bluealsa.interface "hci0"
defaults.bluealsa.device "$MAC_ADDRESS"
defaults.bluealsa.profile "a2dp"
defaults.bluealsa.delay 10000 
EOF

# Pulse
# pacmd list-cards

# pacmd set-card-profile bluez_card.$MAC_ADDRESS_ $PROFIL

# pacmd set-default-sink bluez_sink.$MAC_ADDRESS_.$PROFIL
# pacmd set-default-source bluez_source.$MAC_ADDRESS_.$PROFIL
