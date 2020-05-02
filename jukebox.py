#!/usr/bin/env python3

import colorsys
import rainbowhat as rh
from rainbowhat import display, lights, weather, rainbow, buzzer, touch
import time
import signal
from subprocess import Popen, PIPE
import asyncio
import glob
import threading
import re

class Player:
  def __init__(self, path='music/'):
    self.process = Popen(["echo", "Hello World!"])
    self.playing = False
    def findDir(path): return sorted(glob.glob(path + "**/", recursive=True))
    def findMp3(path): return sorted(glob.glob(path + "*.mp3"))
    self.albums = [album for album in [findMp3(d) for d in findDir(path)] if len(album) > 0]
    self.currentAlbum = 0
    self.currentTrack = 0
    self.__display()
    # print(self.albums)
    # print(self.album)

  def __enter__(self):
    return self

  def __exit__(self, exc_type, exc_value, traceback):
    display.clear()
    display.show()
    self.stop()
    self.process.__exit__(exc_type, exc_value, traceback)

  def __display(self):
    value = '%02d%02d' % (min(self.__currentAlbum + 1, 99), min(self.__currentTrack + 1, 99))
    display.clear()
    display.print_str(value)
    display.set_decimal(1, True)
    display.show()

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
    self.__display()

    def waitProcessTermination(self):
      _, stderr = self.process.communicate()
      # print("returncode %s" % self.process.returncode)
      if(self.process.returncode == 0):
        self.next()
      elif(self.process.returncode is not None):
        error = stderr.decode('utf-8')
        # error = re.sub('[^\r\n\t!-~]+', ' ', stderr.decode('utf-8')).strip()
        print("Error %s: %s" % (self.process.returncode, error))

    thread = threading.Thread(target=waitProcessTermination, args=[self])
    thread.start()

  def pause(self):
    print("Pause")
    self.process.send_signal(signal.SIGSTOP)
    self.playing = False

  def resume(self):
    print("Resume")
    self.process.send_signal(signal.SIGCONT)
    self.playing = True

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

  def nextAlbum(self):
    print("Next album")


class Buttons:
  def __init__(self, player):
    self.player = player
    touch.A.press(lambda button: self.press(button))
    touch.B.press(lambda button: self.press(button))
    touch.C.press(lambda button: self.press(button))
    touch.A.release(lambda button: self.release(button))
    touch.B.release(lambda button: self.release(button))
    touch.C.release(lambda button: self.release(button))

  def press(self, button):
    lights.rgb(int(button == 0), int(button == 1), int(button == 2))
    # print("A %s B %s C %s" % (touch.A.pressed, touch.B.pressed, touch.C.pressed))

  def release(self, button):
    lights.rgb(0, 0, 0)
    if(button == touch.A._index):
      self.player.previous()
    elif(button == touch.B._index):
      self.player.togglePauseResume()
    elif(button == touch.C._index):
      self.player.next()


with Player() as player:
  Buttons(player)
  signal.pause()


# import os
# os.spawnl(os.P_DETACH, 'some_long_running_command')

# from touch import Buttons as touch

# value = 0
# process = None
# print("A %s B %s C %s" % (touch.A.pressed, touch.B.pressed, touch.C.pressed))
# import RPi.GPIO as GPIO

# def my_callback_one(channel):
#     print('Callback one %s' % channel)

# channel=21
# GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.add_event_detect(channel, GPIO.BOTH)
# GPIO.add_event_callback(channel, my_callback_one)

# channel=20
# GPIO.setup(channel, GPIO.IN, pull_up_down=GPIO.PUD_UP)
# GPIO.add_event_detect(channel, GPIO.BOTH)
# GPIO.add_event_callback(channel, my_callback_one)

# print("A %s\nB %s\nC %s" % (touch.A.__dict__, touch.B.__dict__, touch.C.__dict__))


# def runProcess(args):
#   global process
#   if process != None:
#     # print("Killing " + str(process.pid))
#     process.kill()
#   print("Running " + str(args))
#   process = Popen(args, stdout=PIPE, stderr=PIPE)
#   # stdout, stderr = process.communicate()
#   # returncode = process.returncode
#   # if returncode != 0:
#   #     return "Error: " + stderr.decode('utf-8')
#   # return stdout.decode('utf-8')

# async def pressAsync(button):
#   # print("A %s\nB %s\nC %s" % (touch.A.__dict__, touch.B.__dict__, touch.C.__dict__))
#   print("A %s B %s C %s" % (touch.A.pressed, touch.B.pressed, touch.C.pressed))

