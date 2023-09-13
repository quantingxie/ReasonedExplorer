# from MCTS_async import MCTS
from RRT import rrt
from MCTS import MCTS
from exploration_simulator import Exploration
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
    fov = 86 # Field of View
    rom = 120 # Range of motion
    explorer_instance = None  # Declare this outside the try block so it can be accessed in the finally block

    # Level 1: Find XS
    ################################
    '''L = 1, N = 3'''
    find_fountain_goal = "Find me a fountain"
    # Example NED position (N, E, D)
    find_fountain_start_pos = (-5, 0, -5) 
    find_fountain_start_yaw = 0
    #################################



    # Level 2: Find X conditioned on Y
    exp_name = "Sim_Exp_RRT_5_Fountain_L0_"
    exp_type = "RRT" # baseline, RRT, MCTS
    start_pos = find_fountain_start_pos  
    start_yaw = find_fountain_start_yaw
    goal = find_fountain_goal

    try:
        # Initialize MCTS
        mcts_instance = MCTS(ETA, GAMMA, N, L, goal, MODEL)
        rrt_instance = rrt(N, L, goal, MODEL)
        print("MCTS Instance established")
        # Initialize Exploration with the MCTS instance
        explorer_instance = Exploration(exp_name, exp_type, start_pos, start_yaw, mcts_instance, rrt_instance, X, K, d0, N, fov, rom, goal, MODEL)
        print("Explorer")
        # Run the exploration process
        explorer_instance.explore()

    except KeyboardInterrupt:
        print("\nReceived a KeyboardInterrupt! Stopping the exploration process.")
    finally:
        if explorer_instance:
            explorer_instance.cleanup()