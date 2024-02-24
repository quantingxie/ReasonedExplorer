import argparse
from src.llm_rrt import RRT
from src.exploration import Exploration 


OPENAI_API_KEY = "1Uk1lDxQW4Zg9zG6u3qcT3BlbkFJqFqclakGCEDaTFu91piW"

def get_args():
    parser = argparse.ArgumentParser(description="Run robot exploration using RRT or Baseline methods.")
    parser.add_argument("--exp_name", type=str, required=True, help="Name of the experiment.")
    parser.add_argument("--type", type=str, choices=['RRT', 'baseline'], required=True, help="Type of experiment: RRT or baseline.")
    parser.add_argument("--goal", type=str, required=True, help="Goal for the robot to achieve.")
    parser.add_argument("--n", type=int, default=5, help="Number of branches for RRT exploration.")
    parser.add_argument("--rounds", type=int, default=3, help="Number of rounds for RRT exploration.")
    parser.add_argument("--model", type=str, default="text-davinci-003", help="Model to use for GPT queries.")
    parser.add_argument("--api_key", type=str, default=OPENAI_API_KEY, help="OpenAI API key.")
    
    args = parser.parse_args()
    return args


def main():
    args = get_args()

    rrt = RRT(model=args.model, goal=args.goal, branches=args.n, rounds=args.rounds, openai_api_key=args.api_key)

    exploration = Exploration(exp_name=args.exp_name, type=args.type, rrt=rrt, n=args.n, goal=args.goal)

    exploration.explore()

if __name__ == "__main__":
    main()



