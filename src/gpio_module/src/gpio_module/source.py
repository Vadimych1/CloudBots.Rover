import RPi.GPIO as gpio
import gpiozero
import time

gpio.setmode(gpio.BCM)

led = gpiozero.LED(2)
led.off()

while True:
    led.on()
    time.sleep(0.5)
    led.off()
    time.sleep(0.5)
