#!/usr/bin/env python3

import threading
import time
import colorsys
from rainbowhat import display, rainbow  # , lights, weather, rainbow, buzzer, touch, rainbow


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
    part = 100 / 7

    def setPixels(rotation, opacity=0.1):
      for pixel in range(7):
        h = ((rotation + part * pixel) % 100) / 100.0
        r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, opacity)]
        rainbow.set_pixel(pixel, r, g, b)
        rainbow.show()

    while True:
      for rotation in range(101):
        if not self.__visibleEvent.is_set():
          setPixels(0, opacity=0)
          rainbow.clear()
          rainbow.show()

        if self.__stopEvent.is_set():
          return

        self.__visibleEvent.wait()

        setPixels(rotation)


if __name__ == "__main__":
  with Display() as d:
    while True:
      d.show(value="YEAH")
      time.sleep(6)
      d.show(value="COOL")
      time.sleep(6)
