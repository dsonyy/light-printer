# Single GPIO LED Control

LED_PIN = 21

try:
	import RPi.GPIO as gpio

	def init():
		print("Initializing GPIOs (signle LED).")
		gpio.setmode(gpio.BCM)
		gpio.setup(LED_PIN, gpio.OUT)
		print("LED Pin number: ", LED_PIN)

	def on():
		gpio.output(LED_PIN, gpio.HIGH)

	def off():
		gpio.output(LED_PIN, gpio.LOW)


except ModuleNotFoundError:
	print("ERR! GPIO Module not found.")

	def init():
		pass

	def on():
		pass

	def off():
		pass

