#!/usr/bin/env python3

import os
import signal
import threading
import time
import glob
import colorsys
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
  def __init__(self, display, path='music/'):
    self.process = Popen(["echo", "Hello World!"])
    self.playing = False
    def findDir(path): return sorted(glob.glob(path + "**/", recursive=True))
    def findMp3(path): return sorted(glob.glob(path + "*.mp3"))
    self.albums = [album for album in [findMp3(d) for d in findDir(path)] if len(album) > 0]
    self.currentAlbum = 0
    self.currentTrack = 0
    self.macAddress = None
    self.__display = display
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
        if self.macAddress is None:
          output = os.popen("echo info | bluetoothctl").read()
          self.macAddress = output.split("Device ")[1].split(" ")[0]
        print("Reconnect to %s" % self.macAddress)
        cmd = "{ echo disconnect; sleep 2; echo connect '%s'; sleep 2; echo connect '%s'; sleep 2; } | bluetoothctl" % (
            self.macAddress, self.macAddress)
        output = os.popen(cmd).read()
        print(output)

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
  def __init__(self, display, player):
    self.display = display
    self.player = player
    self.holding = False
    touch.A.press(lambda button: self.press(button))
    touch.B.press(lambda button: self.press(button))
    touch.C.press(lambda button: self.press(button))
    touch.A.release(lambda button: self.release(button))
    touch.B.release(lambda button: self.release(button))
    touch.C.release(lambda button: self.release(button))
    self.commands = ["PLAY", "RSET", "HALT"]
    self.currentCmd = 0

  def __startHold(self, button):
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


def main():
  me = singleton.SingleInstance() 

  with Display() as display:
    with Player(display) as player:
      Buttons(display, player)
      signal.pause()


if __name__ == "__main__":
  main()
