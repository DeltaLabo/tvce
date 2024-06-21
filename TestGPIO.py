import pyvisa
import time
import RPi.GPIO as GPIO
import board
import digitalio
import adafruit_max31855
import threading
import csv

GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
pins = [17, 27]

for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)
    
class States:
	Idle = 1
	Charge = 2
	Discharge =  3
	Dc_res= 4

def relay_sense_and_power(state): 
	global States
	match state:
		case States.Charge:
			GPIO.output(17, GPIO.HIGH)            
			GPIO.output(27, GPIO.LOW)
		case (States.Idle | States.Discharge | States.DC_res):
			GPIO.output(17, GPIO.LOW)            
			GPIO.output(27, GPIO.HIGH)
relay_sense_and_power(3)
