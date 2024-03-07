import pyvisa
import controller
import time

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
	elif res[i].find("ttyUSB1") > 0:
		heater1 = rm.open_resource(rm.list_resources()[i]) 
		print("Fuente DP711.1 encontrada")
		print(heater1.query("*IDN?"))
	elif res[i].find("ttyUSB2") > 0:
		heater2 = rm.open_resource(rm.list_resources()[i]) 
		print("Fuente DP711.2 encontrada")
		print(heater2.query("*IDN?"))

     


Load = controller.Carga(load, "DL3021")
print(Load.fijar_funcion("CURR"))
Load.remote_sense(True)
Load.fijar_corriente(1.5) #Descargando a C/35
Load.encender_carga()
time.sleep(20)
Load.apagar_carga()
