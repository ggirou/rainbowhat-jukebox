#!/usr/bin/env python3

import signal
import threading
import glob
from rainbowhat import display, lights, weather, rainbow, buzzer, touch, rainbow
from subprocess import Popen, PIPE
from tendo import singleton
from bluetooth import Bluetooth
from display import Display
from menu import MenuController, Buttons


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

  def show(self, value=None):
    self.__display.show(value=value, currentAlbum=self.currentAlbum,
                        currentTrack=self.currentTrack, playing=self.playing)

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

  def play(self, file=None, show=True):
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
    if(show):
      self.show()

    thread = threading.Thread(target=self.onProcessExit)
    thread.start()

  def onProcessExit(self):
    _, stderr = self.process.communicate()
    returncode = self.process.returncode
    if(returncode == 0):
      self.next(show=False)
    elif(returncode is not None):
      error = stderr.decode('utf-8')
      print("Error %s: %s" % (returncode, error))
      if(returncode == 1):
        self.show(value="ERR")
        print("Try to reconnect")
        device = self.__bluetooth.reconnect()
        if device is not None:
          self.show(value="OK")

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

  def next(self, show=True):
    print("Next")
    self.currentTrack += 1
    self.play(show=show)

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


def main():
  me = singleton.SingleInstance()

  bluetooth = Bluetooth()
  with Display() as display:
    bluetooth.autoconnect()
    with Player(display, bluetooth) as player:
      controller = MenuController(player, display, bluetooth)
      Buttons(controller)
      signal.pause()


if __name__ == "__main__":
  main()
