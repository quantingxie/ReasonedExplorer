import openai

def LLM_evaluator(node, goal, model):
    prompt = f"""
        You are an AI judge assigned to evaluate the likelihood of a user finding a specific goal within a described scene. All relevant details about the goal and the scene will be provided in text format. Based on the information, you are to assign a Likert score ranging from 1 to 5. Here's what each score represents:

        1: Highly unlikely the user will find the goal.
        2: Unusual scenario, but there's a chance.
        3: Equal probability of finding or not finding the goal.
        4: Likely the user will find the goal.
        5: Very likely the user will find the goal.

        Your response should only be the score (a number between 1 and 5) without any additional commentary.

        User's goal: {goal}
        Described scene:
        """ + str(node)
    
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.2,
        max_tokens=3000,
        frequency_penalty=0.0
    )
    print(response['choices'][0]['message']['content'].strip())
    score = int(response['choices'][0]['message']['content'].strip())
    print(score)
    return score

def LLM_world_model(node, model):
    prompt = f"""
    You are an AI tasked with extrapolating from a given scene description. Based on the details provided in this scene, envision what this setting could evolve into if one were to continue forward. Your response should be a detailed scene description, focusing on potential elements that may logically appear ahead based on the current context. 

    Current scene observation: {node}
    """
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.2,
        max_tokens=3000,
        frequency_penalty=0.0
    )
    return response.choices[0].message['content'].strip()

def LLM_abstractor(nodes, model):
    prompt = f"""
    You are an AI trained to distill multiple scene descriptions into a higher, more abstract form. Your goal is to create a concise abstraction that encompasses the key information and underlying themes from all the provided scenes. 
    Given scene descriptions: {nodes}
    """
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.2,
        max_tokens=3000,
        frequency_penalty=0.0
    )
    return response.choices[0].message['content'].strip()

def LLM_rephraser(node, global_context, model):
    prompt = f"""
    You are an AI tasked to rephrase and refine scene descriptions using broader context. Please reword the following scene description: '{node}' by incorporating the global context: '{global_context}'
    """    
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.2,
        max_tokens=3000,
        frequency_penalty=0.0
    )
    return response.choices[0].message['content'].strip()
