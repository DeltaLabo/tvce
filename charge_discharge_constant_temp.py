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

deltat = 2.0
statelist=[]
start = False   
temp = 0
cycles = 1
control = False
cont_temp = 0.0
file_date = datetime.now().strftime("%d_%m_%Y_%H_%M")
lista = [] #csv
EOI = True

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
    global index, cycles
    global pulse_cycle, pulse_wait

    
    match inp:
        case "charge":
            state = States.Charge
            print("Charging the battery")
        case "wait":
            state = States.Wait
            print("The State is in Wait")
        case "next state":
            state = States.Wait
            print("The next state is:",statelist[index+1])            
        case "dc_res":
            cycles, wait_time, charging_voltage, charging_current, discharging_current, EOC, EOD, statelist = LecturasVariosCSV.get_values("test_config.csv")
            state = States.DC_Res
            print("Aplying DC Resistance")
        case "discharge":
            state = States.Discharge
            print("Discharging the battery")
        case "dispulse":
            state = States.Dis_Pulses
            print("Discharging pulses")
        case "off":
            apagar_fuentes()
            control = False
            print("Turning off peltier drivers")
        case "stop":
            index = 0
            start = False 
            state = States.Idle
            print("Stopping the state machine")
        case "start":
            cycles, wait_time, charging_voltage, charging_current, discharging_current, EOC, EOD, statelist = LecturasVariosCSV.get_values("test_config.csv")
            if charging_voltage != 0 and charging_current != 0:
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

datapoints = 1000

def temp_figure():
    #Temperature graph
    ax1 = plt.subplot(211)
    ax1.set_ylim(-15,70)
    plt.plot(times.data[-datapoints:],tavg.data[-datapoints:])
    ax1.set_title("Average Temperature")
    ax1.set_ylabel("Temperature (dC)")
    
    
    #Battery graph
    ax2 = plt.subplot(212, sharex=ax1)
    ax2.set_ylim(0,7)
    plt.plot(times.data[-datapoints:], capacity[-datapoints:], label = "Capacity")
    plt.plot(times.data[-datapoints:], voltage[-datapoints:], label = "Voltage")
    plt.plot(times.data[-datapoints:], current[-datapoints:], label = "Current")
    plt.setp(ax2.get_xticklabels(),visible=False)
    ax2.set_title("Battery Characteristics")
    ax2.set_ylabel("Current (A) | Voltage (V) | Capacity (Ah)")
    ax2.legend()

    
    fig.text(0.5, 0.001, "State: {}".format(state), ha='center')
    plt.tight_layout()

#Interrupt Service Routine
#Executed in response to an event such as a time trigger or a voltage change on a pin

def ISR():
    global timer_flag
    global deltat
    t = threading.Timer(deltat, ISR) #ISR execute every 1 s by threading
    t.start()
    timer_flag = 1 



t = threading.Timer(deltat, ISR)
t.start()
plt.ion()
fig = plt.figure(figsize=(8, 9.8))

