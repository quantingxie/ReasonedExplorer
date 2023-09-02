import serial


def adjust_heading(heading):
    if 0 <= heading <= 180:
        return -heading
    elif 180 < heading <= 360:
        return -(heading - 360)


def read_from_serial(port='/dev/ttyUSB0', baudrate=9600, timeout=1):
    with serial.Serial(port, baudrate, timeout=timeout) as ser:
        while True:
            line = ser.readline()  # read a line terminated with a newline (\n)
            try:
                decoded_line = line.decode('utf-8').strip()
                if decoded_line.startswith('$PRDID'):
                    # Split the line by commas
                    parts = decoded_line.split(',')
                    # Heading (relative to true north) is the third value in the list
                    heading = float(parts[3])
                    heading = adjust_heading(heading)
                    print(heading)
            except UnicodeDecodeError:
                # Silently ignore decoding errors
                pass
            except Exception as e:
                print(f"Unexpected error: {e}")

if __name__ == "__main__":
    try:
        read_from_serial()
    except KeyboardInterrupt:
        print("\nStopped reading from serial port.")


