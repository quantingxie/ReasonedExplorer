import syslog
from MCTS_async import MCTS
from exploration import Exploration
import openai
import asyncio
import os
if __name__ == '__main__':
    openai.api_key = "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"
    MODEL = "gpt-3.5-turbo"
    print(os.getenv("OPENAI_API_KEY"))
    ETA = 0.1 # Scaling factor for exploration
    GAMMA = 0.5 # N(S_t+1)^gamma
    X = 5  # X nodes to abstract
    K = 10  # How many iterations to run MCTS at each step
    N = 5 # Action space and tree width
    L = 3  # Tree length
    fov = 86 # Field of View
    rom = 70 # Range of motion


    goal = "Find me a picnic table"
    # Initialize MCTS
    mcts_instance = MCTS(ETA, GAMMA, N, L, goal, MODEL)

    # Initialize Exploration with the MCTS instance
    explorer_instance = Exploration(mcts_instance, X, K, N, fov, rom, MODEL)

    # Run the exploration process
    explorer_instance.explore()