# def press(button):
#     print("press %s" % button)
#     lights.rgb(int(button == 0), int(button == 1), int(button == 2))
#     asyncio.run(pressAsync(button))
#     print("Over")
#     # print("A %s\nB %s\nC %s" % (touch.A.__dict__, touch.B.__dict__, touch.C.__dict__))
#     # print("lights %s %s %s" % (int(button == 0), int(button == 1), int(button == 2)))
#     # print("info %s %s %s" % (touch.A, touch.A.noindex, touch.A.members))

# def release(button):
#     print("release %s" % button)
#     file = '/usr/share/sounds/alsa/Front_Center.wav'
#     # file = "music/1 - La Reine des Neiges 2/CD1/01 - La berceuse d'Ahtohallan.flac"
#     runProcess(['aplay', '-D', 'bluealsa', '-N', file])
#     lights.rgb(0, 0, 0)

# async def main():
#     print('hello')
#     touch.A.press(press)
#     touch.B.press(press)
#     touch.C.press(press)
#     touch.A.release(release)
#     touch.B.release(release)
#     touch.C.release(release)
#     await asyncio.sleep(1)
#     print('world')

# asyncio.run(main())

# while True:
#     t = weather.temperature()
#     p = weather.pressure()
#     print(t, p)
#     time.sleep(0.5)


# Pause the main thread so it doesn't exit
# signal.pause()

# exit()

# #######################

# rainbow.set_pixel(0, 255, 0, 0)
# rainbow.show()

# #######################


# while True:
#     for pixel in range(7):
#         rainbow.clear()
#         rainbow.set_pixel(pixel, 255, 0, 0)
#         rainbow.show()
#         time.sleep(0.1)

# #######################


# rainbow.clear()
# rainbow.show()

# while True:
#     for i in range(101):
#         h = i / 100.0
#         r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 1.0)]
#         rainbow.set_all(r, g, b)
#         rainbow.show()
#         time.sleep(0.02)


# #######################


# s = 100 / 7
# while True:
#     for i in range(101):
#         for pixel in range(7):
#             h = ((i + s * pixel) % 100) / 100.0
#             # rainbow.clear()
#             r, g, b = [int(c * 255) for c in colorsys.hsv_to_rgb(h, 1.0, 0.1)]
#             rainbow.set_pixel(pixel, r, g, b)
#             rainbow.show()

# #######################


# display.print_str('AHOY')
# display.show()

# #######################


# i = 0.0

# while i < 999.9:
#     display.clear()
#     display.print_float(i)
#     display.show()
#     i += 0.01

# #######################


# display.clear()
# display.set_decimal(0, True)
# display.show()


# #######################


# @touch.A.press()
# def touch_a(channel):
#     print('Button A pressed')
#     lights.rgb(1, 0, 0)


# @touch.A.release()
# def release_a(channel):
#     print('Button A released')
#     lights.rgb(0, 0, 0)


# #######################


# value = 0


# def show_value(plus):
#     global value
#     value = value + plus
#     display.clear()
#     display.print_float(value)
#     display.show()


# @touch.A.press()
# def touch_a(channel):
#     lights.rgb(1, 0, 0)
#     show_value(-1)


# @touch.A.release()
# def release_a(channel):
#     lights.rgb(0, 0, 0)


# @touch.B.press()
# def touch_b(channel):
#     lights.rgb(0, 1, 0)
#     show_value(+1)


# @touch.B.release()
# def release_b(channel):
#     lights.rgb(0, 0, 0)


# #######################


# while True:
#     t = weather.temperature()
#     p = weather.pressure()
#     print(t, p)
#     time.sleep(0.5)

# #######################


# while True:
#     t = weather.temperature()
#     display.clear()
#     display.print_float(t)
#     display.show()
#     time.sleep(0.5)

# #######################


# buzzer.note(261, 1)

# buzzer.midi_note(60, 1)

# song = [68, 68, 68, 69, 70, 70, 69, 70, 71, 72]

# for note in song:
#     buzzer.midi_note(note, 0.5)
#     time.sleep(1)


# #######################


# while True:
#     if int(time.time()) % 2 == 0:
#         display.print_float(float(time.strftime('%H.%M')))
#     else:
#         display.print_str(time.strftime('%H%M'))
#     display.show()
#     time.sleep(1)
