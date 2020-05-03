Music player with Rainbow Hat
-----------------------------

# Installation

    sudo apt-get install bluealsa mpg321 python3-rainbowhat
    pip3 install -r requirements.txt

    # Rainbowhat https://github.com/pimoroni/rainbow-hat
    # To test without
    # curl https://get.pimoroni.com/rainbowhat | bash

## Configure bluetooth speaker

    ./pair-bluetooth-speaker.sh 78:44:05:96:3D:EE
    ./pair-bluetooth-speaker.sh FC:58:FA:A8:72:96

    # Test
    aplay -D bluealsa /usr/share/sounds/alsa/Front_Center.wav

## Configure Autologin

    sudo raspi-config
    # 3 Boot Options > B1 Desktop / CLI > B2 Console Autologin

    echo 'pushd jukebox; ./pair-bluetooth-speaker.sh FC:58:FA:A8:72:96; ./jukebox.py > jukebox.log; popd' >> ~/.bashrc

## Run

    ./jukebox.py

# Troubleshooting

## Check and pair bluetooth device

    # Check Bluetooth interface
    hciconfig

    # Scan for Bluetooth devices
    hcitool scan

    sudo hciconfig hci0 up
    sudo hciconfig hci0 reset

    bluetoothctl
    # agent on
    # default-agent
    # scan on
    # trust $MAC_ADDRESS
    # pair $MAC_ADDRESS
    # connect $MAC_ADDRESS 

### For any problem

    sudo apt-get install pi-bluetooth
    sudo dpkg-reconfigure pi-bluetooth

    # pkill hci
    # sudo systemctl enable bluetooth
    # sudo systemctl enable hciuart
    sudo systemctl restart hciuart
    sudo systemctl restart bluetooth
    sudo systemctl restart bluealsa

    sudo systemctl stop bluetooth
    sudo bluetoothd -d -n

    sudo killall pulseaudio
    sudo killall bluealsa

## Install bluealsa

Install:

    sudo apt-get install -y bluealsa
    sudo service bluealsa start

Configure:

    # nano ~/.asoundrc 
    defaults.bluealsa.interface "hci0"
    defaults.bluealsa.device "78:44:05:96:3D:EE"
    defaults.bluealsa.profile "a2dp"
    defaults.bluealsa.delay 10000 

Test:

    aplay -D bluealsa /usr/share/sounds/alsa/Front_Center.wav

## With Pulse (Not working)

https://github.com/drumfreak/homebridge-bluetooth-soundbutton/wiki/Raspberry-Pi-3---Raspbian-Sretch---Bluetooth-Setup---BlueAlsa-and-Pulse-Audio

    sudo apt-get install -y --no-install-recommends bluez pulseaudio pulseaudio-module-bluetooth

Edit `/etc/pulse/system.pa`:

    cat >> /etc/pulse/system.pa <EOF
    ### Automatically load driver modules for Bluetooth hardware
    .ifexists module-bluetooth-policy.so
    load-module module-bluetooth-policy
    .endif

    .ifexists module-bluetooth-discover.so
    load-module module-bluetooth-discover
    .endif
    EOF

Start pulseaudio:

    pulseaudio --start

## Rainbow Hat

https://github.com/pimoroni/rainbow-hat

## PyBluez

    sudo apt-get install python-dev libbluetooth-dev
    pip3 install PyBluez

## Aplay

https://github.com/Arkq/bluez-alsa

    aplay -D bluealsa:SRV=org.bluealsa,DEV=XX:XX:XX:XX:XX:XX,PROFILE=a2dp /usr/share/sounds/alsa/Front_Center.wav

    aplay -D bluealsa:HCI=hci0,DEV=XX:XX:XX:XX:XX:XX,PROFILE=a2dp /usr/share/sounds/alsa/Front_Center.wav

## Mpg321

    mpg321 -a bluealsa:HCI=hci0,DEV=XX:XX:XX:XX:XX:XX,PROFILE=a2dp /usr/share/sounds/alsa/Front_Center.wav

## Python-VLC

    sudo apt-get install vlc python3-vlc
    # Needs PulseAudio

## MPlayer

http://www.mplayerhq.hu/DOCS/man/fr/mplayer.1.html

    sudo apt-get install mplayer

    mplayer -ao alsa:device=bluealsa test.mp3

## Other

[Headless A2DP Audio Streaming on Raspbian Stretch](https://gist.github.com/Pindar/e259bec5c3ab862f4ff5f1fbcb11bfc1)
