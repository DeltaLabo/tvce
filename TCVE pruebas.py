############ Código para TVCE ############
# Juan J. Rojas
# Instituto Tecnológico de Costa Rica

import tty
import sys
import termios
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
encender = 0
file_date = datetime.now().strftime("%d_%m_%Y_%H_%M")


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT) #Pin #18 RPi
GPIO.setup(19,GPIO.OUT) #Pin #19 RPi
GPIO.setup(20,GPIO.OUT) #Pin #20 RPi
GPIO.setup(21,GPIO.OUT) #Pin #21 RPi
GPIO.setup(16, GPIO.IN, pull_up_down = GPIO.PUD_DOWN)

GPIO.output(18, GPIO.LOW)
GPIO.output(19, GPIO.LOW)
GPIO.output(20, GPIO.LOW)
GPIO.output(21, GPIO.LOW)

spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max31855 = adafruit_max31855.MAX31855(spi, cs)

#To show connected sources

rm = pyvisa.ResourceManager()
print(rm.list_resources())

#Configure the sources

fuente1 = rm.open_resource(rm.list_resources()[0])
fuente1.write_termination = '\n'
fuente1.read_termination = '\n'
fuente1.baud_rate = 9600
Fuente1 = DP711.Fuente(fuente1, "DP711.1")

fuente2 = rm.open_resource(rm.list_resources()[1])
fuente2.write_termination = '\n'
fuente2.read_termination = '\n'
fuente2.baud_rate = 9600
Fuente2 = DP711.Fuente(fuente2, "DP711.2")



print("Control de temperatura constante")
control = True
print("Temperatura en ºC:")
cont_temp = input() 

# Identity of source
print(fuente1.query("*IDN?"))
print(fuente2.query("*IDN?"))

def encender_fuentes(channel):
    Fuente1.encender_canal(1)
    Fuente2.encender_canal(1)

GPIO.add_event_detect(16, GPIO.RISING, callback = encender_fuentes)

def apagar_fuentes():
    Fuente1.apagar_canal(1)
    Fuente2.apagar_canal(1)


#Interrupt Service Routine
#Executed in response to an event such as a time trigger or a voltage change on a pin
def ISR():
    global timer_flag
    t = threading.Timer(2.0, ISR) #ISR se ejecuta cada 1 s mediante threading
    t.start()
    timer_flag = 1 #Al iniciar el hilo, el timer_flag pasa a ser 1


def measure_temp(channel):
    GPIO.output(19, channel & 0b001)
    GPIO.output(20, (channel & 0b010)>1)
    GPIO.output(21, (channel & 0b100)>2)
    time.sleep(0.2)
    return max31855.temperature #Measure Temp

base = "/home/pi/tvce_data/"
filename = base + "temp_measurements_" + file_date + ".csv"


def csv_write(filename):
    with open(filename, "w+", newline="") as file:
        write = csv.writer(file)
        write.writerows(list)


def temp_figure():
    ax1 = plt.subplot(211)
    plt.plot(time_data,tavg_data)
    ax2 = plt.subplot(212, sharex=ax1)
    plt.plot(time_data,t1_data)
    plt.plot(time_data,t2_data)
    plt.plot(time_data,t3_data)
    plt.plot(time_data,t4_data)
    plt.setp(ax2.get_xticklabels(),visible=False)
   

######################## Programa Principal ########################
t = threading.Timer(2.0, ISR)
t.start() #Después de 5 segundos ejecutará lo de medición ()
list = [] #Para guardar en csv

plt.ion()
fig = plt.figure()

time_data = []
t1_data = []
t2_data = []
t3_data = []
t4_data = []
tavg_data = []
tref_data = []

from simple_pid import PID

pid = PID(0.5, 0.01, 0.5, setpoint = float(cont_temp))
pid.output_limits = (0,1)

while True:

    
    
    if timer_flag == 1:
        
        time_num = seconds
        time_text = "{:05.2f}".format(time_num)
        time_data.append(time_num)
        t1_num = measure_temp(0)
        t1_text = "{:05.2f}".format(t1_num)
        t1_data.append(t1_num)
        t2_num = measure_temp(2)
        t2_text = "{:05.2f}".format(t2_num)
        t2_data.append(t2_num)
        t3_num = measure_temp(5)
        t3_text = "{:05.2f}".format(t3_num)
        t3_data.append(t3_num)
        t4_num = measure_temp(7)
        t4_text = "{:05.2f}".format(t4_num)
        t4_data.append(t4_num)
        tavg_num = (t1_num+t2_num+t3_num+t4_num)/4
        tavg_text = "{:05.2f}".format(tavg_num)
        tavg_data.append(tavg_num)
        tref_num = max31855.reference_temperature
        tref_text = "{:05.2f}".format(tref_num)
        tref_data.append(tref_num)
    
       
        if float(cont_temp) < tref_num:
            GPIO.output(18, GPIO.HIGH)            
        else:   
            GPIO.output(18, GPIO.LOW)            

        
        
        list.append([time_text, t1_text, t2_text, t3_text, t4_text, tavg_text, tref_text])
        csv_write(filename)
        tiempo_actual = datetime.now()
        deltat = (tiempo_actual - past_time).total_seconds()
        seconds += deltat
        timer_flag = 0
        drawnow(temp_figure)
        
#        Mediciones de temperatura
        #print("t = "+time_text+",", "t1 = "+t1_text+",", "t2 = "+t2_text+",", "t3 = "+t3_text+",", "t4 = "+t4_text+",", "tavg = "+tavg_text+",", "tref = "+tref_text+"")

        past_time = tiempo_actual
        

        
        if control == True:
            
            controlc = pid(tavg_num)
            
            if float(cont_temp) < tref_num:
                err = 1 - controlc
            else:
                err = controlc
            
            Fuente1.aplicar_voltaje_corriente(30,round(err*5,2))
            Fuente2.aplicar_voltaje_corriente(30,round(err*5,2))
        


      



GPIO.cleanup() 
