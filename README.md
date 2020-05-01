Music player with Rainbow Hat
-----------------------------

# Configure bluetooth speaker

## Check and pair bluetooth device

    # Check Bluetooth interface
    hciconfig

    # Scan for Bluetooth devices
    hcitool scan

    sudo ./pair-bluetooth-speaker.sh 78:44:05:96:3D:EE

### For any problem

    sudo hciconfig hci0 up
    sudo hciconfig hci0 reset

    sudo apt-get install pi-bluetooth
    sudo dpkg-reconfigure pi-bluetooth

    # pkill hci
    # sudo service hciuart restart
    # sudo systemctl enable hciuart
    sudo systemctl stop bluetooth
    sudo systemctl stop hciuart
    sudo systemctl start hciuart
    sudo systemctl start bluetooth

    pkill pulseaudio

## Install bluealsa

Install:

    sudo apt-get install -y bluealsa mpg123
    sudo service bluealsa start

Configure:

    # nano ~/.asoundrc 
    defaults.bluealsa.interface "hci0"
    defaults.bluealsa.device "78:44:05:96:3D:EE"
    defaults.bluealsa.profile "a2dp"
    defaults.bluealsa.delay 10000 

Test:

    aplay -D bluealsa /usr/share/sounds/alsa/Front_Center.wav
    mpg123 -a bluealsa test.mp3

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

# Autologin

    sudo raspi-config
    # 3 Boot Options > B1 Desktop / CLI > B2 Console Autologin

TODO .bashrc

# Rainbowhat

https://sourceforge.net/p/raspberry-gpio-python/wiki/Inputs/
