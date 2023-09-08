import openai
# model4 = "gpt-3.5-turbo"

def LLM_evaluator(node, goal, model):
    prompt = f"""
        You are an AI judge assigned to evaluate the likelihood of a user finding a specific goal within a described scene. All relevant details about the goal and the scene will be provided in text format. Based on the information, you are to assign a Likert score ranging from 1 to 5. Here's what each score represents:

        1: Highly unlikely the user will find the goal.
        2: Unusual scenario, but there's a chance.
        3: Equal probability of finding or not finding the goal.
        4: Likely the user will find the goal.
        5: Very likely the user will find the goal.

        Your response should only be the score (a number between 1 and 5) without any additional commentary. For instance, if it's very likely, simply reply with "5".

        User's goal: {goal}
        Described scene:
        """ + str(node)
    
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.9,
        max_tokens=1000,
        frequency_penalty=0.0
    )
    # print(f"Node: {node}")
    try:
        score = int(response['choices'][0]['message']['content'].strip())
    except ValueError:
        # Handle unexpected output
        score = 3  # Default to a neutral score or handle differently as needed    
    print("Score:", score)
    return score

def LLM_world_model(node, model):
    prompt = f"""
    You are an AI tasked with extrapolating from a given scene description. Based on the details provided in this scene, envision what this setting could evolve into if one were to continue forward. Your response should be a detailed scene description, focusing on potential elements that may logically appear ahead based on the current context.

    You should provide a concise description of the given environment that don't exceed 100 words. Emphasize physical structures and natural elements, ensuring specific details about their conditions and characteristics are included. Refrain from mentioning people or activities

    An example of the answer: Moving forward from the curb pavement, the walkway broadens into a cobblestone plaza. Ahead, dense trees form a shaded canopy, under which modern LED streetlights stand at regular intervals. The path leads to a large stone fountain surrounded by a manicured lawn and symmetrical plant beds filled with seasonal flowers. The cobblestone trail continues, branching into multiple paths lined with metal bicycle racks.
    
    Current scene observation: {node}
    """
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.5,
        max_tokens=3000,
        frequency_penalty=0.0
    )
    print(f"Current scene observation: {node}")
    extrapolated_scene = response.choices[0].message['content'].strip()
    print("Extrapolated scene:", extrapolated_scene)

    return extrapolated_scene

def LLM_abstractor(nodes, model):
    prompt = f"""
    You are an AI trained to distill multiple scene descriptions into a higher, more abstract form. Your goal is to create a concise abstraction that encompasses the key information and underlying themes from all the provided scenes. 
    Given scene descriptions: {nodes}
    """
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.5,
        max_tokens=3000,
        frequency_penalty=0.0
    )

    print(f"Given scene descriptions: {nodes}")
    abstracted_description = response.choices[0].message['content'].strip()
    print("Abstracted description:", abstracted_description)

    return abstracted_description

def LLM_rephraser(node, global_context, model):
    prompt = f"""
    You are an AI tasked to rephrase and refine scene descriptions using broader context. Please reword the following scene description: '{node}' by incorporating the global context: '{global_context}'
    """    
    message=[{"role": "user", "content": prompt}]
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages = message,
        temperature=0.8,
        max_tokens=3000,
        frequency_penalty=0.0
    )

    print(f"Node to rephrase: {node}")
    print(f"Using global context: {global_context}")

    rephrased_description = response.choices[0].message['content'].strip()
    print("Rephrased description:", rephrased_description)
    return rephrased_description
