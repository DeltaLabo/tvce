
# TVCE - Battery Characterizer
![TVCE System](/Assets/IMG_9187.jpeg)
![Cube of TVCE](/Assets/IMG_9188.jpeg)

TVCE is a battery characterization system designed for INR18650 type batteries, capable of performing both charging and discharging cycles. This system is composed of two main subsystems:

- **Temperature Control Subsystem**: Utilizes two Rigol DP711 DC power supplies to regulate temperature.
- **Charge and Discharge Subsystem**: Employs a Rigol DL3021 electronic load and a Rigol DP811A DC power supply.

All devices are controlled by a **Raspberry Pi 4**. Communication with the Rigol instruments is done via serial interface using the PySerial library.

## Temperature Control Details

Temperature is managed using an array of four thermocouples, connected through a custom driver that processes the four data sets internally by averaging the temperature readings. Temperature regulation is achieved through Peltier cells that heat or cool heat sinks. Power delivery to the Peltier cells is controlled by an array of relays, allowing precise management of the temperature control system.

![Reles & termocuples](/Assets/IMG_9189.jpeg)

![Reles & termocuples](/Assets/Diagrama_reles_TVCE.drawio.png)

---

This program uses the library `instrument_driver` in order to communicate with the instrumentation. This library is present in this repository as a git submodule, as such, when you clone the repository for this program, you must do an extra step:

> `git clone https://github.com/DeltaLabo/tvce.git`

> `git submodule add https://github.com/username/library-repo.git`

This will clone the latest version of the library into the cloned folder.

If there is a change pushed to the library repository and you wish to update the version in the cloned folder of this program, you must do the following:

> `git submodule update --remote`

Any questions contact Kaleb Granados. kalebgranac13@gmail.com


