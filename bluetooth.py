#!/usr/bin/env python3

import os
import re
import pexpect


class Bluetooth:
  def __init__(self, debug=False):
    self.__device = None
    self.__debug = debug

  @property
  def device(self):
    return self.__device

  @device.setter
  def device(self, value):
    self.__device = value
    with open(os.environ['HOME'] + "/.asoundrc", "w") as f:
      f.write('defaults.bluealsa.interface "hci0"\n')
      f.write(f'defaults.bluealsa.device "{value}"\n')
      f.write('defaults.bluealsa.profile "a2dp"\n')
      # f.write('defaults.bluealsa.delay 10000\n')

  def __exec(self, commands, timeouts=0, rawCommand=None):
    if rawCommand is None:
      if not isinstance(commands, list):
        commands = [commands]
      if not isinstance(timeouts, list):
        timeouts = [timeouts] * len(commands)
      rawCommand = ('{ %s }' % ''.join(["echo %s; sleep %s; " % (c, t) for (c, t) in zip(commands, timeouts)]))

    print(rawCommand)
    output = os.popen("%s | bluetoothctl" % rawCommand).read()
    if(self.__debug):
      print(output)
    return output

  def __parseDevices(self, output):
    return re.findall('Device ([:A-F0-9]+)', output, re.MULTILINE)

  def info(self):
    # output = os.popen("{ echo info; sleep 5; } | bluetoothctl --timeout 5").read()
    output = self.__exec("info")
    devices = self.__parseDevices(output)
    self.device = next(iter(devices), None)
    return self.device

  def pairedDevices(self):
    output = self.__exec("paired-devices")
    return self.__parseDevices(output)

  def scan(self, timeout=5):
    output = self.__exec("scan on", timeouts=timeout)
    return self.__parseDevices(output)

  def pair(self, device, timeout=20):
    # "scan on",
    output = self.__exec(["scan on", "trust " + device, "pair " + device], timeouts=[0, timeout, 2])
    trust = "trust succeeded" in output
    pair = "Pairing successful" in output or "Failed to pair: org.bluez.Error.AlreadyExists" in output
    print("trust %s; pair %s" % (trust, pair))
    return trust and pair and self.connect(device)
    # if 'Connection successful' in output:
    #   return device
    # else:
    #   return None

  def unpair(self, device, timeout=2):
    output = self.__exec(["untrust " + device, "remove " + device], timeouts=timeout)
    untrust = "untrust succeeded" in output
    remove = "remove succeeded" in output
    print("untrust %s; remove %s" % (untrust, remove))

  def autopair(self, timeout=5, tries=3, pairedDevices=None):
    pass

  def autoconnect(self, timeout=5, tries=3, pairedDevices=None):
    print("Autoconnect timeout=%s, tries=%s" % (timeout, tries))
    currentDevice = self.info()
    if currentDevice is not None:
      print("Already connected to %s" % currentDevice)
      return currentDevice

    if pairedDevices is None:
      pairedDevices = self.pairedDevices()
    print("pairedDevices: %s" % pairedDevices)
    # scannedDevices = self.scan(timeout=timeout)
    # connectableDevices = set(pairedDevices) & set(scannedDevices)
    # print("scannedDevices: %s" % scannedDevices)
    # print("connectableDevices: %s" % connectableDevices)
    for device in pairedDevices:
      result = self.connect(device)
      if result is not None:
        return result
    # if len(pairedDevices) > 0:
    #   return self.connect(pairedDevices[1])
    # elif len(connectableDevices) > 0:
    #   return self.connect(connectableDevices.pop())
    # elif tries > 0:
    #   return self.autoconnect(timeout=timeout*2, tries=tries-1, pairedDevices=pairedDevices)
    # else:
    #   return None

  def connect(self, device, timeout=2):
    output = self.__exec("connect %s" % device, timeouts=timeout)
    if 'Connection successful' in output:
      self.device = device
      return device
    else:
      return None

  def disconnect(self, device='', timeout=1):
    if device == '' and self.device is not None:
      device = self.device
    output = self.__exec("disconnect %s" % device, timeouts=timeout)
    self.device = None
    return "Successful disconnected" in output

  def reconnect(self):
    device = self.info()
    self.disconnect()
    if device is None:
      return self.autoconnect()
    else:
      return self.connect(device)
    # print("Try to reconnect")
    # if self.device is None:
    #   output = os.popen("echo info | bluetoothctl").read()
    #   self.device = output.split("Device ")[1].split(" ")[0]
    # print("Reconnect to %s" % self.device)
    # cmd = "{ echo disconnect; sleep 2; echo connect '%s'; sleep 2; echo connect '%s'; sleep 2; } | bluetoothctl" % (
    #     self.device, self.device)
    # output = os.popen(cmd).read()
    # print(output)


def triesWithPexpect():
  ctl = pexpect.spawn('bluetoothctl')
  ctl.expect('^.+# ')
  ctl.sendline('agent on')
  ctl.expect('^.+registered')
  ctl.expect('^.+# ')
  ctl.sendline('default-agent')
  ctl.expect('^.+successful')
  # ctl.sendline('scan on')
  # ctl.expect('^.+# ')
  # time.sleep(5)
  # ctl.expect('Device ([:A-F0-9]+)')
  # print(ctl.__dict__)
  # # print(str(ctl.before))
  # # print(str(ctl.after))
  # print(str(ctl.match))
  # time.sleep(5)
  # print(str(ctl.before))
  # ctl.sendline('scan off')
  # print(str(ctl.before))
  # output = __exec("devices")
  ctl.sendline('devices')
  time.sleep(2)
  # ctl.expect('Device ([:A-F0-9]+)')

  output = ctl.expect(['Device ([:A-F0-9]+)', '^[^\x1b]+# '])
  # output = ctl.expect('^.+# ')
  print(output)
  # print(ctl.read())
  print(ctl.before)
  print(ctl.after)
  print(ctl.match)
  print(ctl.__dict__)
  # return __parseDevices(output)


if __name__ == "__main__":
  bt = Bluetooth(debug=True)

  # output = bt.devices()
  # print(output)

  device = bt.info()
  print(device)
  # mac = '78:44:05:96:3D:EE'

  # device = bt.unpair(mac)
  # print(device)

  # device = bt.pair(mac)
  # print(device)

  # device = bt.autopair()
  # print(device)

  # devices = bt.pairedDevices()
  # print(devices)

  # devices = bt.scan()
  # print(devices)

  # device = bt.disconnect()
  # print(device)

  # device = bt.connect('78:44:05:96:3D:EE')
  # print(device)

  # device = bt.reconnect()
  # print(device)
