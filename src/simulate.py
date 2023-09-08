from MCTS_async import MCTS
from exploration_simulator import Exploration
import openai
import os
if __name__ == '__main__':

    
    openai.api_key = "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"
    MODEL = "gpt-3.5-turbo"
    os.environ['OPENAI_API_KEY'] = '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'
    print(os.getenv("OPENAI_API_KEY"))
    ETA = 0.1 # Scaling factor for exploration
    GAMMA = 0.5 # N(S_t+1)^gamma
    X = 5  # X nodes to abstract
    K = 1  # How many iterations to run MCTS at each step
    N = 3 # Action space and tree width
    L = 1  # Tree length
    fov = 86 # Field of View
    rom = 90 # Range of motion
    explorer_instance = None  # Declare this outside the try block so it can be accessed in the finally block

    try:

        goal = "Find me a picnic table"
        # Initialize MCTS
        mcts_instance = MCTS(ETA, GAMMA, N, L, goal, MODEL)
        print("MCTS Instance established")
        # Initialize Exploration with the MCTS instance
        explorer_instance = Exploration(mcts_instance, X, K, N, fov, rom, MODEL)
        print("Explorer")
        # Run the exploration process
        explorer_instance.explore()

    except KeyboardInterrupt:
        print("\nReceived a KeyboardInterrupt! Stopping the exploration process.")
    finally:
        if explorer_instance:
            explorer_instance.cleanup()