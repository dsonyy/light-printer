# Single GPIO LED Control
import RPi.GPIO as gpio

LED_PIN = 21

def init():
	print("Initializing GPIOs (signle LED).")
	gpio.setmode(gpio.BCM)
	gpio.setup(LED_PIN, gpio.OUT)
	print("LED Pin number: ", LED_PIN)

def on():
	gpio.output(LED_PIN, gpio.HIGH)

def off():
	gpio.output(LED_PIN, gpio.LOW)
