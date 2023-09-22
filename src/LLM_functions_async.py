import openai
import asyncio
import aiohttp
import os
import requests
from tenacity import retry, stop_after_attempt, wait_random_exponential

async def fetch(session, url, headers, json_data):
    async with session.post(url, headers=headers, json=json_data) as response:
        return await response.json()
    
@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
async def LLM_evaluator_async(node, goal, model):
    prompt = f"""
        You are an judge to evaluate the likelihood of a user finding a specific goal within a described scene. Based on goal and scene info, you are to assign a Likert score from 1 to 5:

        1: Highly unlikely finding the goal.
        2: Unusual scenario, but there's a chance.
        3: Equal probability of finding or not finding the goal.
        4: Likely finding the goal.
        5: Very likely finding the goal.

        If the scene's background is largely object or walls, means you are about to hit something, give a score of -1 this case.
        If the goal specify somewhere not to go, you give a score of -1 if you think you are on it. For example, goal says not to go step on grass, you give a score of -1 if on the grass
        Your response should only be the score (a number between 1 and 5) without any additional commentary

        User's goal: {goal}
        Described scene:
        """ + str(node)
    # prompt = f"""
    #         You are a judge tasked with evaluating the likelihood of a user finding a specific conditioned on the path preference within a described scene. The goal consist of user's desired object and the prefered path. Based on goal and scene info, you are to assign a Likert score from 1 to 5:

    #         Scores:
    #         1: Highly unlikely finding the goal.
    #         2: Unusual scenario, but there's a chance.
    #         3: Equal probability of finding or not finding the goal.
    #         4: Likely finding the goal.
    #         5: Very likely finding the goal.

    #         *If the scene's background is primarily objects or walls (indicating a barrier), give a score of 1.*

    #         User's goal: {goal}


    #         Expected Output:
    #         Scene Recap: [Summary of scene elements]
    #         Reasoning: [Reasoning about the likelihood of achieving the goal]
    #         Score: [Assigned score based on the above reasoning]

    #         Described scene:
    #         """ + str(node)    
    message=[{"role": "user", "content": prompt}]
    request_payload = {
        "model": "gpt-4-0314",
        # "model": "gpt-3.5-turbo-16k",
        "messages": message,
        "temperature": 0.8,
        "max_tokens": 400,
        "frequency_penalty": 0.0
    }
    url="https://api.openai.com/v1/chat/completions"
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",  # replace with your API key
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, url, headers, request_payload)
        print("Response", response)
    try:
        score = int(response['choices'][0]['message']['content'].strip())
    except ValueError:
        # Handle unexpected output
        score = 3  # Default to a neutral score or handle differently as needed    
    print("Score:", score)
    return score

@retry(wait=wait_random_exponential(min=1, max=60), stop=stop_after_attempt(6))
async def LLM_world_model_async(node, model):
    prompt = f"""
        You are a world model tasked with outputting a new scene description based on an action and a previous scene. If an agent were to move forward by 10m from the provided scene, envision how this setting could evolve. Your response should stay true to the details of the current scene and be a detailed description, including the position of the agent.

        *Do not introduce new major elements that aren't present or hinted at in the initial observation. Emphasize physical structures and natural elements. The description shouldn't exceed 50 words.*

        1. Current Scene Recap:
        Before extrapolating, list down the major elements in the scene:

        - List of observed elements from the scene

        2. Extrapolation:
        Using the above elements, describe in details how the scene might look when the agent moves forward by 10m:

        Your Extrapolation Here

        Example 1:
        Scene: The image showcases a brick patio with a red dining table and chairs under a blue umbrella. The umbrella provides shade to the dining area. In the background, there's a brick wall.

        Observed elements:
        - Brick patio
        - Red dining table and chairs
        - Blue umbrella
        - Brick wall

        State Description: Moving 10m forward, the agent stands directly in front of the brick wall, touching its surface.The whole scene is largely the wall. 

        Example 2:
        Scene: The image displays in a plaza setting, a brick sidewalk with a tree to the left. Beside the tree is a building. On the right side of the sidewalk, there's another building and a bench close to it.

        Observed elements:
        - Brick sidewalk
        - Tree and building on the left
        - Another building and bench on the right

        State Description: Progressing 10m, the agent should still be in the plaza, stands near the tree. To the right, the building ends, a bicycle rack and bins are in sight.

        Now, Current scene observation: {node}
    """
    message=[{"role": "user", "content": prompt}]
    request_payload = {
        "model": model,
        "messages": message,
        "temperature": 0.8,
        "max_tokens": 3000,
        "frequency_penalty": 0.0
    }
    url="https://api.openai.com/v1/chat/completions"
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",  # replace with your API key
        "Content-Type": "application/json"
    }
    async with aiohttp.ClientSession() as session:
        response = await fetch(session, url, headers, request_payload)
    # print(f"Current scene observation: {node}")print(response)
    # print("=====Error===",response)
    extrapolated_scene = response['choices'][0]['message']['content'].strip()
    print("===Extrapolated scene:", extrapolated_scene)

    return extrapolated_scene

