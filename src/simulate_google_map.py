# from MCTS_async import MCTS
from MCTS import MCTS
from RRT import rrt
from exploration_google_map import Exploration
import openai
import os
if __name__ == '__main__':

    
    openai.api_key = "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"
    MODEL = "gpt-3.5-turbo-16k"
    os.environ['OPENAI_API_KEY'] = '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'
    print(os.getenv("OPENAI_API_KEY"))
    ETA = 1 # Scaling factor for exploration
    GAMMA = 3 # N(S_t+1)^gamma
    X = 5  # X nodes to abstract
    K = 0.5  # Shapness of K
    d0 = 60 # This is the midpoint of sigmoid function, like a desired distance
    N = 3 # Action space and tree width
    L = 1  # Tree length
    fov = 120 # Field of View
    rom = 54 # Range of motion
    explorer_instance = None  # Declare this outside the try block so it can be accessed in the finally block



    exp_name = "Sim_Exp_RRT_1"
    exp_type = "MCTS" # baseline, RRT, MCTS
    try:

        goal = "Find the orange sports bag I left on the bench of the soccer field"
        # Initialize MCTS
        mcts_instance = MCTS(ETA, GAMMA, N, L, goal, MODEL)
        rrt_instance = rrt(N, L, goal, MODEL)
        print("MCTS Instance established")
        # Initialize Exploration with the MCTS instance
        explorer_instance = Exploration(exp_name, exp_type, mcts_instance, rrt_instance, X, K, d0, N, fov, rom, goal, MODEL)
        print("Explorer")
        # Run the exploration process
        explorer_instance.explore()

    except KeyboardInterrupt:
        print("\nReceived a KeyboardInterrupt! Stopping the exploration process.")
