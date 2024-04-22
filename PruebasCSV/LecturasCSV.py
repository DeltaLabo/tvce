import csv

def get_voltage_and_current(file_path):
    with open(file_path, newline='') as f:
        data = csv.reader(f, delimiter=',')
        next(data)  # Salta la cabecera del archivo CSV
        # Lee la segunda fila para el voltaje
        voltage_row = next(data)
        # Lee la tercera fila para la corriente
        current_row = next(data)
        # Convierte los valores a flotantes y los retorna
        voltage = float(voltage_row[0])
        current = float(current_row[0])
        return voltage, current

# Llamamos a la función con el path del archivo y guardamos los valores
Voltage, Current = get_voltage_and_current('Prueba_1.csv')

print("Voltage:", Voltage)
print("Current:", Current)
