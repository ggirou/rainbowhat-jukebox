#!/usr/bin/env python3

import threading
import signal
import os
from subprocess import Popen
from display import Display
from rainbowhat import display, lights, touch


class MenuController:
  def __init__(self, player, display, bluetooth):
    self.player = PlayerMenu(self, player)
    self.option = OptionMenu(self, display, bluetooth)
    self.goToPlayer()

  def press(self, button):
    self.current.press(button)

  def hold(self, button):
    self.current.hold(button)

  def goToPlayer(self):
    self.current = self.player
    self.current.show()

  def goToOption(self):
    self.current = self.option
    self.current.show()


class PlayerMenu:
  def __init__(self, controller, player):
    self.controller = controller
    self.player = player

  def press(self, button):
    if(button == touch.A._index):
      self.player.previous()
    elif(button == touch.B._index):
      self.player.togglePauseResume()
    elif(button == touch.C._index):
      self.player.next()

  def hold(self, button):
    if(button == touch.A._index):
      self.player.previousAlbum()
    elif(button == touch.B._index):
      self.controller.goToOption()
    elif(button == touch.C._index):
      self.player.nextAlbum()

  def show(self):
    self.player.show()


class OptionMenu:
  def __init__(self, controller, display, bluetooth):
    self.controller = controller
    self.display = display
    self.bluetooth = bluetooth
    self.commands = ["MENU", "PLAY", "PAIR", "RSET", "HALT"]
    self.current = 0

  def press(self, button):
    if(button == touch.A._index):
      self.current = (self.current + len(self.commands) - 1) % len(self.commands)
      self.show()
    elif(button == touch.B._index):
      cmd = self.commands[self.current]
      if cmd == "MENU" or cmd == "PLAY":
        self.current = 0
        self.controller.goToPlayer()
      elif cmd == "PAIR":
        print("Auto-Pair")
        self.bluetooth.autopair()
      elif cmd == "RSET":
        print("Reboot")
        self.display.clear()
        Popen(["shutdown", "-r", "now"])
        os.kill(os.getpid(), signal.SIGINT)
      elif cmd == "HALT":
        print("Shutdown")
        self.display.clear()
        Popen(["shutdown", "now"])
        os.kill(os.getpid(), signal.SIGINT)
    elif(button == touch.C._index):
      self.current = (self.current + 1) % len(self.commands)
      self.show()

  def hold(self, button):
    pass

  def show(self):
    self.display.show(value=self.commands[self.current])


class Buttons:
  def __init__(self, controller):
    self.controller = controller
    self.holding = False
    touch.A.press(lambda button: self.press(button))
    touch.B.press(lambda button: self.press(button))
    touch.C.press(lambda button: self.press(button))
    touch.A.release(lambda button: self.release(button))
    touch.B.release(lambda button: self.release(button))
    touch.C.release(lambda button: self.release(button))
    self.holdTimer = threading.Timer(0, lambda: None)

  def __startHold(self, button):
    self.holdTimer.cancel()
    self.holdTimer = threading.Timer(1.0, self.hold, [button])
    self.holdTimer.start()

  def hold(self, button):
    # print("Hold %s" % button)
    self.holding = True
    self.controller.hold(button)
    self.__startHold(button)

  def press(self, button):
    # print("A %s B %s C %s" % (touch.A.pressed, touch.B.pressed, touch.C.pressed))
    lights.rgb(int(button == 0), int(button == 1), int(button == 2))
    self.__startHold(button)

  def release(self, button):
    lights.rgb(0, 0, 0)
    self.holdTimer.cancel()
    if self.holding:
      self.holding = False
    else:
      self.controller.press(button)


if __name__ == "__main__":
  class PlayerMock:
    def __init__(self):
      self.display = display

    def show(self): self.display.show(value="0101")
    def previous(self): print("previous")
    def next(self): print("next")
    def previousAlbum(self): print("previousAlbum")
    def nextAlbum(self): print("nextAlbum")
    def togglePauseResume(self): print("togglePauseResume")

  class BluetoothMock:
    def autopair(self): print("autopair")

  with Display() as display:
    controller = MenuController(PlayerMock(), display, BluetoothMock())
    Buttons(controller)
    signal.pause()
