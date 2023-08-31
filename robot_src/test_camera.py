import cv2

def test_camera_indices(max_index=10):
    for i in range(max_index):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            print(f"Found camera at index {i}")
            cap.release()
        else:
            print(f"No camera found at index {i}")

test_camera_indices()