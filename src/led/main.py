import RGBLib
import time
import random
import machine

colors = ["red", "green", "yellow", "blue", "orange", "pink", "purple", "cyan", "white"]


# LED CONTROLLER
LED = RGBLib.Controller(4,26,27)

print("boot")
LED.boot()
time.sleep(2)

print("escolha")
LED.set(colors[random.randrange(0, 8)])
time.sleep(2)

print("dormiu")
machine.deepsleep(1000)