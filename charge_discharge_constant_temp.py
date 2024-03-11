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

# ~ Load.fijar_funcion("CURR")
# ~ Load.remote_sense(True)
# ~ Load.fijar_corriente(1.5) #Descargando a C/35
# ~ Load.encender_carga()


# ~ Source.aplicar_voltaje_corriente(4.2,0.1)
# ~ Source.encender_canal(1)

# ~ time.sleep(20)
# ~ Load.apagar_carga()
# ~ Source.apagar_canal(1)

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
    
    
class KeyboardThread(threading.Thread):

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def run(self):
        while True:
            self.input_cbk(input()) #waits to get input + Return

showcounter = 0 #something to demonstrate the change

def my_callback(inp):
    #evaluate the keyboard input
    match inp:
        case "a":
            control = False
            apagar_fuentes()
            print("Turning off peltier drivers")

#start the Keyboard thread
kthread = KeyboardThread(my_callback)
    
    

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
        write.writerows(lista)

def temp_figure():
    ax1 = plt.subplot(211)
    plt.plot(times.data,tavg.data)
    ax2 = plt.subplot(212, sharex=ax1)
    plt.plot(times.data,t1.data)
    plt.plot(times.data,t2.data)
    plt.plot(times.data,t3.data)
    plt.plot(times.data,t4.data)
    plt.setp(ax2.get_xticklabels(),visible=False)

######################## Programa Principal ########################
t = threading.Timer(2.0, ISR)
t.start() #Después de 5 segundos ejecutará lo de medición ()
lista = [] #Para guardar en csv

plt.ion()
fig = plt.figure()

pid = PID(0.5, 0.01, 0.5, setpoint = float(cont_temp))
pid.output_limits = (0,1)


class States:
    Charge = 0
    Discharge = 1

statelist = [States.Charge, States.Discharge]

print(statelist)



def state_machine(state_class, state):
    match state:
        case state_class.Charge:
            fCharge(voltage,current,EOC)
        case state_class.Discharge:
            fDischarge(voltage,current,EOD)


def fCharge(voltage, current, EOC, vmeas, cmeas):
    print("Charge")
    # ~ Source.aplicar_voltaje_corriente(4.2,0.1)
    # ~ Source.encender_canal(1)
    # ~ if cmeas < EOC:
        # ~ state = States.Discharge
        
def fCharge(voltage, current, EOC, vmeas, cmeas):
    print("Charge")
    # ~ Source.aplicar_voltaje_corriente(4.2,0.1)
    # ~ Source.encender_canal(1)
    # ~ if cmeas < EOC:
        # ~ state = States.Discharge


        
class misc:
    def __init__(self, num, text, data):
        self.num = num
        self.text = text
        self.data = data
        

t1 = misc(0,"",[])
t2 = misc(0,"",[])
t3 = misc(0,"",[])
t4 = misc(0,"",[])
tavg = misc(0,"",[])
tref = misc(0,"",[])
times = misc(0,"",[])



def fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref):
    times.num = seconds
    times.text = "{:05.2f}".format(times.num)
    times.data.append(times.num)
    t1.num = measure_temp(0)
    t1.text = "{:05.2f}".format(t1.num)
    t1.data.append(t1.num)
    t2.num = measure_temp(2)
    t2.text = "{:05.2f}".format(t2.num)
    t2.data.append(t2.num)
    t3.num = measure_temp(5)
    t3.text = "{:05.2f}".format(t3.num)
    t3.data.append(t3.num)
    t4.num = measure_temp(7)
    t4.text = "{:05.2f}".format(t4.num)
    t4.data.append(t4.num)
    tavg.num = (t1.num+t2.num+t3.num+t4.num)/4
    tavg.text = "{:05.2f}".format(tavg.num)
    tavg.data.append(tavg.num)
    tref.num = max31855.reference_temperature
    tref.text = "{:05.2f}".format(tref.num)
    tref.data.append(tref.num)
    lista.append([times.text, t1.text, t2.text, t3.text, t4.text, tavg.text, tref.text])
    csv_write(filename)

def protection():
    if (t1.num >= 70) | (t2.num >= 70) | (t3.num >= 70) |  (t4.num >= 70):
        apagar_fuentes()

def relay_control():
    if float(cont_temp) < tref.num:
        GPIO.output(18, GPIO.HIGH)            
    else:   
        GPIO.output(18, GPIO.LOW)            

def build_seconds(past_time, actual_time, seconds):
    actual_time = datetime.now()
    deltat = (actual_time - past_time).total_seconds()
    seconds += deltat
    past_time = actual_time
    
def control_temperatura():
    if control == True:
        controlc = pid(tavg.num)
    if float(cont_temp) < tref.num:
        err = 1 - controlc
    else:
        err = controlc
    Heater1.aplicar_voltaje_corriente(30,round(err*5,2))
    Heater2.aplicar_voltaje_corriente(30,round(err*5,2))

past_time = datetime.now()

while True:
    if timer_flag == 1:
        timer_flag = 0
        fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref)
        protection()
        relay_control()
        actual_time = datetime.now()
        deltat = (actual_time - past_time).total_seconds()
        seconds += deltat
        # ~ build_seconds(past_time, datetime.now(), seconds)
        control_temperatura()
        drawnow(temp_figure)
        past_time = actual_time

GPIO.cleanup() 



