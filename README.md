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
