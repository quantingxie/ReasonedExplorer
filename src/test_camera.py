import pyrealsense2 as rs
import numpy as np
import cv2
import time
import os
def initialize_cameras(serial_numbers, delay=5):
    pipelines = []
    for serial_number in serial_numbers:
        pipeline = rs.pipeline()
        config = rs.config()
        config.enable_device(serial_number)
        config.enable_stream(rs.stream.color, 640, 480, rs.format.bgr8, 6)
        config.enable_stream(rs.stream.depth, 640, 480, rs.format.z16, 6)
        pipeline.start(config)
        pipelines.append(pipeline)
        
    print("Cameras initialized. Waiting for auto-exposure adjustment for 5s...")
    time.sleep(delay)
    return pipelines

def capture_image_from_camera(pipeline):
    frames = pipeline.wait_for_frames()
    color_frame = frames.get_color_frame()
    if not color_frame:
        return None
    color_image = np.asanyarray(color_frame.get_data())
    return color_image

def capture_image_and_average_depth(pipeline, serial_number, image_folder="images"):
    """
    Captures a color image and its average depth from a RealSense camera pipeline,
    saves the image, and returns the image path and average depth.
    """
    try:
        os.makedirs(image_folder, exist_ok=True)  # Ensure the directory exists
        frames = pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()

        if not depth_frame or not color_frame:
            return None, None, None

        # Process depth frame
        depth_image = np.asanyarray(depth_frame.get_data())
        non_zero_depths = depth_image[depth_image != 0]
        average_depth = np.mean(non_zero_depths) if non_zero_depths.size > 0 else 0

        # Process color frame and save image
        color_image = np.asanyarray(color_frame.get_data())
        filename = f"camera_{serial_number}.jpg"
        filepath = os.path.join(image_folder, filename)
        cv2.imwrite(filepath, color_image)

        return color_image, average_depth, filepath
    except Exception as e:
        print(f"Failed to capture images: {e}")
        return None, None, None

    
def main():
    serial_numbers = ['936322070007', '238722073643', '242322077802']
    pipelines = initialize_cameras(serial_numbers)

    for i, pipeline in enumerate(pipelines):
        image, average_depth = capture_image_and_average_depth(pipeline)
        if image is not None:
            filename = f'camera_{serial_numbers[i]}.jpg'
            cv2.imwrite(filename, image)
            print(f"Image saved as {filename}. Average depth: {average_depth}")
    for pipeline in pipelines:
        pipeline.stop()

if __name__ == "__main__":
    main()