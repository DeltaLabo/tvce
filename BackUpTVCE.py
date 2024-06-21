import pyvisa
from instrument_driver import controller
from PruebasCSV import LecturasVariosCSV
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


# %%% Variables %%%

on = True 
start = False   
timer_flag = 0
seconds = 0
temp = 0
control = False
cont_temp = 0.0
file_date = datetime.now().strftime("%d_%m_%Y_%H_%M")
lista = [] #Para guardar en csv

# %%% Initialize GPIO %%%
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
pins = [18, 19, 20, 21]
for pin in pins:
    GPIO.setup(pin, GPIO.OUT)
    GPIO.output(pin, GPIO.LOW)

# %%% Initialize SPI and MAX31855 %%%
spi = board.SPI()
cs = digitalio.DigitalInOut(board.D5)
max31855 = adafruit_max31855.MAX31855(spi, cs)


# %%% Initialize pyvisa %%%
rm = pyvisa.ResourceManager()
res = rm.list_resources()
print("Cantidad de instrumentos encontrados:", len(res))

# %%% Find and initialize instruments %%%
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

print("Control de temperatura constante")
control = True
print("Temperatura en ºC:")
cont_temp = float(input())  

pid = PID(0.5, 0.01, 0.5, setpoint = cont_temp)
pid.output_limits = (0,1)

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

def my_callback(inp):
    #evaluate the keyboard input
    global start
    global control
    global on
    global state
    global States
    global cont_temp
    global charging_voltage, charging_current, iter_max

    
    match inp:
        case "charge":
            state = States.Charge
            print("Charging the battery")
        case "discharge":
            state = States.Discharge
            print("Discharging the battery")
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
            
            charging_voltage, charging_current, iter_max = LecturasVariosCSV.c_test()
            if charging_voltage != 0 and charging_current != 0 and iter_max != 0:
                start = True
                print("Starting the state machine")
            else:
                start = False
                print("There was a mistake running the state machine")
            
            # ~ start = True
            # ~ print("Starting the state machine")
        case "colder":
            print("decreasing 10ºC")
            cont_temp -= 10
            pid.setpoint = cont_temp
            print(f"Temperatura Actual: {cont_temp}") 
        case "hotter":
            print("Increasing 10ºC")
            cont_temp += 10
            pid.setpoint = cont_temp
            print(f"Temperatura Actual: {cont_temp}") 
        
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
    global lista
    with open(filename, "w+", newline="") as file:
        write = csv.writer(file)
        write.writerows(lista)

def temp_figure():
    ax1 = plt.subplot(411)
    ax1.set_ylim(-15,70)
    plt.plot(times.data[-720:],tavg.data[-720:])
    ax1.set_title("Average Temperature")
    ax1.set_ylabel("Degrees C")
    ax2 = plt.subplot(412, sharex=ax1)
    ax2.set_ylim(-15,70)
    plt.plot(times.data[-720:],t1.data[-720:], label = "T1")
    plt.plot(times.data[-720:],t2.data[-720:], label = "T2")
    plt.plot(times.data[-720:],t3.data[-720:], label = "T3")
    plt.plot(times.data[-720:],t4.data[-720:], label = "T4")
    plt.setp(ax2.get_xticklabels(),visible=False)
    ax2.set_title("Sensor Temperature")
    ax2.set_ylabel("Degrees C")
    ax2.legend()
    ax3 = plt.subplot(413)
    ax3.set_ylim(0,5)
    plt.plot(times.data[-720:], voltage[-720:])
    ax3.set_title("Battery Voltage")
    ax3.set_ylabel("Volts")
    ax4 = plt.subplot(414)
    ax4.set_ylim(0,5)
    plt.plot(times.data[-720:], current[-720:])
    ax4.set_title("Battery Current")
    ax4.set_ylabel("Amps")
    
    fig.text(0.5, 0.01, "State: {}".format(state), ha='center')
    plt.tight_layout()

#Interrupt Service Routine
#Executed in response to an event such as a time trigger or a voltage change on a pin

def ISR():
    global timer_flag
    t = threading.Timer(5.0, ISR) #ISR se ejecuta cada 1 s mediante threading
    t.start()
    timer_flag = 1 #Al iniciar el hilo, el timer_flag pasa a ser 1



