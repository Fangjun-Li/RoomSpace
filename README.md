<div align="center">
  <h1>🏠 RoomSpace Benchmark</h1> 
  <p>
    🌐 <a href="https://roomspace-benchmark.web.app/">Homepage</a> • 
    🤗 <a href="https://huggingface.co/datasets/Fangjun/RoomSpace">Hugging Face</a> • 
    📁 <a href="https://archive.researchdata.leeds.ac.uk/1293/">Dataset</a> • 
    📙 <a href="https://arxiv.org/abs/2405.15064">Paper</a>
  </p>
   <p><em>Simplify LLM evaluation using a convenient Colab notebook.</em></p>
   <a href="https://colab.research.google.com/drive/1fAK8J1UHAjMm-mNVsuzIbEZd-SZG6bX-?usp=sharing"><img src="img/colab.svg" alt="Open In Colab"></a></center>
</div>
<br/>






## 🔍 Overview

This repository contains the code used to generate the dataset for the RoomSpace benchmark, as introduced in the IJCAI-24 paper, [Reframing Spatial Reasoning Evaluation in Language Models: A Real-World Simulation Benchmark for Qualitative Reasoning](https://arxiv.org/pdf/2405.15064.pdf).

## 🏘️ Room Scene Generation Code
Our room generation code is based on [ProcTHOR](https://procthor.allenai.org/). Several modifications are required to generate room scenes effectively:

1. Install ProcTHOR by following the instructions provided [here](https://github.com/allenai/procthor).
2. Locate the `procthor` folder, then:
   - Replace the corresponding files under `./procthor/procthor/generation` with the files from this repository in the same directory.
   - Copy the `generate_room.py` file under `./procthor/scripts` in this repository to the corresponding folder in the downloaded ProcTHOR directory.
3. In the `./procthor` directory, run the example script to generate rooms by executing the following command:
   ```bash
   python scripts/generate_room.py
   ```

   The default setting is for generating SD-100. You can modify the `save_path` variable and adjust the `for i in range(0, 100)` loop to specify your desired save path and the number of rooms you want to generate.

## 📷 Image Generation Code

To generate images of the room, follow these steps:

- To get a top-down view image of the room, run the following command:
  ```bash
  python draw_top-down.py
  ```

- To get a view image of the room from a robot positioned at the south door, run the following command:
  ```bash
  python draw_robot-south.py
  ```

## 💻 Logical Reasoner
The `solver.py` module provides functions for solving spatial relationship constraints between objects within a grid of configurable size. 
### How to Use

1. **Set the Domain Size:**
   - Define the size of the grid (e.g., `(12, 12)` for a 12x12 grid) when calling `solve_single_candidate` or `solve_all_candidates`.

2. **Create Test Data:**
   - Define facts and queries for the relationships between objects within the grid. This data is passed into the `example` dictionary.

3. **Run the Solver:**
   - Use `solve_single_candidate` to check if a specific relationship holds true or `solve_all_candidates` to find all possible relationships.

### Example Usage

Here is how you might use the module in another script:

```python
from solver import solve_single_candidate, solve_all_candidates

# Set the domain size
domain_size = (12, 12)

# Define facts and queries
facts = [
    ("bed", "NER", "room"),
    ("dresser", "SWR", "room"),
    ("house plant", "ER", "room"),
    ("dining table", "CR", "room"),
    ("chair", "CR", "room"),
    ("bed", "NE", "dresser"),
    ("dresser", "SW", "house plant"),
    ("house plant", "SE", "dining table"),
    ("dining table", "N", "chair")
] 

query = [
    ("bed", "chair")
]

example = {'example_id': 0, "facts": facts, "query": query}

# Solving for a specific candidate relationship
yn_relation = "south-west"
solvable_answer, time_taken = solve_single_candidate(example, yn_relation, domain_size)
print(yn_relation, ":", solvable_answer, f"Time: {time_taken:.4f}s")

# Solving for all candidate relationships
solvable_relations, time_taken = solve_all_candidates(example, domain_size)
print("All Candidates:", solvable_relations, f"Time: {time_taken:.4f}s")
```

## 📃 Text Generation Code




## Citation

This code is used to generate rooms for the [RoomSpace](https://arxiv.org/pdf/2405.15064) paper:

```bibtex
@article{li2024reframing,
  title={Reframing Spatial Reasoning Evaluation in Language Models: A Real-World Simulation Benchmark for Qualitative Reasoning},
  author={Li, Fangjun and Hogg, David C and Cohn, Anthony G},
  journal={arXiv preprint arXiv:2405.15064},
  year={2024}
}
