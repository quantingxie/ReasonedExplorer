# import requests

# # Define the URL for the Flask app
# # app_url = 'http://localhost:5000'  # Update the URL as needed
# app_url = "https://6bb0-128-237-82-20.ngrok-free.app"

# # Define the image file to upload

# prompt1 = "<image>0</image>Describe every objects in the image and their spatial relationship with each other, and describe the backgrouds."
# prompt2 = "<image>0</image><grounding>list all objects in the image <phrase>"
# goal = "Bench"
# threshold=0.05

# def VLM_query(image_path):
#     image_file = {'image': open(image_path, 'rb')}
#     try:
#         # Send a POST request with the image file
#         response = requests.post(app_url, files=image_file, data={'text_inputs': prompt1, 'grounding_prompt':prompt2, 'goal':goal,'threshold':threshold})
#         data = response.json()
#         # print("Caption data",data)
#         if 'result' in data:
#             print("Extracted Text") #:", data['result'])
#         elif 'error' in data:
#             print("Error:", data['error'])
#         if 'found' in data:
#             print(f"Found {goal}:", data['found'])
#         if 'all_objects' in data:
#             print(f"Found all objects:", data['all_objects'])
#         # return data['result'],data['found']
#         return data['result']
#     except requests.exceptions.RequestException as e:
#         print("Request Error:", e)

import requests
from PIL import Image

# Define the URL for the Flask app
app_url = "https://6bb0-128-237-82-20.ngrok-free.app"

# Define prompts, goal, and threshold
prompt1 = "<image>0</image>Describe every objects in the image and their spatial relationship, and describe the backgrouds:"
# prompt1 = "<image>0</image>Describe this image in detail:"
prompt2 = "<image>0</image><grounding>list all objects in the image <phrase>"
goal = "Bench"
threshold = 0.05

def VLM_query(image_path):
    # Open the image using PIL
    with Image.open(image_path) as image:
        # Convert the image to a binary stream (in memory)
        from io import BytesIO
        byte_io = BytesIO()
        image.save(byte_io, 'PNG')
        image_file = {'image': byte_io.getvalue()}

        try:
            # Send a POST request with the image file
            response = requests.post(app_url, files=image_file, data={'text_inputs': prompt1, 'grounding_prompt': prompt2, 'goal': goal, 'threshold': threshold})
            data = response.json()
            if 'result' in data:
                print("Extracted Text")  # Remove the comment if you want the result text to be printed: , data['result'])
            elif 'error' in data:
                print("Error:", data['error'])
            if 'found' in data:
                print(f"Found {goal}:", data['found'])
            if 'all_objects' in data:
                print(f"Found all objects:", data['all_objects'])
            
            return data['result']
        
        except requests.exceptions.RequestException as e:
            print("Request Error:", e)