def state_machine(statelist):
    global States
    global start
    global state
    global firstCycle
    global cycles, index, DC_Res_cont
    global tdc1, tdc2, tdc3, dc_state, dc_wait, deltat
    global cmeas, vmeas, capmeas, capacity, current
    global v1,v2,v3,v4,c1,c2,c3,c4
    global charging_voltage, charging_current, discharging_current, EOD, EOC, wait_time
    global pulse_cycle, pulse_wait, EOI
    global initialtime
    
    match state:
        
        case States.Idle:
            Source.turn_off_channel(1)
            Load.turn_off_load()
            vmeas,cmeas = Load.measure_all()
            index = 0
            EOI = True
            #print("ciclos", cycles)
            if start == True and cycles != 0 and EOI == True:
                #print("Cicló")
                cycles -= 1
                state = statelist[index]
                #print("Estado de ciclo", state)
                EOI = False
                
            
            if start == True and EOI == True:
                pulse_wait = PULSE_TIME
                EoP = False
                if statelist[index] == States.Dis_Pulses and not EoP:
                    if vmeas > EOD:
                        state = States.Dis_Pulses
                    else:
                        EoP = True
                else:
                    index += 1
                    state = statelist[index]
                
        case States.Wait:
            Source.turn_off_channel(1)
            Load.turn_off_load()
            vmeas,cmeas = Load.measure_all()
            if firstCycle == False:
                initialtime = seconds
                firstCycle = True
            if (seconds - initialtime) > wait_time:
                dc_state = DC_states.Discharge_1
                index += 1
                state = statelist[index]
            
        case States.Charge:
            vmeas,cmeas, _ = Source.measure_all(1)
            if cmeas < EOC and firstCycle == False:
                state = States.Wait
            if firstCycle == True:
                Source.apply_voltage_current(1,charging_voltage, charging_current)
                Source.turn_on_channel(1)
                firstCycle = False

                
        case States.Discharge:
            vmeas,cmeas = Load.measure_all()
            if vmeas < EOD and firstCycle == False:
                state = States.Wait
            if firstCycle == True:
                Load.set_current(discharging_current)
                Load.turn_on_load()
                firstCycle = False

        
        case States.Dis_Pulses:
            vmeas,cmeas = Load.measure_all()
            if vmeas < 2:
                print("Terminaron los pulsos")
                start = False
                state = States.Idle
            if pulse_wait == PULSE_TIME:
                Load.set_current(nominal_capacity*1.5)
                Load.turn_on_load()
            elif pulse_wait == 0:
                Load.turn_off_load()
            elif pulse_wait == -1:
                v1 = vmeas
                print("v1 = ", v1,'\n')
            elif pulse_wait == -2:
                pulse_wait = 0
                if ((vmeas-v1)/vmeas) < (0.005/100):
                    state = States.Idle
                    print("vmeas = ", vmeas,'\n')
                    print("v1 = ", v1,'\n')
            pulse_wait -= 1

                    
                    
                
                
        
        case States.DC_Res:
            match dc_state:
                case DC_states.Discharge_1:
                    vmeas,cmeas = Load.measure_all()
                    Load.set_current(nominal_capacity) # 1 * Capacity of the battery
                    Load.turn_on_load()
                    dc_wait -= 1
                    if dc_wait == 0:
                        dc_state = DC_states.Discharge_2
                        dc_wait = 108 / deltat
                case DC_states.Discharge_2:
                    vmeas,cmeas = Load.measure_all()                    
                    Load.set_current(nominal_capacity*0.75) # 0.75 * Capacity of the battery
                    Load.turn_on_load()
                    dc_wait -= 1
                    if dc_wait == 0:
                        v1,c1 = vmeas,cmeas
                        dc_state = DC_states.Wait_1
                        dc_wait = 40/deltat
                case DC_states.Charge:
                    vmeas,cmeas, _ = Source.measure_all(1)
                    Source.apply_voltage_current(1,charging_voltage, nominal_capacity*0.75)
                    Source.turn_on_channel(1)
                    if firstCycle == True:
                        time.sleep(10)
                        firstCycle = False
                    dc_wait -= 1
                    if dc_wait == 0:
                        v3,c3 = vmeas,cmeas
                        dc_state = DC_states.Wait_2
                        dc_wait = 40/deltat
                case DC_states.Wait_1:
                    vmeas,cmeas = Load.measure_all()
                    Source.turn_off_channel(1)
                    Load.turn_off_load()
                    dc_wait -= 1
                    if dc_wait == 0:
                        v2,c2 = vmeas,cmeas
                        dc_state = DC_states.Charge
                        dc_wait = 20/deltat                        
                case DC_states.Wait_2:
                    vmeas,cmeas = Load.measure_all()
                    Source.turn_off_channel(1)
                    Load.turn_off_load()
                    dc_wait -= 1
                    if dc_wait == 0:
                        v4,c4 = vmeas,cmeas
                        dc_state = DC_states.Charge
                        DCIR_discharge = ((v2-v1)/c1)*1000 #miliohms
                        DCIR_charge = ((v3-v4)/c3)*1000
                        print("")
                        print(f"The DCIR for charge is: {DCIR_charge} miliohms")
                        print("")
                        print(f"The DCIR for discharge is: {DCIR_discharge} miliohms")
                        state = States.Wait 
                    
                
