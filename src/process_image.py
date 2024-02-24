import cv2
import numpy as np

def stitch_images(image1, image2, image3):
    # Use OpenCV's createStitcher function to stitch images
    stitcher = cv2.Stitcher_create()
    (status, stitched) = stitcher.stitch([image1, image2, image3])

    if status != cv2.Stitcher_OK:
        print("Can't stitch images, error code = %d" % status)
        return None
    
    return stitched

def draw_paths_on_ground(stitched_image, num_paths=3):
    height, width = stitched_image.shape[:2]
    horizon_line = height // 2
    start_point = (width // 2, height)  # Middle bottom of the image
    vanishing_point = (width // 2, horizon_line + 200)  

    # Draw the paths in a default color (light gray for visibility)
    default_color = (200, 200, 200)

    # Set font parameters for numbering the paths
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 1
    font_color = (200, 200, 200)  # Black color for the text
    font_thickness = 2
    angle_increment = np.pi / (num_paths - 1)

    for i in range(num_paths):
        angle = angle_increment * i - (np.pi / 2)
        print(np.degrees(angle))
        # Determine the length of the line from the horizon to the bottom of the image
        line_length = (start_point[1] - vanishing_point[1]) / np.cos(angle)

        # Calculate the end point of the line
        end_x = int(start_point[0] + np.sin(angle) * line_length)
        end_y = int(start_point[1] - np.cos(angle) * line_length)

        # Ensure the end points are valid integers within the image boundaries
        end_x = max(0, min(end_x, width - 1))
        end_y = max(0, min(end_y, height - 1))

        # Draw the line
        cv2.line(stitched_image, start_point, (end_x, end_y), default_color, 2)

        # Number the path
        path_number = str(i+1)
        text_size = cv2.getTextSize(path_number, font, font_scale, font_thickness)[0]
        text_position = (end_x - 20, end_y - 20)  # Centered text position

        # Ensure the text position is within the image boundaries
        text_x = max(0, min(text_position[0], width - text_size[0]))
        text_y = max(0, min(text_position[1], height - 1))

        cv2.putText(stitched_image, path_number, (text_x, text_y), font, font_scale, font_color, font_thickness)

    return stitched_image


def color_code_paths(stitched_image, scores):
    height, width = stitched_image.shape[:2]
    start_point = (width // 2, height)  # Middle bottom of the image
    horizon_line = height // 2
    vanishing_point = (width // 2, horizon_line + 200)  # Assuming vanishing point at horizon center

    # Define the base colors
    weak_color = np.array([200, 200, 200], dtype=np.float32)  # Light gray color for weak paths
    strong_color = np.array([0, 0, 255], dtype=np.float32)  # Red color for strong paths

    # Define the base and max thickness
    base_thickness = 2
    max_thickness = 6

    max_score = max(scores)
    min_score = min(scores)

    for i, score in enumerate(scores):
        # Normalize the score to range [0,1]
        normalized_score = (score - min_score) / (max_score - min_score)
        
        # Interpolate the color and thickness based on the normalized score
        color = (weak_color * (1 - normalized_score) + strong_color * normalized_score).astype(np.uint8).tolist()
        thickness = int(base_thickness + normalized_score * (max_thickness - base_thickness))

        angle = ((i / float(len(scores) - 1)) * np.pi) - (np.pi / 2)  # Angle in radians
        
        # Calculate the end point of the line using perspective projection
        end_x_horizon = int(vanishing_point[0] + np.cos(angle) * (width / 2))
        end_y_horizon = horizon_line

        line_length = (start_point[1] - vanishing_point[1]) / np.cos(angle)
        end_x = int(start_point[0] + np.sin(angle) * line_length)
        end_y = int(start_point[1] - np.cos(angle) * line_length)

        # Ensure that the line endpoints are within the image boundaries
        end_x = max(0, min(end_x, width))
        end_y = max(0, min(end_y, height))

        # If the end point is above the horizon, use the horizon intersection point
        if end_y < horizon_line:
            end_x = end_x_horizon
            end_y = end_y_horizon

        # Draw the line with the interpolated color and thickness
        cv2.line(stitched_image, start_point, (end_x, end_y), color, thickness)

    return stitched_image

def process_images(image1, image2, image3, scores):
    stitched = stitch_images(image1, image2, image3)
    if stitched is None:
        return None, None  # Return None if stitching failed

    stitched_with_ground_paths = draw_paths_on_ground(stitched.copy(), num_paths=len(scores))
    return stitched_with_ground_paths


# Testing
# Replace 'left.png' and 'right.png' with your actual image paths
image1 = cv2.imread('VLM/images/left2.png')
image2 = cv2.imread('VLM/images/mid2.png')
image3 = cv2.imread('VLM/images/right2.png')

# Stitch images
stitched = stitch_images(image1, image2, image3)

if stitched is not None:
    # Draw the initial paths in the same color
    stitched_with_ground_paths = draw_paths_on_ground(stitched.copy())

    # Save the image with uniform paths
    cv2.imwrite('stitched_paths_uniform.png', stitched_with_ground_paths)

    # Hypothetical scores for demonstration
    scores = [1, 2, 5]
    
    # Apply color coding based on the scores
    result_image = color_code_paths(stitched_with_ground_paths, scores)

    # Save the image with color-coded paths
    cv2.imwrite('stitched_paths_scored.png', result_image)
