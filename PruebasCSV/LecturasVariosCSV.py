import csv

def get_voltage_and_current(file_path):
    with open(file_path, newline='') as f:
        data = csv.reader(f, delimiter=',')
        next(data)  # Saltar el titulo de la prueba
        voltage_row = next(data)
        current_row = next(data)
        cycles_row = next(data)
        

        # Convierte los valores eh flotantes
        voltage = float(voltage_row[0])
        current = float(current_row[0])
        cycles = int(cycles_row[0])
        return voltage, current, cycles

def main():
    
    test_choice = input("Choose the number of the test: ").strip()
    file_name = f"Prueba_{test_choice}.csv"

    try:
        Voltage, Current, cycles = get_voltage_and_current(file_name)
        print(f"Voltage: {Voltage} V, Current: {Current} A, Number of cycles: {cycles}")
        print('')
    except FileNotFoundError:
        print(f"Test number {test_choice} was not found.")
    except Exception as e:
        print(f"There was a mistake in the test {test_choice}: {e}")


main()
