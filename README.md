# ReasonedExplorer

## Reasoning about the unseen for efficient outdoor object navigation

### Exploration Modes:
Search Mode: Search through the graph for a node with a description that has high semantic similarity to the goal. If such a node is found and the similarity is above a threshold, the robot will move directly to that node.
Exploration Mode: If no node with high enough semantic similarity is found, the robot will continue to explore by expanding nodes and assessing their scores and descriptions relative to the goal.


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
  - `settings.json`: Default settings for AirSim's sensors, you could add cameras and add other sensors here.



### Getting Started:
1. **Install requirements.txt**
2. **Setup**: 
    - Setup Google API-key
    - Setup OpenAI API-key
3. **Example Use**: `python run.py --exp_name "Forest Exploration" --type RRT --goal "Find the river" --n 5 --rounds 3`



### Citation:
If you find our work useful in your research, please consider citing our paper. Below is the BibTeX entry:

```bibtex
@misc{xie2023reasoning,
      title={Reasoning about the Unseen for Efficient Outdoor Object Navigation}, 
      author={Quanting Xie and Tianyi Zhang and Kedi Xu and Matthew Johnson-Roberson and Yonatan Bisk},
      year={2023},
      eprint={2309.10103},
      archivePrefix={arXiv},
      primaryClass={cs.RO}
}