import cv2
import numpy as np
def capture_image_at_angle(angle):
    # Assuming you have a way to rotate the camera to a specific angle.
    # Rotate camera to the desired angle (this is a placeholder and would depend on your actual setup)
    # rotate_camera_to(angle)  

    # Capture a single frame

    # Open handle for camera
    camera = cv2.VideoCapture(1)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return
    
    ret, frame = camera.read()
    frame = cv2.flip(frame, 0)
    frame = cv2.flip(frame, 1)

    cv2.imwrite(f"degrees.jpg", frame)

    if not ret:
        print(f"Error: Couldn't capture image at angle {angle}.")
        return None

    return frame

def get_GPS():
    """Function that simulates fetching GPS and yaw data."""
    # Randomly simulating latitude and longitude
    latitude = np.random.uniform(-78, 79)
    longitude = np.random.uniform(-135, 136)

    # Randomly simulating yaw (orientation) from 0 to 359
    yaw = np.random.uniform(0, 360)

    return (latitude, longitude), yaw