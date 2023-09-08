import serial
import time

def adjust_heading(heading):
    if 0 <= heading <= 180:
        return -heading
    elif 180 < heading <= 360:
        return -(heading - 360)


def read_from_serial(port='/dev/ttyTHS0', baudrate=115200, timeout=0.1):
    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        while True:
            line = ser.readline()  # read a line terminated with a newline (\n)
            try:
                decoded_line = line.decode('utf-8').strip()
                # print(decoded_line)
                if decoded_line.startswith('$HCHDG'):
                    # Split the line by commas
                    parts = decoded_line.split(',')
                    # Heading (relative to true north) is the third value in the list
                    heading = float(parts[1])
                    # print("unadjusted heading", heading, float(parts[3]))
                    # heading = adjust_heading(heading)
                    # heading = h
                    # 3..eading
                    print(decoded_line)
                    # print("current time: "+time.strftime("%H:%M:%S", time.localtime()))
                    print(heading)
            except UnicodeDecodeError:
                # Silently ignore decoding errors
                pass
            except Exception as e:
                print(f"Unexpected error: {e}")

import robot_interface as sdk
if __name__ == "__main__":
    # HIGHLEVEL = 0xee
    # LOWLEVEL  = 0xff

    # udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
    # print("UDP Initialized")
    # cmd = sdk.HighCmd()
    # state = sdk.HighState()
    # udp.InitCmdData(cmd)


    try:
        read_from_serial()
    
    except KeyboardInterrupt:
        print("\nStopped reading from serial port.")


