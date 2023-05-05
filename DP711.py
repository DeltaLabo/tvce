import pyvisa
import numpy
import time


# functions for power supply
class Fuente:  
    def __init__(self, instrument, name=None, tipoFuente=False):
        self.instrument = instrument
        self.name = name  # Nombre para identificar en depuracion
        self.delay_enable = tipoFuente
        self.modo = "2W"
        id = ""
        if self.delay_enable:
            instrument.write_termination = '\n'
            instrument.read_termination = '\n'
            self.delay_enable = True
            
        instrument.write("*IDN?")
        time.sleep(0.05)
        id = instrument.read()
        print("ID: {}".format(id))



    # turn on channel
    def encender_canal(self, channel: int):
        self.instrument.write("OUTP:STAT CH{:n},ON".format(channel))
        time.sleep(0.05)
        return "ON"

    # turn off channel
    def apagar_canal(self, channel: int):
        self.instrument.write("OUTP:STAT CH{:n},OFF".format(channel))
        time.sleep(0.05)
        return "OFF"


    # apply voltage & current
    def aplicar_voltaje_corriente(self, voltaje: float, corriente: float):
        self.instrument.write("SOUR:VOLT {}".format(voltaje))
        time.sleep(0.05)
        self.instrument.write("SOUR:CURR {}".format(corriente))
        time.sleep(0.05)
        self.instrument.write("SOUR:VOLT?")
        time.sleep(0.05)
        voltMeas = self.instrument.read()
        time.sleep(0.05)
        self.instrument.write("SOUR:CURR?")
        time.sleep(0.05)
        currMeas = self.instrument.read()
        time.sleep(0.05)
        return "CH1:30V/5A," + voltMeas + "," + currMeas

    # measure everything (in order returns: voltage, current and power)
    def medir_todo(self, channel: int):
        if self.delay_enable:
            self.instrument.write("MEAS:VOLT? CH1")
            time.sleep(0.05)
            voltaje = float(self.instrument.read())
            time.sleep(0.05)
            self.instrument.write("MEAS:CURR? CH1")
            time.sleep(0.05)
            corriente = float(self.instrument.read())
            time.sleep(0.05)
            #self.instrument.write("MEAS:POWE? CH1")
            #time.sleep(0.05)
            #potencia = float(self.instrument.read())
            #time.sleep(0.05)
            return voltaje, corriente#, potencia
        else:
            medicion = self.instrument.query(":MEASURE:ALL?").split(",")
            medicion[-1] = medicion[-1][:-1]
            voltaje = medicion[0]
            corriente = medicion[1]
            #potencia = medicion[2]
            return float(voltaje), float(corriente)#, float(potencia)

    def toggle_4w(self):
        if self.delay_enable:
            if self.modo == "2W":
                self.modo = "4W"
                self.instrument.write("MODE:SET {}".format(self.modo))
                time.sleep(0.5)
                return "4W"
            elif self.modo == "4W":
                self.modo = "2W"
                self.instrument.write("MODE:SET {}".format(self.modo))
                time.sleep(0.5)
                return "2W"