t = threading.Timer(5.0, ISR)
t.start()
plt.ion()
fig = plt.figure(figsize=(6.4, 9.6))




class States:
    Idle = 0
    Wait = 1
    Charge = 2
    Discharge = 3
    DC_Res = 4

statelist = [States.Charge, States.Discharge]
# ~ L = len(statelist)


firstCycle = True

def state_machine(States, EOD, EOC):
    global start
    global state
    global firstCycle
    global cycles, index
    global charging_voltage, charging_current, iter_max
    
    L = len(statelist)
    
    if index < L:
        # ~ i=0
        
        # ~ print(start,state)
        match state:
        
            case States.Idle:
                #if start == True:
                    #state = States.Charge
                state = statelist[index]
                    
            case States.Wait:
                # ~ for i in range(L):
                    # ~ state=statelist[i]
                    # ~ i=i+1
                time.sleep(10)
                state = States.Idle
                
            case States.Charge:
                Source.apply_voltage_current(1,charging_voltage, charging_current)
                # ~ Source.toggle_4w()
                Source.turn_on_channel(1)
                drawing_voltage, drawing_current, _ = Source.measure_all(1)
                if firstCycle == True:
                    time.sleep(3)
                    firstCycle = False
                vmeas,cmeas, _ = Source.measure_all(1)
                if cmeas < EOC:
                    state = States.Wait
                    Source.turn_off_channel(1)
                    index += 1
                    
            case States.Discharge:
                Load.set_current(2)
                Load.turn_on_load()
                # vmeas,cmeas, _ = Load.measure_all()
                vmeas,cmeas = Load.measure_all()
                drawing_voltage, drawing_current = Load.measure_all()
                if vmeas < EOD:
                    state = States.Wait
                    Load.turn_off_load()
                    #start = False
                    index += 1

def fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref,draw_volt, draw_curr):
    times.num = seconds / 60
    times.text = "{:05.3f}".format(times.num)
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
    voltage.append(draw_volt)
    current.append(draw_curr)
    lista.append([times.text, t1.text, t2.text, t3.text, t4.text, tavg.text, tref.text, draw_volt, draw_curr, state])
    csv_write(filename)

def protection():
    if (t1.num >= 70) | (t2.num >= 70) | (t3.num >= 70) |  (t4.num >= 70):
        apagar_fuentes()

def relay_control():
    if float(cont_temp) < tref.num:
        GPIO.output(18, GPIO.HIGH)            
    else:   
        GPIO.output(18, GPIO.LOW)            

def build_seconds(actual_time):
    global past_time
    global seconds
    actual_time = datetime.now()
    deltat = (actual_time - past_time).total_seconds()
    seconds += deltat
    past_time = actual_time

def control_temperature():
    global cont_temp
    controlc = 0
    if control == True:
        controlc = pid(tavg.num)
    if cont_temp < tref.num:
        err = 1 - controlc
    else:
        err = controlc
    Heater1.apply_voltage_current(1,30,round(err*5,2))
    Heater2.apply_voltage_current(1,30,round(err*5,2))

class misc:
    def __init__(self, num, text, data):
        self.num = num
        self.text = text
        self.data = data

state = States.Idle
cycles = 0
index = 0
EOD = 3.0
EOC = 0.2 
t1 = misc(0,"",[])
t2 = misc(0,"",[])
t3 = misc(0,"",[])
t4 = misc(0,"",[])
tavg = misc(0,"",[])
tref = misc(0,"",[])
times = misc(0,"",[])
voltage = []
current = []
drawing_voltage = 0
drawing_current = 0
seconds = 0

######################## Programa Principal ########################

past_time = datetime.now()

while on:
    if timer_flag == 1:
        timer_flag = 0
        # ~ print("sec = ", seconds)
        # ~ print("times = ", times.num)
        fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref, drawing_voltage, drawing_current)
        drawing_voltage = 0
        drawing_current = 0
        protection()
        relay_control()
        build_seconds(datetime.now())
        control_temperature()
        if start == True:
            state_machine(States, EOD, EOC)
        if state == States.Charge: #Charge
            drawing_voltage, drawing_current, _ = Source.measure_all(1)
        else: #Discharge or standby
            drawing_voltage, drawing_current = Load.measure_all()
        drawnow(temp_figure)
        # ~ print("flag= ", timer_flag)

GPIO.cleanup() 



