#!/usr/bin/env python3

import pexpect
import os
import signal
import threading
import time
import glob
import colorsys
import re
from rainbowhat import display, lights, weather, rainbow, buzzer, touch, rainbow
from subprocess import Popen, PIPE
from tendo import singleton


class Display:
  def __init__(self):
    self.__visibleEvent = threading.Event()
    self.__visibleEvent.set()
    self.__stopEvent = threading.Event()
    self.__rainbowThread = threading.Thread(target=self.__rainbow)
    self.__rainbowThread.start()
    self.__clearTimer = threading.Timer(5.0, self.clear)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.clear()
    self.__stopEvent.set()
    self.__visibleEvent.set()

  def show(self, value=None, currentAlbum=1, currentTrack=1, playing=True):
    display.clear()
    if value is not None:
      display.print_str(value)
    elif playing:
      value = '%02d%02d' % (min(currentAlbum + 1, 99), min(currentTrack + 1, 99))
      display.print_str(value)
      display.set_decimal(1, playing)
    else:
      display.print_str(' || ')
    display.show()

    self.__visibleEvent.set()

    self.__clearTimer.cancel()
    self.__clearTimer = threading.Timer(5.0, self.clear)
    self.__clearTimer.start()

  def clear(self):
    self.__visibleEvent.clear()
    self.__clearTimer.cancel()
    display.clear()
    display.show()

  def __rainbow(self):
    s = 100 / 7
    while True:
      for i in range(101):
        for pixel in range(7):
          if not self.__visibleEvent.is_set():
            rainbow.clear()
            rainbow.show()

          if self.__stopEvent.is_set():
            return

          self.__visibleEvent.wait()
          h = ((i + s * pixel) % 100) / 100.0
          # rainbow.clear()
          r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 0.1)]
          rainbow.set_pixel(pixel, r, g, b)
          rainbow.show()


class Player:
  def __init__(self, display, bluetooth, path='music/'):
    self.process = Popen(["echo", "Hello World!"])
    self.playing = False
    def findDir(path): return sorted(glob.glob(path + "**/", recursive=True))
    def findMp3(path): return sorted(glob.glob(path + "*.mp3"))
    self.albums = [album for album in [findMp3(d) for d in findDir(path)] if len(album) > 0]
    self.currentAlbum = 0
    self.currentTrack = 0
    self.macAddress = None
    self.__display = display
    self.__bluetooth = bluetooth
    self.show()

    # print(self.albums)
    # print(self.album)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    self.stop()
    self.__display.__exit__(exc_type, exc_value, traceback)
    self.process.__exit__(exc_type, exc_value, traceback)

  def show(self):
    self.__display.show(currentAlbum=self.currentAlbum, currentTrack=self.currentTrack, playing=self.playing)

  @property
  def currentAlbum(self):
    return self.__currentAlbum

  @currentAlbum.setter
  def currentAlbum(self, value):
    self.__currentAlbum = (value + len(self.albums)) % len(self.albums)
    self.album = self.albums[self.__currentAlbum]

  @property
  def currentTrack(self):
    return self.__currentTrack

  @currentTrack.setter
  def currentTrack(self, value):
    if(value < 0):
      self.currentAlbum -= 1
      self.__currentTrack = (value + len(self.album)) % len(self.album)
    elif(value >= len(self.album)):
      self.currentAlbum += 1
      self.__currentTrack = 0
    else:
      self.__currentTrack = value

  def stop(self):
    self.playing = False
    # if self.process.poll() is not None:
    self.process.send_signal(signal.SIGINT)

  def play(self, file=None):
    if(file is None):
      file = self.album[self.currentTrack]

    self.stop()

    # args = ['mpg123', '-a', 'bluealsa', file]
    args = ['mpg321', '--quiet', '-a', 'bluealsa', file]

    # args = ['sleep', '30000']
    self.process = Popen(args, stdout=PIPE, stderr=PIPE)
    self.playing = True
    print("Playing %s" % file)
    self.show()

    thread = threading.Thread(target=self.onProcessExit)
    thread.start()

  def onProcessExit(self):
    _, stderr = self.process.communicate()
    returncode = self.process.returncode
    if(returncode == 0):
      self.next()
    elif(returncode is not None):
      error = stderr.decode('utf-8')
      print("Error %s: %s" % (returncode, error))
      if(returncode == 1):
        print("Try to reconnect")
        self.__bluetooth.reconnect()

  def pause(self):
    print("Pause")
    self.playing = False
    self.show()
    self.process.send_signal(signal.SIGSTOP)

  def resume(self):
    print("Resume")
    self.playing = True
    self.show()
    self.process.send_signal(signal.SIGCONT)

  def togglePauseResume(self):
    # print("%s" % self.process.poll())
    if self.process.poll() is not None:
      self.play()
    elif self.playing:
      self.pause()
    else:
      self.resume()

  def previous(self):
    print("Previous")
    self.currentTrack -= 1
    self.play()

  def next(self):
    print("Next")
    self.currentTrack += 1
    self.play()

  def previousAlbum(self):
    print("Previous album")
    self.currentAlbum -= 1
    self.currentTrack = 0
    self.play()

  def nextAlbum(self):
    print("Next album")
    self.currentAlbum += 1
    self.currentTrack = 0
    self.play()


