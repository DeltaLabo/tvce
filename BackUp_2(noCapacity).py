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
import numpy as np
import matplotlib.pyplot as plt
from drawnow import drawnow
from simple_pid import PID
import csv

deltat = 2.5
statelist=[]
start = False   
temp = 0
control = False
cont_temp = 0.0
file_date = datetime.now().strftime("%d_%m_%Y_%H_%M")
lista = [] #Para guardar en csv

# %%% Initialize GPIO %%%
GPIO.setwarnings(False)
GPIO.setmode(GPIO.BCM)
pins = [17, 18, 19, 20, 21, 27]
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
        # ~ print(load.query("*IDN?"))
    elif "DP8D23" in resource:
        source = rm.open_resource(resource)
        print("Fuente DP811A encontrada")
        # ~ print(source.query("*IDN?"))
    elif "ttyUSB0" in resource:
        heater1 = rm.open_resource(resource)
        heater1.query_delay = 0.4
        print("Fuente DP711.1 encontrada")
        # ~ print(heater1.query("*IDN?"))
    elif "ttyUSB1" in resource:
        heater2 = rm.open_resource(resource)
        heater2.query_delay = 0.4
        print("Fuente DP711.2 encontrada")
        # ~ print(heater2.query("*IDN?"))


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



####################Functions##################

def apagar_fuentes():
    Heater1.turn_off_channel(1)
    Heater2.turn_off_channel(1)
    Source.turn_off_channel(1)
    Load.turn_off_load()
    

def my_callback(inp):
    #evaluate the keyboard input
    global start
    global control
    global on
    global state
    global States
    global cont_temp
    global statelist
    global charging_voltage, charging_current, discharging_current, iter_max, wait_time, EOD, EOC

    
    match inp:
        case "charge":
            state = States.Charge
            print("Charging the battery")
        case "discharge":
            state = States.Discharge
            print("Discharging the battery")
        case "off":
            apagar_fuentes()
            control = False
            print("Turning off peltier drivers")
        case "stop":
            index = 0
            state = States.Idle
            print("Stopping the state machine")
        case "start":
            iter_max, wait_time, charging_voltage, charging_current, discharging_current, EOC, EOD, statelist = LecturasVariosCSV.get_values("test_config.csv")
            if charging_voltage != 0 and charging_current != 0 and iter_max != 0:
                start = True
                print("Starting the state machine")
            else:
                start = False
                print("There was a mistake running the state machine")
        case "colder":
            print("decreasing 10ºC")
            cont_temp -= 10
            pid.setpoint = cont_temp
            print(f"Temperatura Actual: {cont_temp}") 
        case "hotter":
            print("increasing 10ºC")
            cont_temp += 10
            pid.setpoint = cont_temp
            print(f"Temperatura Actual: {cont_temp}") 
    # ~ return iter_max, wait_time, charging_voltage, charging_current, discharging_current, EOC, EOD, statelist
        

    
    

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

# ~ def csv_write(filename):
    # ~ global lista
    # ~ with open(filename, "w+", newline="") as file:
        # ~ write = csv.writer(file)
        # ~ write.writerows(lista)

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
    global deltat
    t = threading.Timer(deltat, ISR) #ISR se ejecuta cada 1 s mediante threading
    t.start()
    timer_flag = 1 #Al iniciar el hilo, el timer_flag pasa a ser 1



t = threading.Timer(deltat, ISR)
t.start()
plt.ion()
fig = plt.figure(figsize=(6.4, 9.6))

def state_machine(statelist):
    global States
    global start
    global state
    global firstCycle
    global cycles, index
    global cmeas, vmeas, capmeas
    global charging_voltage, charging_current, discharging_current, iter_max, EOD, EOC, wait_time
    match state:
        case States.Idle:
            Source.turn_off_channel(1)
            Load.turn_off_load()
            vmeas,cmeas = Load.measure_all()
            index = 0
            if start == True:
                state = statelist[index]                                    
        case States.Wait:
            # ~ print("Entro a wait")
            Source.turn_off_channel(1)
            Load.turn_off_load()
            vmeas,cmeas = Load.measure_all()
            time.sleep(wait_time)
            index += 1
            state = statelist[index]
        case States.Charge:
            Source.apply_voltage_current(1,charging_voltage, charging_current)
            Source.turn_on_channel(1)
            if firstCycle == True:
                time.sleep(10)
                firstCycle = False
            vmeas,cmeas, _ = Source.measure_all(1)
            # ~ capmeas = np.trapz(current, dx=deltat)
            # ~ capmeas = (capmeas/3600)*1000  
            print(f"Capacity of the battery:{capmeas}")         
            if cmeas < EOC:
                state = States.Wait
        case States.Discharge:
            Load.set_current(discharging_current)
            Load.turn_on_load()
            vmeas,cmeas = Load.measure_all()
            if vmeas < EOD:
                state = States.Wait
        
                    
def relay_sense_and_power(state):   
	global States
	match state:
		case States.Charge:
			GPIO.output(17, GPIO.LOW)
			GPIO.output(27, GPIO.LOW)
		case (States.Idle | States.Discharge | States.DC_Res):
			GPIO.output(17, GPIO.HIGH)       
			GPIO.output(27, GPIO.HIGH)
    

def fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref,draw_volt, draw_curr, draw_cap):
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
    capacity.append(draw_cap)
    lista.append([times.text, t1.text, t2.text, t3.text, t4.text, tavg.text, tref.text, draw_volt, draw_curr,draw_cap, state])
    #csv_write(filename)

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



######################## Classes ########################

class KeyboardThread(threading.Thread):

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def run(self):
        while True:
            self.input_cbk(input()) #waits to get input + Return
            
class States:
    Idle = 0
    Wait = 1
    Charge = 2
    Discharge = 3
    DC_Res = 4

class misc:
    def __init__(self, num, text, data):
        self.num = num
        self.text = text
        self.data = data



######################## Variables ########################


cycles = 0
index = 0 
t1 = misc(0,"",[])
t2 = misc(0,"",[])
t3 = misc(0,"",[])
t4 = misc(0,"",[])
tavg = misc(0,"",[])
tref = misc(0,"",[])
times = misc(0,"",[])
voltage = []
current = []
capacity= []
seconds = 0
cmeas = 0
vmeas = 0
capmeas = 0
firstCycle = True

kthread = KeyboardThread(my_callback)



# ~ statelist = [States.Charge, States.Discharge]
state = States.Idle
past_time = datetime.now()

fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref, vmeas, cmeas, capmeas)

######################## Programa Principal ########################
timer_flag = 0
while True:
    if timer_flag == 1:
        timer_flag = 0
        fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref, vmeas, cmeas,capmeas)
        protection()
        relay_control()
        relay_sense_and_power(state)
        build_seconds(datetime.now())
        control_temperature()
        state_machine(statelist)
        drawnow(temp_figure)
        # ~ print(timer_flag)

GPIO.cleanup() 



