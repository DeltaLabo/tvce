import pyvisa
import controller
import DP711
import time
import RPi.GPIO as GPIO
import board
import digitalio
import adafruit_max31855
from datetime import datetime
import threading
import pandas as pd
import matplotlib.pyplot as plt
from drawnow import drawnow
from simple_pid import PID
import csv
# ~ import maquina_de_estados


class equipment:
    heater1 = "RIGOL TECHNOLOGIES,DP711,DP7A242200986,00.01.05\n"
    heater2 = "RIGOL TECHNOLOGIES,DP711,DP7A242201004,00.01.05\n"
    source = "RIGOL TECHNOLOGIES,DP811A,DP8D235000392,00.01.16\n"
    load = "RIGOL TECHNOLOGIES,DL3021,DL3A213700642,00.01.05.00.01\n"
    
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


rm = pyvisa.ResourceManager()
res = rm.list_resources()
print(len(res))

for i in range(len(res)):
	print(res[i])
	if res[i].find("DL3A21") > 0:
		load = rm.open_resource(rm.list_resources()[i]) 
		print("Carga DL3A21 encontrada")
		print(load.query("*IDN?"))
	elif res[i].find("DP8D23") > 0:
		source = rm.open_resource(rm.list_resources()[i]) 
		print("Fuente DP811A encontrada")
		print(source.query("*IDN?"))
	elif res[i].find("ttyUSB0") > 0:
		heater1 = rm.open_resource(rm.list_resources()[i]) 
		print("Fuente DP711.1 encontrada")
		print(heater1.query("*IDN?"))
	elif res[i].find("ttyUSB1") > 0:
		heater2 = rm.open_resource(rm.list_resources()[i]) 
		print("Fuente DP711.2 encontrada")
		print(heater2.query("*IDN?"))

Heater1 = DP711.Fuente(heater1, "DP711.1")
Heater2 = DP711.Fuente(heater2, "DP711.2")
Load = controller.Carga(load, "DL3021")
Source = DP711.Fuente(source, "DP811A")

Load.fijar_funcion("CURR")
Load.remote_sense(True)
Load.fijar_corriente(1.5) #Descargando a C/35
Load.encender_carga()


Source.aplicar_voltaje_corriente(4.2,0.1)
Source.encender_canal(1)

time.sleep(20)
Load.apagar_carga()
Source.apagar_canal(1)

print("Control de temperatura constante")
control = True
print("Temperatura en ºC:")
cont_temp = input()  

Heater1.aplicar_voltaje_corriente(0,0)
Heater2.aplicar_voltaje_corriente(0,0)
Heater1.encender_canal(1)
Heater2.encender_canal(1)


def apagar_fuentes():
    Heater1.apagar_canal(1)
    Heater2.apagar_canal(1)

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
    try:
        temp = max31855.temperature
    except: 
        temp = 70
    return temp #Measure Temp

base = "/home/delta/tvce_data/"
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
        
        if (t1_num >= 70) | (t2_num >= 70) | (t3_num >= 70) |  (t4_num >= 70):
            apagar_fuentes()
            break
    
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
        print("t = "+time_text+",", "t1 = "+t1_text+",", "t2 = "+t2_text+",", "t3 = "+t3_text+",", "t4 =  "+t4_text+",", "tavg = "+tavg_text+",", "tref = "+tref_text+"")

        past_time = tiempo_actual
        
        
        if control == True:
            
            controlc = pid(tavg_num)
            
            if float(cont_temp) < tref_num:
                err = 1 - controlc
            else:
                err = controlc
            
            Heater1.aplicar_voltaje_corriente(30,round(err*5,2))
            Heater2.aplicar_voltaje_corriente(30,round(err*5,2))



GPIO.cleanup() 



