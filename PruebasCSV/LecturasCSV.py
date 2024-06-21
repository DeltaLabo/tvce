import csv

# ~ statelist=[]

def get_voltage_and_current(file_path):
    with open(file_path, newline='') as f:
        # ~ data = csv.reader(f, delimiter=',')
        data = list(csv.reader(f, delimiter=','))
        
        voltage_row = float(data[2][0])
        current_row = [float(x) for x in data[4]]
        state_row = [int(x) for x in data[8]]
        
        # ~ for element in 
                
        voltage = voltage_row
        current = current_row
        statelist = state_row        
        
        return voltage, current, statelist

# Llamamos a la función con el path del archivo y guardamos los valores
Voltage, Current, State_List = get_voltage_and_current('Prueba_1.csv')

print('')
print("Voltage:", Voltage)
print("Current:", Current)
print("State List", State_List)


