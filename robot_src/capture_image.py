import cv2

def capture_image_at_angle(angle):
    camera = cv2.VideoCapture(1)
    if not camera.isOpened():
        print("Error: Could not open camera.")
        return
    
    ret, frame = camera.read()
    frame = cv2.flip(frame, 0)
    frame = cv2.flip(frame, 1)

    cv2.imwrite(f"{angle}_degrees.jpg", frame)

    if not ret:
        print(f"Error: Couldn't capture image at angle {angle}.")
        return None

    return f"{angle}_degrees.jpg"
