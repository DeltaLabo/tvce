import pyvisa
from instrument_driver import controller
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

on = True 
start = False   
timer_flag = 0
past_time = datetime.now()
seconds = 0
temp = 0
control = False
cont_temp = 0
file_date = datetime.now().strftime("%d_%m_%Y_%H_%M")
    
# Initialize GPIO
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
pins = [18, 19, 20, 21]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# Initialize SPI and MAX31855
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max31855 = adafruit_max31855.MAX31855(spi, cs)

# Initialize pyvisa
rm = pyvisa.ResourceManager()
res = rm.list_resources()
print("Cantidad de instrumentos encontrados:", len(res))

# Find and initialize instrumnts
for resource in res:
    if "DL3A21" in resource:
        load = rm.open_resource(resource)
        print("Carga DL3A21 encontrada")
        print(load.query("*IDN?"))
    elif "DP8D23" in resource:
        source = rm.open_resource(resource)
        print("Fuente DP811A encontrada")
        print(source.query("*IDN?"))
    elif "ttyUSB0" in resource:
        heater1 = rm.open_resource(resource)
        heater1.query_delay = 0.4
        print("Fuente DP711.1 encontrada")
        print(heater1.query("*IDN?"))
    elif "ttyUSB1" in resource:
        heater2 = rm.open_resource(resource)
        heater2.query_delay = 0.4
        print("Fuente DP711.2 encontrada")
        print(heater2.query("*IDN?"))

Heater1 = controller.Source(heater1)
Heater2 = controller.Source(heater2)
Load = controller.Load(load)
Source = controller.Source(source)

Load.set_function("CURR")
Load.remote_sense(True)
# ~ Load.set_current(1.5) #Descargando a C/35
# ~ Load.turn_on_load()


# ~ Source.apply_voltage_current(4.2,0.1)
# ~ Source.turn_on_channel(1)

# ~ time.sleep(20)
# ~ Load.turn_off_load()
# ~ Source.turn_off_channel(1)

print("Control de temperatura constante")
control = True
print("Temperatura en ºC:")
cont_temp = input()  

Heater1.apply_voltage_current(1,0,0)
Heater2.apply_voltage_current(1,0,0)
Heater1.turn_on_channel(1)
Heater2.turn_on_channel(1)


def apagar_fuentes():
    Heater1.turn_off_channel(1)
    Heater2.turn_off_channel(1)
    Source.turn_off_channel(1)
    Load.turn_off_load()
    


    
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
    global start
    global control
    global on
    global state
    global States
    match inp:
        case "off":
            control = False
            apagar_fuentes()
            state = States.Idle
            print("Turning off peltier drivers")
        case "stop":
            control = False
            apagar_fuentes()
            on = False
            print("Stopping the process")
        case "start":
            start = True
            print("Starting the state machine")

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

#Interrupt Service Routine
#Executed in response to an event such as a time trigger or a voltage change on a pin
def ISR():
    global timer_flag
    t = threading.Timer(2.0, ISR) #ISR se ejecuta cada 1 s mediante threading
    t.start()
    timer_flag = 1 #Al iniciar el hilo, el timer_flag pasa a ser 1

######################## Programa Principal ########################
t = threading.Timer(2.0, ISR)
t.start() #Después de 5 segundos ejecutará lo de medición ()
lista = [] #Para guardar en csv

plt.ion()
fig = plt.figure()

pid = PID(0.5, 0.01, 0.5, setpoint = float(cont_temp))
pid.output_limits = (0,1)


class States:
    Idle = 0
    Wait = 1
    Charge = 2
    Discharge = 3
    DC_Res = 4

statelist = [States.Charge, States.Discharge]

print(statelist)


firstCycle = True
def state_machine(States, EOD, EOC):
    global start
    global state
    global firstCycle
    # ~ print(start,state)
    match state:
        case States.Idle:
            if start == True:
                state = States.Charge
                print(States.Charge, state)
        case States.Charge:
            print("Charge")
            Source.apply_voltage_current(1,4.2,1.5)
            # ~ Source.toggle_4w()
            Source.turn_on_channel(1)
            if firstCycle == True:
                time.sleep(3)
                firstCycle = False
            vmeas,cmeas, _ = Source.measure_all(1)
            if cmeas < EOC:
                state = States.Discharge
                Source.turn_off_channel(1)
        case States.Discharge:
            print("Discharge")
            Load.set_current(1.5)
            Load.turn_on_load()
            # vmeas,cmeas, _ = Load.measure_all()
            vmeas,cmeas = Load.measure_all()
            if vmeas < EOD:
                state = States.Discharge
                Load.turn_off_load()



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

def build_seconds(past_time, actual_time):
    global seconds
    actual_time = datetime.now()
    deltat = (actual_time - past_time).total_seconds()
    seconds += deltat
    past_time = actual_time
    
def control_temperatura():
    control = 1.0
    if control == True:
        controlc = pid(tavg.num)
    if float(cont_temp) < tref.num:
        err = 1 - controlc
    else:
        err = controlc
    Heater1.apply_voltage_current(1,30,round(err*5,2))
    Heater2.apply_voltage_current(1,30,round(err*5,2))

past_time = datetime.now()

state = States.Idle
EOD = 2.5
EOC = 0.2 

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


    

while on:
    if timer_flag == 1:
        timer_flag = 0
        fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref)
        protection()
        relay_control()
        build_seconds(past_time, datetime.now())
        control_temperatura()
        state_machine(States, EOD, EOC)
        drawnow(temp_figure)
        # past_time = actual_time

GPIO.cleanup() 



