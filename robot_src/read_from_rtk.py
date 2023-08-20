import os
import socket
import serial

port = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver-if00'
baud_rate = 9600
timeout = 1
host = '127.0.0.1'  # Local host
socket_port = 12345  # Ensure the port is available

ser = None
serversocket = None

try:
    if os.path.exists(port):
        ser = serial.Serial(port, baud_rate, timeout=timeout)

        # Create a socket object
        serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        serversocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        serversocket.bind((host, socket_port))
        serversocket.listen(5)  # Queue up to 5 requests

        print("Server listening...")

        # Establish a connection
        clientsocket, addr = serversocket.accept()

        print(f"Got a connection from {str(addr)}")
        
        with open('send_gps_data_log.txt', 'w') as f:
    
            while True:
                line = ser.readline()
                try:
                    line = line.decode('ISO-8859-1').strip()
                    if line.startswith('$GNGLL'):
                        split_line = line.split(',')
                        lat = str(float(split_line[1])/100)
                        lon = str(float(split_line[3])/100)
                        f.write(lat + ',' + lon + '\n')
                        print(f"({lat}, {lon})".encode('utf-8'))
                        clientsocket.send(f"({lat}, {lon})".encode('utf-8'))
                except UnicodeDecodeError:
                    print('Could not decode line, moving to next line.')
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
