import serial

port = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver-if00'
# port = '/dev/ttyS0'

baud_rate = 9600
timeout = 1

ser = None
try:
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    while True:
        line = ser.readline()
        try:
            line = line.decode('ISO-8859-1').strip()
            if line.startswith('$GNGLL'):
                print(line)
        except UnicodeDecodeError:
            print('Could not decode line, moving to next line.')
except KeyboardInterrupt:
    print("\nProgram terminated!")
finally:
    if ser is not None:
        ser.close()
        print("Serial port closed.")
import serial

port = '/dev/serial/by-id/usb-u-blox_AG_-_www.u-blox.com_u-blox_GNSS_receiver-if00'
# port = '/dev/ttyS0'

baud_rate = 9600
timeout = 1

ser = None
try:
    ser = serial.Serial(port, baud_rate, timeout=timeout)
    while True:
        line = ser.readline()
        try:
            line = line.decode('ISO-8859-1').strip()
            if line.startswith('$GNGLL'):
                print(line)
        except UnicodeDecodeError:
            print('Could not decode line, moving to next line.')
except KeyboardInterrupt:
    print("\nProgram terminated!")
finally:
    if ser is not None:
        ser.close()
        print("Serial port closed.")
