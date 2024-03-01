import pandas as pd
from matplotlib import pyplot as plt


data1 = pd.read_csv('34a40.csv', names=["t", "T1", "T2", "T3", "T4", "Tp", "Ta"], header=None)
data2 = pd.read_csv('40a15.csv', names=["t", "T1", "T2", "T3", "T4", "Tp", "Ta"], header=None)
print(data1.head())

plt.plot(data1.t, data1.Tp)
plt.plot(data2.t, data2.Tp)
plt.title('Prueba a temperatura constante')
plt.ylabel('Temperatura (°C)')
plt.xlabel('Tiempo (s)')
plt.xlim(left=0, right=750)
plt.ylim(bottom=0, top=50) 
plt.legend(['Control a 40°C','Control a 15°C'],loc='lower right')
plt.show()