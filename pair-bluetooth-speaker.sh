#!/bin/bash

[ -z $1 ] && echo -e "Usage:\n\t$0 DEVICE_MAC_ADRESS\n\nExample:\n\t$0 78:44:05:96:3D:EE" && exit 1

MAC_ADDRESS=$1
MAC_ADDRESS_=`echo $MAC_ADDRESS | tr ':' '_'`
# a2dp_sink, headset_head_unit, off
PROFIL=a2dp_sink

bluetoothctl <<-EOF
agent on
default-agent
disconnect
trust $MAC_ADDRESS
pair $MAC_ADDRESS
connect $MAC_ADDRESS
EOF

cat > ~/.asoundrc <<-EOF
defaults.bluealsa.interface "hci0"
defaults.bluealsa.device "$MAC_ADDRESS"
defaults.bluealsa.profile "a2dp"
defaults.bluealsa.delay 10000 
EOF
