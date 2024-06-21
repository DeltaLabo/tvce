import pandas as pd

def get_values(data_path):
        global statelist
        
        test_choice = int(input("Choose the number of the test: ").strip())
        test_choice -= 1
             
        data = ["test_number", "cycles","wait_time", "cv", "cc", "dc", "eod", "eoc"]
        states = ["e1", "e2", "e3", "e4", "e5", "e6", "e7", "e8", "e9", "e10"]
        
        data_test = pd.read_csv(data_path, usecols = data)
        states_test = pd.read_csv(data_path,usecols = states)
        
        wait_time = data_test.loc[test_choice, "wait_time"]
        wait_time = wait_time*1 #Tiempo en segundos
        iter_max = data_test.loc[test_choice, "cycles"]
        charging_voltage = data_test.loc[test_choice,"cv"]
        charging_current = data_test.loc[test_choice,"cc"]
        discharging_current = data_test.loc[test_choice,"dc"]
        EOD = data_test.loc[test_choice,"eod"]
        EOC = data_test.loc[test_choice,"eoc"]
        statelist = (states_test.iloc[test_choice]).values.tolist()

        
        
        print(" ")
        print("Number of cycles: ", iter_max)
        print("Wait time between cycles: ", wait_time)
        print("Charging Voltage:", charging_voltage)
        print("Charging Current:", charging_current)
        print("Discharging Current:", discharging_current)
        print("End of charge:", EOC)
        print("End of discharge:", EOD)
        print("State list:\n", statelist)
        print(" ")
        return iter_max, wait_time, charging_voltage, charging_current, discharging_current, EOC, EOD, statelist

