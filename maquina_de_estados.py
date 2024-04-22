import pyvisa
import DP711
import time

global state

statelist = [States.Charge,States.Discharge,States.Charge,States.Discharge]
L = len(statelist)

i=0

for i in range(L):
        state=statelist[i]
        print(i, "\n")
        print(state, "\n")
        i=i+1
