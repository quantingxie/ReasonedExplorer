# ReasonedExplorer

## Reasoning about the unseen for efficient outdoor object navigation

### Abstract:
— Robots should exist anywhere humans do: indoors, outdoors, and even unmapped environments. In contrast,
the focus of recent advancements in Object Goal Navigation
(OGN) has targeted navigating in indoor environments
by leveraging spatial and semantic cues that do not generalize
outdoors. While these contributions provide valuable insights
into indoor scenarios, the broader spectrum of real-world
robotic applications often extends to outdoor settings. As
we transition to the vast and complex terrains of outdoor
environments, new challenges emerge. Unlike the structured
layouts found indoors, outdoor environments lack clear spatial
delineations and are riddled with inherent semantic ambiguities.
Despite this, humans navigate with ease because we can reason
about the unseen. We introduce a new task OUTDOOR, a new
mechanism for Large Language Models (LLMs) to accurately
hallucinate possible futures, and a new computationally aware
success metric for pushing research forward in this more
complex domain. Additionally, we show impressive results on
both a simulated drone and physical quadruped in outdoor
environments. Our agent has no premapping and our formalism
outperforms naive LLM-based approaches.

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
  - `settings.json`: Default settings for AirSim's sensors, you could add cameras and add other sensors here.



### Getting Started:
1. **Install requirements.txt**
2. **Setup**: 
    - Download AirSim: https://microsoft.github.io/AirSim/
    - Downtown West Modular Pack in Unreal Engine Marketplace under free environments categoty
    - Setup Google API-key
    - Setup OpenAI API-key
3. **Running Experiments**: Change the simulate.py script


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