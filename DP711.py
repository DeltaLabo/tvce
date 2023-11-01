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
        instrument.write("*IDN?")
        time.sleep(0.05)
        id = instrument.read()
        print("ID: {}".format(id))



    # turn on channel
    def encender_canal(self, channel: int):
        self.instrument.write(":OUTP:STAT CH{:n},ON".format(channel))
        time.sleep(0.1)
        return "ON"

    # turn off channel
    def apagar_canal(self, channel: int):
        self.instrument.write(":OUTP:STAT CH{:n},OFF".format(channel))
        time.sleep(0.05)
        return "OFF"


    # apply voltage & current
    def aplicar_voltaje_corriente(self, voltaje: float, corriente: float):
        self.instrument.write(":VOLT {}".format(voltaje))
        time.sleep(0.2)
        self.instrument.write(":CURR {}".format(corriente))
        time.sleep(0.2)
        return True

    # measure everything (in order returns: voltage, current and power)
    def medir_todo(self, channel: int):
        if self.delay_enable:
            self.instrument.write(":MEAS:VOLT? CH1")
            time.sleep(0.05)
            voltaje = float(self.instrument.read())
            time.sleep(0.05)
            self.instrument.write(":MEAS:CURR? CH1")
            time.sleep(0.05)
            corriente = float(self.instrument.read())
            time.sleep(0.05)
            return voltaje, corriente#, potencia
        else:
            medicion = self.instrument.query(":MEASURE:ALL?").split(",")
            medicion[-1] = medicion[-1][:-1]
            voltaje = medicion[0]
            corriente = medicion[1]
            #potencia = medicion[2]
            return float(voltaje), float(corriente)#, float(potencia)
