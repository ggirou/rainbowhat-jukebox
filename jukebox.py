#!/usr/bin/env python3

import signal
import threading
import glob
from rainbowhat import display, lights, weather, rainbow, buzzer, touch, rainbow
from subprocess import Popen, PIPE
from tendo import singleton
from bluetooth import Bluetooth
from display import Display


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
    # args = ['mpg321', '--quiet', '-a', f'bluealsa:SRV=org.bluealsa,DEV={self.__bluetooth.device},PROFILE=a2dp', file]
    # args = ['mplayer', '-ao', 'alsa:device=bluealsa', file]

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


def main():
  singleton.SingleInstance()

  bluetooth = Bluetooth()
  with Display() as display:
    bluetooth.autoconnect()
    with Player(display, bluetooth) as player:
      Buttons(display, player, bluetooth)
      signal.pause()


if __name__ == "__main__":
  main()
