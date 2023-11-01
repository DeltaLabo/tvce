import RPi.GPIO as GPIO

#boton = input()

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(16, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

def button_callback(channel):
	print("pulso :\)")

GPIO.add_event_detect(16, GPIO.RISING, callback = button_callback)

message = input("Presione enter para salir :\) \n")

GPIO.cleanup()

