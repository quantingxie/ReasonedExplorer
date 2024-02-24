
from openai import OpenAI
import os

# TODO: Async need to be implemented

class RRT:
    def __init__(self, model, goal, branches, rounds, openai_api_key):
        self.client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY",openai_api_key))
        self.model = model
        self.goal = goal
        self.n = branches
        self.r = rounds

    def multi_turn_conversation(self, model, initial_description, rounds):
        messages = [
            {"role": "system", "content": f"You are a navigator tasked with outputting a new scene description conditioned on the description given with your navigation commonsense of what possibly ahead. Description: '{initial_description}'"},
        ]

        user_input = "Now, imagine what happens if you go straight further?"
        scene_descriptions = []

        for _ in range(rounds):  
            messages.append({"role": "user", "content": user_input})

            response = self.client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
            )

            # Extract the text of GPT-4's response and append it to the scene descriptions list
            gpt_response_text = response.choices[0].message['content']
            scene_descriptions.append(gpt_response_text)

            # Append GPT-4's response to the conversation history for context in the next round
            messages.append({"role": "assistant", "content": gpt_response_text})
        return scene_descriptions

    def generate_scene_descriptions(self, initial_description):
        """
        Generate multiple branches of scene descriptions.
        Each branch is 'rounds' long.
        """
        branches_descriptions = []
        for _ in range(self.n):
            scene_descriptions = self.multi_turn_conversation(self.model, initial_description, self.r)
            branches_descriptions.append(scene_descriptions)
        return branches_descriptions

    def score_scene_description(self, scene_description):
        # Function to score the scene description
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": f"How likely is this scene related to the goal: '{self.goal}'? Scene: '{scene_description}'"},
                {"role": "user", "content": "Score the relevance on a scale of 1 to 5."},
            ],
            temperature=0,  
        )
        score_text = response.choices[0].message['content']
        try:
            score = float(score_text)
        except ValueError:
            score = 0
        return score

    def run_rrt(self, initial_description):
        # Generate scene descriptions
        branches_descriptions = self.generate_scene_descriptions(initial_description, self.r, self.n)
        
        # Score each branch
        branch_scores = []
        for branch in branches_descriptions:
            branch_score = sum([self.score_scene_description(desc) for desc in branch]) / len(branch)
            branch_scores.append(branch_score)
        
        # Average score across the tree
        tree_score = sum(branch_scores) / len(branch_scores)
        return tree_score, branches_descriptions
