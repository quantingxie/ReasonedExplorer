import random

def VLM_query(image):
    """Mock function to simulate capturing a picture and generating a node."""
    mock_description = "This scene features a park, likely an urban park area, with a curb pavement. You see a bicycle, a car, a meter parking meter, and a pole to your front"
    
    # Randomly generate bounding box coordinates
    x1 = random.randint(0, 192)  # 192 ensures the bbox has room on the screen for width
    y1 = random.randint(0, 192)  # 192 ensures the bbox has room on the screen for height
    x2 = random.randint(x1 + 50, 384)  # x2 is guaranteed to be greater than x1 by at least 50 pixels
    y2 = random.randint(y1 + 50, 384)  # y2 is guaranteed to be greater than y1 by at least 50 pixels

    mock_bbox = (x1, y1, x2, y2)
    
    return mock_description, mock_bbox