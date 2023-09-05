import requests

# Define the URL for the Flask app
# app_url = 'http://localhost:5000'  # Update the URL as needed
app_url = "https://6bb0-128-237-82-20.ngrok-free.app"

# Define the image file to upload

prompt1 = "<image>0</image>Describe the objects in the image and summarize"
prompt2 = "<image>0</image><grounding>list all objects in the image <phrase>"
goal = "bench"
threshold=0.05

def VLM_query(image_path):
    image_file = {'image': open(image_path, 'rb')}
    try:
        # Send a POST request with the image file
        response = requests.post(app_url, files=image_file, data={'text_inputs': prompt1, 'grounding_prompt':prompt2, 'goal':goal,'threshold':threshold})
        data = response.json()
        print(data)
        if 'result' in data:
            print("Extracted Text:", data['result'])
        elif 'error' in data:
            print("Error:", data['error'])
        if 'found' in data:
            print(f"Found {goal}:", data['found'])
        if 'all_objects' in data:
            print(f"Found all objects:", data['all_objects'])
        return data['result'],data['found']

    except requests.exceptions.RequestException as e:
        print("Request Error:", e)

# def VLM_query(image):
#     """Mock function to simulate capturing a picture and generating a node."""
#     mock_description = "This scene features a park, likely an urban park area, with a curb pavement. You see a bicycle, a car, a meter parking meter, and a pole to your front"
    
#     # Randomly generate bounding box coordinates
#     x1 = random.randint(0, 192)  # 192 ensures the bbox has room on the screen for width
#     y1 = random.randint(0, 192)  # 192 ensures the bbox has room on the screen for height
#     x2 = random.randint(x1 + 50, 384)  # x2 is guaranteed to be greater than x1 by at least 50 pixels
#     y2 = random.randint(y1 + 50, 384)  # y2 is guaranteed to be greater than y1 by at least 50 pixels

#     mock_bbox = (x1, y1, x2, y2)
    
#     return mock_description, mock_bbox