import numpy as np
from typing import List, Tuple
from LLM_functions import LLM_evaluator, LLM_world_model
import time
import aiohttp
import asyncio

class MCTS:
    def __init__(self, eta, gamma, n, l, goal, model):
        self.eta = eta
        self.gamma = gamma
        self.n = n
        self.l = l
        self.goal = goal
        self.model = model
        """Initializes the Q-values and N-values."""
        self.Q = {}  # Placeholder for Q-values
        self.N = {}  # Placeholder for N-values
    
    def selection(self, S_t1: List[str], depth: int) -> Tuple[str, int]:
        """Recursively selects the best node."""
        print("\n")
        print("==========Doing Selection==========")
        
        # If S_t1 is a leaf node
        # if self.is_leaf(S_t1):
        values = []
        for idx, description in enumerate(S_t1):  # Iterate over descriptions directly
            print("Evaluating action for description", idx)
            q_value = self.Q.get(description, 0)
            n_value = self.N.get(description, 0)
            val = q_value + self.eta * LLM_evaluator(description, goal=self.goal, model=self.model) / (1 + n_value ** self.gamma)
            print("score of action for description", idx, "=", val, "Q = ", q_value)
            values.append(val)
        
        # Return the description with the highest value and the depth
        return S_t1[np.argmax(values)], depth
        
        # Otherwise, continue the recursive selection
        # else:
        #     selected_node, new_depth = self.selection(max(S_t1, key=lambda desc: self.Q.get(desc, 0)), depth+1)
        #     return selected_node, new_depth


    def expansion(self, S_t1_star: List) -> List:
        """Generates a list of possible nodes and selects one based on the probabilities."""
        print("\n")
        print("==========Doing Expansion==========")

        S_t2_list = []
        S_t2_pi_list = []
        for _ in range(self.n):
            S_t2 = LLM_world_model(S_t1_star, model=self.model)
            pi = LLM_evaluator(S_t2, self.goal, model=self.model)
            S_t2_list.append(S_t2)
            S_t2_pi_list.append(pi)

        # Make a copy of the original scores (unnormalized)
        original_scores = S_t2_pi_list.copy()

        # Normalize the probabilities to ensure they sum to 1
        S_t2_pi_list = [pi/sum(S_t2_pi_list) for pi in S_t2_pi_list]
        chosen_index = np.random.choice(len(S_t2_list), p=S_t2_pi_list)
        chosen_S_t2 = S_t2_list[chosen_index]
        chosen_pi = original_scores[chosen_index]  # Using the unnormalized score

        return chosen_S_t2, chosen_pi


    def simulation(self, S_t1) -> float:  # Changing the parameter to S_t1
        """Predicts the outcome for a single node."""  # Updated the description
        print("\n")
        print("==========Doing simulation==========")

        pi_list = []
        for l in range(1, self.l+1):
            S_t2_plus_l = LLM_world_model(S_t1, model=self.model)  # Updated to work with the single state
            pi_t2_plus_l = LLM_evaluator(S_t2_plus_l, self.goal, model=self.model)
            pi_list.append(pi_t2_plus_l)
        return pi_list

    def back_propagation(self, pi_mean: float, depth: int, S_t1_star: List) -> None:
        """Updates the Q-values and N-values."""
        print("\n")
        print("==========Doing back_propagation==========")

        Q_star = self.Q.get(str(S_t1_star), 0)
        # self.Q[str(S_t1_star)] = (Q_star + pi_mean) / depth
        self.Q[str(S_t1_star)] = pi_mean
        self.N[str(S_t1_star)] = self.N.get(str(S_t1_star), 0) + 1

    # def is_leaf(self, S_t: List) -> bool:
    #     """Determines if the given node is a leaf node."""
    #     return not str(S_t) in self.Q
    
    def run_mcts(self, K: int, S_t1_list: List) -> None:
        """Executes the MCTS algorithm."""
        
        for k in range(K):
            start_time = time.time()  # start timer
            
            S_t1_star, depth = self.selection(S_t1_list, 1)
            S_t2_sample, expansion_score  = self.expansion(S_t1_star)
            pi_list  = self.simulation(S_t2_sample)
            print("expansion_score", expansion_score)
            print("pi_list", pi_list)
            true_mean = (sum(pi_list) + expansion_score) / (len(pi_list) + 1)
            self.back_propagation(true_mean, depth, S_t1_star)
            
            end_time = time.time()  # end timer
            
            print(f"Iteration {k + 1} took {end_time - start_time:.6f} seconds.")