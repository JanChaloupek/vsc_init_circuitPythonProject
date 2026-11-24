import serial
import serial.tools.list_ports
import time

PICO_PORT = "COM4"  # Change as needed

def send_stop_command():
    """Function to send STOP command to the Pico."""
    try:
        time.sleep(0.5) # Allow time for the connection to stabilize
        with serial.Serial(PICO_PORT, 115200, timeout=1) as ser:
            ser.write(bytes([3]))  # Send STOP command
            print("STOP command sent!")
    except serial.SerialException as e:
        print(f"Error: {e}")

def check_for_com():
    """Continuously checks for COM4 and sends the STOP command when connected."""
    while True:
        ports = [port.device for port in serial.tools.list_ports.comports()]
        
        if PICO_PORT in ports:
            print(f"{PICO_PORT} detected! Sending STOP command...")
            send_stop_command()
            break  # Exit loop after sending command
        
        print(f"Waiting for {PICO_PORT} to connect...")
        time.sleep(0.1)  # Check every 2 seconds

if __name__ == "__main__":
    check_for_com()