class Buttons:
  def __init__(self, display, player, bluetooth):
    self.display = display
    self.player = player
    self.bluetooth = bluetooth
    self.holding = False
    touch.A.press(lambda button: self.press(button))
    touch.B.press(lambda button: self.press(button))
    touch.C.press(lambda button: self.press(button))
    touch.A.release(lambda button: self.release(button))
    touch.B.release(lambda button: self.release(button))
    touch.C.release(lambda button: self.release(button))
    self.commands = ["PLAY", "PAIR", "RSET", "HALT"]
    self.currentCmd = 0
    self.holdTimer = threading.Timer(0, lambda: None)

  def __startHold(self, button):
    self.holdTimer.cancel()
    self.holdTimer = threading.Timer(1.0, self.hold, [button])
    self.holdTimer.start()

  def hold(self, button):
    # print("Hold %s" % button)
    self.holding = True
    if(button == touch.A._index):
      self.player.previousAlbum()
    elif(button == touch.B._index):
      self.currentCmd = (self.currentCmd + 1) % len(self.commands)
      self.display.show(value=self.commands[self.currentCmd])
    elif(button == touch.C._index):
      self.player.nextAlbum()
    self.__startHold(button)

  def press(self, button):
    lights.rgb(int(button == 0), int(button == 1), int(button == 2))
    self.__startHold(button)
    # print("A %s B %s C %s" % (touch.A.pressed, touch.B.pressed, touch.C.pressed))

  def release(self, button):
    lights.rgb(0, 0, 0)
    self.holdTimer.cancel()
    if self.holding:
      self.holding = False
      if(button == touch.B._index):
        cmd = self.commands[self.currentCmd]
        if cmd == "PLAY":
          self.player.show()
        elif cmd == "PAIR":
          print("Auto-Pair")
          self.bluetooth.autopair()
        elif cmd == "RSET":
          print("Reboot")
          self.display.clear()
          Popen(["shutdown", "-r", "now"])
          exit()
        elif cmd == "HALT":
          print("Shutdown")
          self.display.clear()
          Popen(["shutdown", "now"])
          exit()
    elif(button == touch.A._index):
      self.player.previous()
    elif(button == touch.B._index):
      self.player.togglePauseResume()
    elif(button == touch.C._index):
      self.player.next()


class Bluetooth:
  def __init__(self):
    self.device = None

  def __exec(self, commands, timeouts=0, rawCommand=None):
    if rawCommand is None:
      if not isinstance(commands, list):
        commands = [commands]
      if not isinstance(timeouts, list):
        timeouts = [timeouts] * len(commands)
      rawCommand = ('{ %s }' % ''.join(["echo %s; sleep %s; " % (c, t) for (c, t) in zip(commands, timeouts)]))

    print(rawCommand)
    output = os.popen("%s | bluetoothctl" % rawCommand).read()
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


def main():
  # bt = Bluetooth()

  # output = bt.devices()
  # print(output)

  # mac = bt.info()
  # print(mac)
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

  singleton.SingleInstance()

  bluetooth = Bluetooth()
  with Display() as display:
    bluetooth.autoconnect()
    with Player(display, bluetooth) as player:
      Buttons(display, player, bluetooth)
      signal.pause()


if __name__ == "__main__":
  main()
