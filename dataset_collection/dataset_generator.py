import cv2
import numpy as np
import os




"""Code to check camreas"""

# cap = cv2.VideoCapture(8)

# if not cap.isOpened():
#     print("Cannot open camera")
#     exit()

# while True:
#     ret, frame = cap.read()
#     if not ret:
#         print("Can't receive frame. Exiting ...")
#         break
#     cv2.imshow('frame', frame)
#     if cv2.waitKey(1) == ord('q'):
#         break

# cap.release()
# cv2.destroyAllWindows()


def resize_frame(frame, width=None, height=220):
    aspect = frame.shape[1] / float(frame.shape[0])
    
    if not width:
        width = int(height * aspect)
    
    return cv2.resize(frame, (width, height))

# Open handles to the webcams
cap1 = cv2.VideoCapture(1)
cap2 = cv2.VideoCapture(8)
cap3 = cv2.VideoCapture(4)
cap4 = cv2.VideoCapture(2)

angles = [[0, 90, 180, 270], [45, 135, 225, 315]]

while True:
    point_name = input("Enter the GPS(Lat, Lon) of the point (or type 'exit' to quit): ")
    
    if point_name.lower() == "exit":
        break

    # Create a directory for the current point
    point_directory = os.path.join("dataset", point_name)
    if not os.path.exists(point_directory):
        os.makedirs(point_directory)

    capture_index = 0
    print(f"Capturing images for {point_name}. Press 'p' to capture and 'q' to move to the next point.")

    while True:
        ret1, frame1 = cap1.read()
        ret2, frame2 = cap2.read()
        ret3, frame3 = cap3.read()
        ret4, frame4 = cap4.read()

        if ret1 and ret2 and ret3 and ret4:
            frame1 = cv2.flip(frame1, 0)
            frame2 = cv2.flip(frame2, 0)
            frame3 = cv2.flip(frame3, 0)
            frame4 = cv2.flip(frame4, 0)

            frame1 = cv2.flip(frame1, 1)
            frame2 = cv2.flip(frame2, 1)
            frame3 = cv2.flip(frame3, 1)
            frame4 = cv2.flip(frame4, 1)

            frame1 = resize_frame(frame1)
            frame2 = resize_frame(frame2)
            frame3 = resize_frame(frame3)
            frame4 = resize_frame(frame4)

            combined_frames = np.hstack((frame1, frame2, frame3, frame4))

            cv2.imshow('All Cameras', combined_frames)

            key = cv2.waitKey(1) & 0xFF
        
            if key == ord('p'):
                if capture_index < len(angles):
                    current_angles = angles[capture_index]
                    cv2.imwrite(os.path.join(point_directory, f"{current_angles[0]}_degrees.jpg"), frame1)
                    cv2.imwrite(os.path.join(point_directory, f"{current_angles[1]}_degrees.jpg"), frame2)
                    cv2.imwrite(os.path.join(point_directory, f"{current_angles[2]}_degrees.jpg"), frame3)
                    cv2.imwrite(os.path.join(point_directory, f"{current_angles[3]}_degrees.jpg"), frame4)
                    print(f"Captured set {capture_index + 1}")
                    capture_index += 1
                else:
                    print("All sets captured for this point.")
                    break
            elif key == ord('q'):
                break
        else:
            print("Unable to capture frame")
            break

cap1.release()
cap2.release()
cap3.release()
cap4.release()
cv2.destroyAllWindows()
