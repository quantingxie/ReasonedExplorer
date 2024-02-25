import requests
import json
import base64


def GPT4V_baseline(image_path, goal_obj, openai_api_key):
    # Convert the image to a base64 encoded string
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # API endpoint for GPT-4 vision capabilities
    endpoint = "https://api.openai.com/v1/chat/completions"

        # Hardcoded prompt
    prompt = f"Is the object '{goal_obj}' present in the image in a reachable distance? Please only answer with 'yes' or 'no'."

    prompt = f"""Identify the grey paths in the image score each of them based on the likelihoood of finding '{goal_obj}' in the direction they pointing to.
                Please structure your response as follows:
                'Path [Number]: [score];'
                Ensure each path's score is terminated with a semicolon and a newline for easy parsing."""

    # Headers for authentication and content type
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None


def GPT4V_query(image_path, openai_api_key):
    # Convert the image to a base64 encoded string
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # API endpoint for GPT-4 vision capabilities
    endpoint = "https://api.openai.com/v1/chat/completions"

        # Hardcoded prompt
    prompt = """Identify the grey paths in the image and describe the space at their endpoints, 
                specifying where each leads with logical inference based on visual cues. 
                Please structure your response with clear separation and numbering for each path, as follows:
                'Path [Number]: [Destination description];'
                Ensure each path's description is terminated with a semicolon and a newline for easy parsing."""

    # Headers for authentication and content type
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def GPT4V_query(image_path, openai_api_key):
    # Convert the image to a base64 encoded string
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # API endpoint for GPT-4 vision capabilities
    endpoint = "https://api.openai.com/v1/chat/completions"

        # Hardcoded prompt
    prompt = """Identify the grey paths in the image and describe the space at their endpoints, 
                specifying where each leads with logical inference based on visual cues. 
                Please structure your response with clear separation and numbering for each path, as follows:
                'Path [Number]: [Destination description];'
                Ensure each path's description is terminated with a semicolon and a newline for easy parsing."""

    # Headers for authentication and content type
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}"
                        }
                    }
                ]
            }
        ],
        "max_tokens": 500
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None



def phi2_query(image_path):
    
    app_url = "https://a7de-128-237-82-9.ngrok-free.app/vlm"

    # Hardcoded prompt
    # prompt = "Identify the grey paths in the image, describe the space in the end point, specifying whether it leads to with logical inference using visual cues. Structure your response as follows: 'Path [Number]: [Destination description]"
    prompt = "Describe the objects in the scene"
    # Define the image file to upload
    image_file = {'image': open(image_path, 'rb')}
    
    try:
        # Send a POST request with the image file and the hardcoded prompt
        response = requests.post(app_url, files=image_file, data={'text': prompt})
        data = response.json()
        if 'error' in data:
            print("Error:", data['error'])
    except requests.exceptions.RequestException as e:
        print("Request Error:", e)
        data = {'error': str(e)}
    finally:
        # Ensure the file is closed after the request
        image_file['image'].close()
    
    return data['response']


def parse_response(response_text):
    """
    Parse the structured response from GPT-4 Vision and return a dictionary.
    
    Args:
    - response_text (str): The structured response from GPT-4 Vision.
    
    Returns:
    - dict: A dictionary where keys are path identifiers and values are answers.
    """
    # Split the response into parts based on the semicolon and newline
    parts = response_text.strip().split(';\n')
    
    parsed_data = {}
    for part in parts:
        if part:
            # Split each part at the first colon to separate the path identifier from the answer
            path, answer = part.split(':', 1)
            parsed_data[path.strip()] = answer.strip()
    
    return parsed_data

def success_checker(image_path, goal_obj):
    app_url = "https://a7de-128-237-82-9.ngrok-free.app/vlm"

    prompt = f"Is the object '{goal_obj}' present in the image in a reachable distance? Please only answer with 'yes' or 'no'."
    # Define the image file to upload
    image_file = {'image': open(image_path, 'rb')}
    
    try:
        # Send a POST request with the image file and the hardcoded prompt
        response = requests.post(app_url, files=image_file, data={'text': prompt})
        data = response.json()
        if 'error' in data:
            print("Error:", data['error'])
    except requests.exceptions.RequestException as e:
        print("Request Error:", e)
        data = {'error': str(e)}
    finally:
        # Ensure the file is closed after the request
        image_file['image'].close()
    
    return data['response']

def GPT4V_checker(image_path, goal_obj, openai_api_key):
    """
    Check if the goal object is present in the image using GPT-4 Vision.

    Args:
    - image_path (str): Path to the image file.
    - goal_obj (str): Goal object to search for in the image.
    - openai_api_key (str): OpenAI API key for authentication.

    Returns:
    - str: "yes" if the goal object is found, "no" otherwise.
    """
    # Convert the image to a base64 encoded string
    with open(image_path, "rb") as image_file:
        base64_image = base64.b64encode(image_file.read()).decode("utf-8")
    
    # Update the prompt to explicitly ask about the presence of the goal object
    prompt = f"Is the object '{goal_obj}' present in the image in a reachable distance? Please only answer with 'yes' or 'no'."

    # API endpoint for GPT-4 vision capabilities
    endpoint = "https://api.openai.com/v1/chat/completions"

    # Headers for authentication and content type
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }

    # Prepare the payload with the updated prompt and the base64 image
    payload = {
        "model": "gpt-4-vision-preview",
        "messages": [
            {
                "role": "user",
                "content": prompt
            },
            {
                "role": "system",
                "content": {
                    "type": "image",
                    "data": f"data:image/jpeg;base64,{base64_image}"
                }
            }
        ],
        "max_tokens": 50  
    }

    try:
        response = requests.post(endpoint, headers=headers, data=json.dumps(payload))
        response_data = response.json()
        # Parse the response to find the answer (yes or no)
        answer = parse_yes_no(response_data)
        return answer

    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        return None

def parse_yes_no(response_data):
    try:
        messages = response_data.get('choices', [])[0].get('message', {}).get('content', '')
        if "yes" or "Yes" in messages.lower():
            return "yes"
        elif "no" or "No" in messages.lower():
            return "no"
        else:
            return "Response unclear"
    except IndexError:
        return "Error parsing response"


