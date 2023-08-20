import sys
import time
import math
import csv
import socket
import threading

sys.path.append('../lib/python/amd64')
import robot_interface as sdk

initial_lat = initial_lon = current_lat = current_lon = None
lock = threading.Lock()  # A lock for synchronizing threads

def socket_client_thread():
    global initial_lat, initial_lon, current_lat, current_lon
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connect to the server
    s.connect(('127.0.0.1', 12345))

    # Buffer for storing partial lines
    data_buffer = ''

    with open('gps_data.csv', 'w') as f:
        writer = csv.writer(f)
        writer.writerow(['timestamp', 'x', 'y', 'z', 'q_x', 'q_y', 'q_z', 'q_w'])

        while True:
            # Receive data from the server
            received_data = s.recv(1024).decode('utf-8')

            # Add received data to buffer
            data_buffer += received_data

            # Check if there's a full line of data
            while '\n' in data_buffer:
                line, data_buffer = data_buffer.split('\n', 1)
                
                try:
                    # Convert received data to tuple and extract lat and lon
                    lat, lon = eval(line)

                    current_lat, current_lon = lat, lon

                    if initial_lat is None and initial_lon is None:
                        initial_lat, initial_lon = lat, lon

                    with lock:
                        state = sdk.HighState()
                        udp.GetRecv(state)
                        q = state.imu.quaternion

                    writer.writerow([time.time(), lat, lon, 0, q[1], q[2], q[3], q[0]])  # 0 for z as it is not available
                except:
                    print("Error while processing GPS data.")

if __name__ == '__main__':

    # Start socket client in a separate thread
    threading.Thread(target=socket_client_thread).start()

    HIGHLEVEL = 0xee
    LOWLEVEL  = 0xff

    try:
        udp = sdk.UDP(HIGHLEVEL, 8080, "192.168.123.161", 8082)
    except:
        print("Error while connecting to the device.")
        sys.exit(1)

    cmd = sdk.HighCmd()
    state = sdk.HighState()
    udp.InitCmdData(cmd)

    # Create a csv file and write the headers
    with open('imu_data.csv', mode='w') as imu_file:
        writer = csv.writer(imu_file)
        writer.writerow(['timestamp', 'q_x', 'q_y', 'q_z', 'q_w', 'ang_vel_x', 'ang_vel_y', 'ang_vel_z', 'lin_acc_x', 'lin_acc_y', 'lin_acc_z'])

    motiontime = 0
    while True:
        time.sleep(0.002)
        motiontime = motiontime + 1

        udp.Recv()

        with lock:
            udp.GetRecv(state)

        if any(state.imu.quaternion) and any(state.imu.gyroscope) and any(state.imu.accelerometer):
            # Log the data into csv
            with open('imu_data.csv', mode='a') as imu_file:
                writer = csv.writer(imu_file)
                writer.writerow([time.time(), state.imu.quaternion[1], state.imu.quaternion[2], state.imu.quaternion[3], state.imu.quaternion[0],
                                 state.imu.gyroscope[0], state.imu.gyroscope[1], state.imu.gyroscope[2],
                                 state.imu.accelerometer[0], state.imu.accelerometer[1], state.imu.accelerometer[2]])
        else:
            print("Received zero values from IMU.")

