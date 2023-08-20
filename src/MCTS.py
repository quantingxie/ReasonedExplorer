import numpy as np
from typing import List, Tuple
from .LLM_functions import LLM_evaluator, LLM_world_model

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
    
    def selection(self, S_t: List, depth: int) -> Tuple[List, int]:
        """Recursively selects the best node."""
        # If S_t is a leaf node
        if self.is_leaf(S_t):
            values = []
            for S_t1 in range(self.n):
                q_value = self.Q.get(str(S_t1), 0)
                n_value = self.N.get(str(S_t1), 0)
                val = q_value + self.eta * LLM_evaluator(S_t1, goal= self.goal, model= self.model) / (1 + n_value ** self.gamma)
                values.append(val)
            return self.n[np.argmax(values)], depth
        # Otherwise, continue the recursive selection
        else:
            selected_node, new_depth = self.selection(max(self.n, key=lambda x: self.Q.get(str(x), 0)), depth+1)
            return selected_node, new_depth

    def expansion(self, S_t1_star: List) -> List:
        """Generates a list of possible nodes and selects one based on the probabilities."""
        S_t2_list = []
        S_t2_pi_list = []
        for _ in range(self.n):
            S_t2 = LLM_world_model(S_t1_star, model=self.model)
            pi = LLM_evaluator(S_t2, self.goal, model=self.model)
            S_t2_list.append(S_t2)
            S_t2_pi_list.append(pi)
        return np.random.choice(S_t2_list, p=S_t2_pi_list)

    def simulation(self, S_t1_list: List) -> float:
        """Predicts the outcome for a series of nodes."""
        pi_list = []
        for l in range(1, self.l+1):
            S_t2_plus_l = LLM_world_model(S_t1_list[l+1], model=self.model)
            pi_t2_plus_l = LLM_evaluator(S_t2_plus_l, self.goal, model=self.model)
            pi_list.append(pi_t2_plus_l)
        return np.mean(pi_list)

    def back_propagation(self, pi_mean: float, depth: int, S_t1_star: List) -> None:
        """Updates the Q-values and N-values."""
        Q_star = self.Q.get(str(S_t1_star), 0)
        self.Q[str(S_t1_star)] = (Q_star + pi_mean) / depth
        self.N[str(S_t1_star)] = self.N.get(str(S_t1_star), 0) + 1

    def is_leaf(self, S_t: List) -> bool:
        """Determines if the given node is a leaf node."""
        return not str(S_t) in self.Q
    
    def run_mcts(self, K: int, S_t1_list: List) -> None:
        """Executes the MCTS algorithm."""
        for k in range(K):
            S_t1_star, depth = self.selection(S_t1_list, 1)
            S_t2_sample = self.expansion(S_t1_star)
            pi_mean = self.simulation(S_t2_sample)
            self.back_propagation(pi_mean, depth, S_t1_star)