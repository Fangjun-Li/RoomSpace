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


This repository contains the code used to generate the dataset for the RoomSpace benchmark, as introduced in the IJCAI-24 paper, [Reframing Spatial Reasoning Evaluation in Language Models: A Real-World Simulation Benchmark for Qualitative Reasoning](https://arxiv.org/pdf/2405.15064.pdf).

## 🏘️ Room Scene Generation Code
This section guides you through setting up and running the room scene generation code, which is based on [ProcTHOR](https://procthor.allenai.org/). 

1. Install ProcTHOR.
   Detailed installation instructions can be found on the [ProcTHOR GitHub repository](https://github.com/allenai/procthor).
2. Locate the `procthor` folder in your installation directory, replace and add files to customize room generation.
   - Replace the corresponding files under `./procthor/procthor/generation` with the files from this repository in the same directory.
   - Copy the `generate_room.py` file under `./procthor/scripts` in this repository to the corresponding folder in the downloaded ProcTHOR directory.
4. Navigate to the `./procthor` directory and run the example script to generate room scenes. Use the following command:
   ```bash
   python scripts/generate_room.py
   ```
   - Save path: By default, the script generates rooms for the SD-100 dataset. You can customize the `save_path` variable in the script to specify where the generated room configuration files should be saved.
   - Number of rooms: Adjust the loop `for i in range(0, 100)` to change the number of rooms generated.

**Check the Generated Meta Room Configuration Files**: After the script completes, check the `Meta/SD-100` folder. You should find the generated `.json` files for each room containing the configuration details.

## 📷 Image & Video Generation Code
After generating the room configurations, you can create images and videos to visualize the rooms. Below are the steps to generate top-down view images, robot perspective view images, and videos.

- To get a top-down view image of each room:
  ```bash
  python draw_top-down.py
  ```

- To generate images from a robot's perspective at the south door of each room:
  ```bash
  python draw_robot-south.py
  ```
**Check the Generated Images**: After the script completes, check the `Data/SD-100/Image/top-down` and `Data/SD-100/Image/robot-south` folder. You should see the generated `.jpg` image files corresponding to each room JSON file.

- To create videos showing a 360-degree view of each room:
  ```bash
  python create_video.py
  ```
**Check the Generated Videos**: After the script completes, check the `Data/SD-100/Video/` folder. You should find the generated `.mp4` video files, with each video corresponding to a room JSON file.

## 🧠 Logical Reasoner
Our CSP reasoner is based on the [Python constraint module](https://pypi.org/project/python-constraint/). To use it, first install the module by running:

```bash
pip install python-constraint
```

The `solver.py` script provides functions for solving spatial relationship constraints between objects within a configurable grid size.


### How to Use

1. **Set the Domain Size:**
   Define the size of the grid (e.g., `(12, 12)` for a 12x12 grid) when calling `solve_single_candidate` or `solve_all_candidates`.

2. **Create Test Data:**
   Define facts and queries for the relationships between objects within the grid. This data is passed into the `example` dictionary.

3. **Run the Solver:**
   Use `solve_single_candidate` to check if a specific relationship holds true or `solve_all_candidates` to find all possible relationships.

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

To run the script with the desired parameters, use the following command in your terminal:

```bash
python generate_vary_m_n.py --data_version SD-1K --test_num 1000 --domain_size (9, 9) --n_range [4] --m_range [3]
```

**Argument Descriptions**

 - **`--data_version`** (`str`, default: `'SD-100'`):
  Specifies the version of the dataset to use. This can be one of the predefined versions such as `SD-100`, `SD-1K`, or `SD-10k`.
  
- **`--test_num`** (`int`, default: `100`):
  Indicates the number of test cases the script should process. Adjust this value to process more or fewer test cases in a single run.
  
- **`--test_num_start`** (`int`, default: `0`):
  Sets the starting index for processing test cases. This is useful if you want to skip some initial test cases and start processing from a specific index.
  
- **`--domain_size`** (`tuple`, default: `(12, 12)`):
  Defines the size of the domain grid. This should be specified as a tuple of two integers representing the width and height of the grid.
  
- **`--n_range`** (`list`, default: `[5]`):
  Specifies the range of numbers indicating the number of objects to consider in the test cases. This can be a single number or a list of numbers.
  
- **`--m_range`** (`list`, default: `[4,5,6,7,8,9]`):
  Defines the range of numbers indicating the number of object pairs to consider. This should be provided as a list of numbers.
  
**Check the Generated Texts/Logic**: After the script completes, check the `Data/SD-100/Text/` and `Data/SD-100/Logic/`folder. You should find the generated `.json` files. The filenames typically indicate the specific parameters (`m`, `n`, `d`) used during generation. For example, a file named `n5_m4_d144.json` indicates that it was generated with `n=5`, `m=4`, and `domain_size=(12,12)`.

## Citation
```bibtex
@article{li2024reframing,
  title={Reframing Spatial Reasoning Evaluation in Language Models: A Real-World Simulation Benchmark for Qualitative Reasoning},
  author={Li, Fangjun and Hogg, David C and Cohn, Anthony G},
  journal={arXiv preprint arXiv:2405.15064},
  year={2024}
}
