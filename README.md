# ReasonedExplorer

## Reasoning about the unseen for efficient outdoor object navigation

### Introduction:
In the realm of outdoor object navigation, understanding and reasoning about unseen objects is of paramount importance. This repository contains the code, datasets, and supplementary materials related to our paper.

### The Challenge:
#### Sensory challenges of deploying current methods in outdoor/real-world navigation:
- **Poor depth perception**: This makes VSLAM nearly unusable in outdoor environments.

(Add more challenges or key points as they appear in your paper.)

### Repository Structure:
- `src/`: Contains the source code of Reasoned_Explorer
  - `utils/`: Helper functions.
  - `simulator_utils/`: Helper functions for Airsim
  - `LLM_functions`: All llm functions goes here
  - `LLM_functions_async`: Paralleled LLM functions 
  - `simulate`: Main script for experiments in simulator, where you specify the goal and the algorithm to run
  - `real`: An example script for experiments in real environment, need additional local planners/GPS implementation for your own robot setup.
  - `exploration_simulator` : The logic script for graph building and visualization
  - `RRT`: The main agent script for Reasoned-Explorer, where hullucination and action happens
  - `VLM`: Kosmos-2 VLM can be queried on our server



### Getting Started:
1. **Install requirements.txt**
2. **Setup**: Download AirSim and 
3. **Running Experiments**: Change the script

### Citation:
If you find our work useful in your research, please consider citing our paper:
@misc{xie2023reasoning,
      title={Reasoning about the Unseen for Efficient Outdoor Object Navigation}, 
      author={Quanting Xie and Tianyi Zhang and Kedi Xu and Matthew Johnson-Roberson and Yonatan Bisk},
      year={2023},
      eprint={2309.10103},
      archivePrefix={arXiv},
      primaryClass={cs.RO}
}