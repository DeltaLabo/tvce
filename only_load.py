import pyvisa
import controller
import DP711
import time
import RPi.GPIO as GPIO
import board
import digitalio
import adafruit_max31855
from datetime import datetime
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

# ~ for inst in range(len(res)): 
	# ~ insti = rm.open_resource(rm.list_resources()[inst])
	# ~ try:
		# ~ insti.write("*IDN?")
		# ~ time.sleep(0.2)
		# ~ aux = insti.read()
	# ~ except:
		# ~ print("Not VISA")
	# ~ print(aux)
	# ~ match aux:
		# ~ case equipment.heater1:
			# ~ try:
				# ~ heater1 = rm.open_resource(rm.list_resources()[inst])
				# ~ print("Heater1 asigned", end="\n\n")
			# ~ except:
				# ~ print("Error assigning Heater1", end="\n\n")
		# ~ case equipment.heater2:
			# ~ try: 
				# ~ heater2 = rm.open_resource(rm.list_resources()[inst])            
				# ~ print("Heater2 asigned", end="\n\n")
			# ~ except:
				# ~ print("Error assigning Heater2", end="\n\n")
		# ~ case equipment.source:
			# ~ try:
				# ~ source = rm.open_resource(rm.list_resources()[inst])
				# ~ print("Source asigned", end="\n\n")
			# ~ except:
				# ~ print("Error assigning Source", end="\n\n")
		# ~ case equipment.load:
            # ~ try:
                # ~ load = rm.open_resource(rm.list_resources()[inst])
                # ~ print("Load asigned", end="\n\n")
            # ~ except:
                # ~ print("Error assigning Load", end="\n\n")    

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


# ~ Load.cargar_celda(1.5)


