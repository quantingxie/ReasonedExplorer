
import asyncio
import numpy as np
from typing import List, Tuple
from LLM_functions_async import LLM_evaluator_async, LLM_world_model_async

class rrt:
    def __init__(self, n, l, goal, model):
        self.n = n
        self.l = l
        self.goal = goal
        self.model = model
        self.Q = {}  # Placeholder for Q-values
    
    async def expansion(self, S_t1: List[str]) -> List[Tuple[str, float]]:
        """Expand on a single node asynchronously for n times."""
        tasks = [LLM_world_model_async(S_t1, model=self.model) for _ in range(self.n)]
        S_t2_list = await asyncio.gather(*tasks)

        evaluator_tasks = [LLM_evaluator_async(S_t2, self.goal, model=self.model) for S_t2 in S_t2_list]
        pi_list = await asyncio.gather(*evaluator_tasks)

        return list(zip(S_t2_list, pi_list))

    async def simulation_async(self, S_t2: str) -> List[float]:
        """Simulates the outcome for a single node asynchronously."""
        pi_list = []
        for _ in range(self.l):
            S_t2_plus_l = await LLM_world_model_async(S_t2, model=self.model)
            pi_t2_plus_l = await LLM_evaluator_async(S_t2_plus_l, self.goal, model=self.model)
            pi_list.append(pi_t2_plus_l)
        return pi_list
    
    def run_rrt(self, S_t1_list: List) -> None:
        """Execute the RRT approach."""
        print("Starting RRT run...")

        async def mcts_coroutine():
            # 1. Expand on each S_t1
            print("Step 1: Expanding on each S_t1 node...")
            expansion_tasks = asyncio.gather(*[self.expansion(s) for s in S_t1_list])
            all_expanded_nodes_and_scores = await expansion_tasks

            # 2. Do simulations on all of the expanded nodes simultaneously
            print("Step 2: Starting simulations for expanded nodes...")
            simulation_tasks = asyncio.gather(*[self.simulation_async(node) for expanded_nodes_and_scores in all_expanded_nodes_and_scores for node, _ in expanded_nodes_and_scores])
            simulation_results = await simulation_tasks

            # 3. Average the scores of the simulations and expansions
            print("Step 3: Averaging scores for simulations and expansions...")
            sim_index = 0
            for idx, s in enumerate(S_t1_list):
                total_scores = []
                for node, score in all_expanded_nodes_and_scores[idx]:
                    total_scores.append(score)
                    total_scores.extend(simulation_results[sim_index])
                    sim_index += 1

                # Average the scores
                true_mean = sum(total_scores) / len(total_scores)

                # 4. Update the Q value of each S_t1
                self.Q[str(s)] = true_mean
                print(f"Updated Q value for node {s}: {true_mean}")

        loop = asyncio.get_event_loop()
        if loop.is_closed():
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

        try:
            loop.run_until_complete(mcts_coroutine())
        finally:
            loop.close()
