############ Código para TVCE ############
# Juan J. Rojas
# Instituto Tecnológico de Costa Rica

import pyvisa
import DP711
import time
from time import sleep
import threading
import pandas as pd
from datetime import datetime
import RPi.GPIO as GPIO
import board 
import digitalio
import adafruit_max31855
import csv
import matplotlib.pyplot as plt
from drawnow import drawnow


timer_flag = 0
past_time = datetime.now()
seconds = 0
temp = 0
control = False
cont_temp = 0
file_date = datetime.now().strftime("%d_%m_%Y_%H_%M")


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT) #Pin #18 RPi
GPIO.setup(19,GPIO.OUT) #Pin #19 RPi
GPIO.setup(20,GPIO.OUT) #Pin #20 RPi
GPIO.setup(21,GPIO.OUT) #Pin #21 RPi

GPIO.output(18, GPIO.LOW)
GPIO.output(19, GPIO.LOW)
GPIO.output(20, GPIO.LOW)
GPIO.output(21, GPIO.LOW)

spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max31855 = adafruit_max31855.MAX31855(spi, cs)

#To show connected sources

rm = pyvisa.ResourceManager()

res = rm.list_resources()
print("Equipos Conectados")
print(res ,"\n")
print("Cantidad de Equipos Detectados:")
print(len(res),"\n")

#ESTA PARTE LEE LOS ONSTRUMENTOS Y BUSCA Y ASIGA LAS FUENTES 1 Y 2 SEGUN ID

for inst in range(len(res)): 
    insti = rm.open_resource(rm.list_resources()[inst])
    print(inst)
    try:
        insti.write("*IDN?")
        time.sleep(0.2)
        aux = insti.read()
    except:
        print("Not VISA")
    match aux:
        case "RIGOL TECHNOLOGIES,DP711,DP7A242200986,00.01.05":
            print("Heater1")
        case "RIGOL TECHNOLOGIES,DP711,DP7A242201004,00.01.05":
            print("Heater2")
            
    
    # ~ if inst != 2:
        # ~ print("Numero de Equipo:")
        # ~ print(inst,"\n")
        # ~ insti = rm.open_resource(rm.list_resources()[inst])
        # ~ insti.write("*IDN?")
        # ~ time.sleep(0.2)
        # ~ #print(insti.read())
        # ~ insti.write("*IDN?")
        # ~ time.sleep(0.2)
        # ~ aux = insti.read()
        # ~ #if aux == "RIGOL TECHNOLOGIES,DP711,DP7A242200986,00.01.05":
        # ~ if aux == "RIGOL TECHNOLOGIES,DP711,DP7A242200986,00.01.05\n":
            # ~ print("Heater 1 Asignado:")
            # ~ fuente1 = rm.open_resource(rm.list_resources()[inst])
            # ~ fuente1.write("*IDN?")
            # ~ fuente1.baud_rate = 9600
            # ~ Heater1 = DP711.Fuente(fuente1, "DP711.1")
            # ~ print("\n")
            # ~ time.sleep(10)
        # ~ elif aux == "RIGOL TECHNOLOGIES,DP711,DP7A242201004,00.01.05\n":
            # ~ print("Heater 2 Asignado:")
            # ~ fuente2 = rm.open_resource(rm.list_resources()[inst])
            # ~ fuente2.write("*IDN?")
            # ~ fuente2.baud_rate = 9600
            # ~ Heater2 = DP711.Fuente(fuente2, "DP711.1")
            # ~ print("\n")
            # ~ time.sleep(10)
        # ~ elif aux == "RIGOL TECHNOLOGIES,DP811A,DP8D235000392,00.01.16\n":
            # ~ print("Fuente 1 Asignada:")
            # ~ fuente3 = rm.open_resource(rm.list_resources()[inst])
            # ~ fuente3.write("*IDN?")
            # ~ fuente3.baud_rate = 9600
            # ~ Fuente1 = DP711.Fuente(fuente3, "DP711.1")
            # ~ print("\n")
            # ~ time.sleep(0.2)
        # ~ elif aux == "RIGOL TECHNOLOGIES,DL3021,DL3A213700642,00.01.04.00.05\n":
            # ~ print("Carga Electronica Asignada:")
            # ~ fuente2 = rm.open_resource(rm.list_resources()[inst])
            # ~ fuente2.write("*IDN?")
            # ~ fuente2.baud_rate = 9600
            # ~ Carga_elec = DP711.Fuente(fuente2, "DP711.1")
            # ~ print("\n")
            # ~ time.sleep(0.2)
        # ~ else:
            # ~ print(aux)
            # ~ print("sistema no reconocido en la base de datos")
    