async def LLM_abstractor_async(nodes, model):
    prompt = f"""
    You are an AI trained to distill multiple scene descriptions into a higher, more abstract form. Your goal is to create a concise abstraction that encompasses the key information and underlying themes from all the provided scenes. 
    Given scene descriptions: {nodes}
    """
    message=[{"role": "user", "content": prompt}]
    request_payload = {
        "model": model,
        "messages": message,
        "temperature": 0.5,
        "max_tokens": 3000,
        "frequency_penalty": 0.0
    }
    url="https://api.openai.com/v1/chat/completions"
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",  # replace with your API key
        "Content-Type": "application/json"
    }

    async with aiohttp.ClientSession() as session:
        response = await fetch(session, url, headers, request_payload)
     
    # print(f"Given scene descriptions: {nodes}")
    abstracted_description = response['choices'][0]['message']['content'].strip()
    # print("Abstracted description:", abstracted_description)

    return abstracted_description

async def LLM_rephraser_async(node, global_context, model):
    prompt = f"""
    You are an AI tasked to rephrase and refine scene descriptions using broader context. Please reword the following scene description: '{node}' by incorporating the global context: '{global_context}'
    """    
    message=[{"role": "user", "content": prompt}]
    request_payload = {
        "model": model,
        "messages": message,
        "temperature": 0.5,
        "max_tokens": 3000,
        "frequency_penalty": 0.0
    }
    url="https://api.openai.com/v1/chat/completions"
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",  # replace with your API key
        "Content-Type": "application/json"
    }

    # print(f"Node to rephrase: {node}")
    # print(f"Using global context: {global_context}")

    async with aiohttp.ClientSession() as session:
        response = await fetch(session, url, headers, request_payload) 

    rephrased_description = response['choices'][0]['message']['content'].strip()
    # print("Rephrased description:", rephrased_description)
    return rephrased_description



def LLM_world_model_http(node, model):
    prompt = f"""
    You are an AI tasked with extrapolating from a given scene description. Based on the details provided in this scene, envision what this setting could evolve into if one were to continue forward. Your response should be a detailed scene description, focusing on potential elements that may logically appear ahead based on the current context.

    You should provide a concise description of the given environment that don't exceed 100 words. Emphasize physical structures and natural elements, ensuring specific details about their conditions and characteristics are included. Refrain from mentioning people or activities

        An example of the answer: Moving forward from the curb pavement, the walkway broadens into a cobblestone plaza. Ahead, dense trees form a shaded canopy, under which modern LED streetlights stand at regular intervals. The path leads to a large stone fountain surrounded by a manicured lawn and symmetrical plant beds filled with seasonal flowers. The cobblestone trail continues, branching into multiple paths lined with metal bicycle racks.
    
    Current scene observation: {node}
    """
    message = [{"role": "user", "content": prompt}]
    request_payload = {
        "model": model,
        "messages": message,
        "temperature": 0.5,
        "max_tokens": 3000,
        "frequency_penalty": 0.0
    }
    url = "https://api.openai.com/v1/chat/completions"
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=request_payload)
    
    response_data = response.json()
    if 'choices' not in response_data:
        print(response_data)  # Print the entire response for debugging
        return ""  # or handle in some other way
    else:
        extrapolated_scene = response_data['choices'][0]['message']['content'].strip()
    return extrapolated_scene

def LLM_evaluator_http(node, goal, model):
    prompt = f"""
        You are an judge to evaluate the likelihood of a user finding a specific goal within a described scene. Based on goal and scene info, you are to assign a Likert score from 1 to 5:

        1: Highly unlikely the user will find the goal.
        2: Unusual scenario, but there's a chance.
        3: Equal probability of finding or not finding the goal.
        4: Likely the user will find the goal.
        5: Very likely the user will find the goal.

        If you find the scene is largely object or walls, means you are about to hit something, give a score of 1 this case.
        Your response should only be the score (a number between 1 and 5) without any additional commentary

        User's goal: {goal}
        Described scene:
        """ + str(node)

    message = [{"role": "user", "content": prompt}]
    request_payload = {
        "model": model,
        "messages": message,
        "temperature": 0.8,
        "max_tokens": 1000,
        "frequency_penalty": 0.0
    }
    url = "https://api.openai.com/v1/chat/completions"
    api_key = os.getenv("OPENAI_API_KEY")
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    response = requests.post(url, headers=headers, json=request_payload)
    try:
        score = int(response.json()['choices'][0]['message']['content'].strip())
    except ValueError:
        score = 3  # Default to a neutral score or handle differently as needed

    print("Score:", score)
    return score