def relay_sense_and_power(state, dc_state):
    global DC_states
    global States
    match state:
        case States.Charge:
            GPIO.output(17, GPIO.LOW)
            GPIO.output(27, GPIO.LOW)
        case (States.Idle | States.Discharge | States.Wait | States.Dis_Pulses):
            GPIO.output(17, GPIO.HIGH)
            GPIO.output(27, GPIO.HIGH)
        case States.DC_Res:
            match dc_state:
                case DC_states.Charge:
                    GPIO.output(17, GPIO.LOW)
                    GPIO.output(27, GPIO.LOW)
                case (DC_states.Discharge_1 | DC_states.Discharge_1 | DC_states.Wait_1 | DC_states.Wait_2):
                    GPIO.output(17, GPIO.HIGH)
                    GPIO.output(27, GPIO.HIGH)
        
                
            
            
    

def fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref,draw_volt, draw_curr, state):
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
    
    capmeas = np.trapz(current, dx=deltat)
    capmeas = (capmeas/3600)
    if state == States.Wait:
        current.append(0)
        capacity.append(0)
    else:
        current.append(draw_curr)
        capacity.append(capmeas)
    voltage.append(draw_volt)
            
    
    lista.append([times.text, t1.text, t2.text, t3.text, t4.text, tavg.text, tref.text, draw_volt, draw_curr,capmeas, state])
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



######################## Classes ########################

class KeyboardThread(threading.Thread):

    def __init__(self, input_cbk = None, name='keyboard-input-thread'):
        self.input_cbk = input_cbk
        super(KeyboardThread, self).__init__(name=name)
        self.start()

    def run(self):
        while True:
            self.input_cbk(input()) #waits to get input + Return
     
class DC_states:
    Discharge_1 = 0
    Discharge_2 = 1
    Charge = 2
    Wait_1 = 3     #Measure V2 and I2
    Wait_2 = 4     #Measure V4 and I4
            
class States:
    Idle = 0
    Wait = 1
    Charge = 2
    Discharge = 3
    DC_Res = 4
    Dis_Pulses = 5

class misc:
    def __init__(self, num, text, data):
        self.num = num
        self.text = text
        self.data = data



######################## Variables ########################



index = 0 
iter_max = 0

#According to ISO 12405
dc_state = DC_states.Discharge_1
dc_wait = 18 / deltat
PULSE_TIME = 60
pulse_wait = PULSE_TIME
pulse_cycle = 10
v1 = 0
v2 = 0
v3 = 0
v4 = 0
c1 = 0
c2 = 0
c3 = 0
c4 = 0
# ~ tdc1 = 9 #18 seconds, but the sistem takes data every 2 seconds
# ~ tdc2 = 51 #102 seconds
# ~ tdc3 = 10 #20 seconds
# ~ dc_wait_time = 10

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
nominal_capacity = 3.5 #Ah
seconds = 0
cmeas = 0
vmeas = 0
capmeas = 0
firstCycle = True

kthread = KeyboardThread(my_callback)



# ~ statelist = [States.Charge, States.Discharge]
state = States.Idle
past_time = datetime.now()

fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref, vmeas, cmeas, state)

######################## Programa Principal ########################
timer_flag = 0
while True:
    if timer_flag == 1:
        timer_flag = 0
        
        fill_measure_data(times,seconds,t1,t2,t3,t4,tavg,tref, vmeas, cmeas, state)
        protection()
        relay_control()
        relay_sense_and_power(state, dc_state)
        build_seconds(datetime.now())
        control_temperature()
        state_machine(statelist)
        drawnow(temp_figure)
        # ~ print(timer_flag)

GPIO.cleanup() 



