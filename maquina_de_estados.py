import pyvisa
import controller
import DP711
import time

class Ciclar:
	
	def __init__(self, instrument, name=None):
        self.carga = instrument
        self.name = name  # Nombre para identificar en depuracion
	
	def cargar_celda(self, state, corriente: float):
		
        self.carga.write("SENS ON")
        self.carga.write(":SOUR:CURR:LEV:IMM {}".format(corriente))
        self.carga.query(":SOUR:CURR:LEV:IMM?")
        self.carga.write(":SOUR:INP:STAT 1")
        self.carga.query(":SOUR:INP:STAT?")
        time.sleep(30)
        self.carga.write(":SOUR:INP:STAT 0")
        return self.carga.query(":SOUR:INP:STAT?")
        

