# Davka v Pythonu. Umi prijimat hodnoty oddelene carkou zaslane z pico:ed-u pres seriovy port a zobrazit je v grafu.
# Verze souboru ze dne 2025-02-21
import serial
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import serial.tools.list_ports
import itertools
from time import sleep

def find_com_device(vid, pid):
    ports = list(serial.tools.list_ports.comports())
    for port in ports:
        if port.vid == vid and port.pid == pid:
            return port.device
    return None

def showInfo():
    com_ports = list(serial.tools.list_ports.comports())
    for port in com_ports:
        print(f"Device: {port.device}")
    
def init_plot():
    # ax.set_xlim(0, 20)
    # ax.set_ylim(0, 1023)
    for line in lines:
        line.set_data([], [])
    return lines

def update_plot(frame):
    data = ser.readline().decode().strip()
    if data:
        try:
            values = list(map(float, data.split(',')))
        except ValueError:
            return lines  # Pokud nelze převést řetězec na číslo, přeskoč řádek
        if len(values) >= 2:
            x_data.append(values[0])
            for i in range(1, len(values)):
                if len(y_data) < i:
                    y_data.append([])  # Přidání nového seznamu pro nový y datový bod
                y_data[i-1].append(values[i])
            ax.set_xlim(min(x_data), max(x_data))
            min_y = min(itertools.chain(*y_data))
            max_y = max(itertools.chain(*y_data))
            ax.set_ylim(min_y, max_y)
            for i, line in enumerate(lines):
                if i < len(y_data):
                    line.set_data(x_data, y_data[i])
            fig.canvas.draw()
            fig.canvas.flush_events()
    sleep(0.01)
    return lines

print("Seznam všech COM portů.")
showInfo()

print("Vyberu a otevřu COM port od připojeného pico:ed-u.")
comPortPicoEd = find_com_device(0x2e8a, 0x1026)

while True:
    try:
        ser = serial.Serial(comPortPicoEd, 9600)
    except:
        print(f"Nemohu otevřít {comPortPicoEd}. Není zapnutý REPL?")
        sleep(1)
    else:
        print(f"Připojen na {ser.name}. Přijímám data.")
        break


x_data = []
y_data = []

fig, ax = plt.subplots()
colors = ['blue', 'green', 'red']
lines = [ax.plot([], [], lw=2, color=color)[0] for color in colors]

ani = animation.FuncAnimation(fig, update_plot, init_func=init_plot, blit=False, cache_frame_data=False)

plt.show()

