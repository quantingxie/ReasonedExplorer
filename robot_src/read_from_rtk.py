import os
import socket
import serial
import math

port = '/dev/ttyUSB1'
baud_rate = 38400
timeout = 1
host = '127.0.0.1'
socket_port = 12345

ser = None
serversocket = None

def dms_to_dd(dms):
    if dms < 0:
        dms = abs(dms)
        degrees = math.floor(abs(dms))
        fractional = abs(dms) - abs(degrees)
        minutes = fractional * 100 / 60
        return -(degrees + minutes)
    else:
        degrees = math.floor(dms)
        fractional = dms - degrees
        minutes = fractional * 100 / 60
        return degrees + minutes

try:
    if os.path.exists(port):
        ser = serial.Serial(port, baud_rate, timeout=timeout)

        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((host, socket_port))
        serversocket.listen(5)
        print("Server listening...")

        clientsocket, addr = serversocket.accept()
        print(f"Got a connection from {str(addr)}")

        with open('send_gps_data_log.txt', 'w') as f:
            while True:
                line = ser.readline().decode('ascii', errors='replace').strip()
                if line.startswith('$GNGLL'):
                    split_line = line.split(',')
                    lat = dms_to_dd(float(split_line[1])/100)
                    lon = dms_to_dd(float(split_line[3])/100)
                    f.write(f"{lat},{lon}\n")
                    print(f"({lat}, {lon})".encode('utf-8'))
                    clientsocket.send(f"({lat}, {lon})".encode('utf-8'))
    else:
        print(f"Serial port {port} does not exist.")

except KeyboardInterrupt:
    print("\nProgram terminated!")

finally:
    if ser is not None:
        ser.close()
        print("Serial port closed.")
    if serversocket is not None:
        serversocket.close()
        print("Socket closed.")
