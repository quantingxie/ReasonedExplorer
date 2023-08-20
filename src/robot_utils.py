import cv2
import numpy as np
def capture_image_at_angle(camera, angle):
    # Assuming you have a way to rotate the camera to a specific angle.
    # Rotate camera to the desired angle (this is a placeholder and would depend on your actual setup)
    # rotate_camera_to(angle)  

    # Capture a single frame
    ret, frame = camera.read()
    frame = cv2.flip(frame, 0)
    frame = cv2.flip(frame, 1)

    cv2.imshow('Current View', frame)

    if not ret:
        print(f"Error: Couldn't capture image at angle {angle}.")
        return None

    return frame

def get_GPS():
    """Function that simulates fetching GPS data."""
    latitude = np.random.uniform(-78, 79)
    longitude = np.random.uniform(-135, 136)
    return latitude, longitude
