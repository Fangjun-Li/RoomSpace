#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18 13:01:26 2024

@author: lfj
"""

import cv2
import os
import glob
import json
from ai2thor.controller import Controller
from PIL import Image
import shutil

def read_json_file(file_path):
    """Reads a JSON file and returns its content."""
    with open(file_path, 'r') as file:
        return json.load(file)
    
    
def create_video_from_images(folder_path: str, output_video_file: str, fps: int = 30):
    """
    Creates a video from a sequence of images stored in a folder.

    Args:
        folder_path (str): Path to the folder containing images.
        output_video_file (str): Path where the output video will be saved.
        fps (int): Frames per second for the output video.
    """
    image_files = glob.glob(os.path.join(folder_path, '*.jpg'))
    
    # Sort image files numerically
    image_files.sort(key=lambda x: int(os.path.splitext(os.path.basename(x))[0]))

    if not image_files:
        print("No images found in the directory.")
        return
    
    first_frame = cv2.imread(image_files[0])
    if first_frame is None:
        print("Error reading the first image.")
        return

    height, width, _ = first_frame.shape
    video = cv2.VideoWriter(output_video_file, cv2.VideoWriter_fourcc(*'mp4v'), fps, (width, height))

    for image_file in image_files:
        frame = cv2.imread(image_file)
        if frame is None:
            print(f"Error reading image {image_file}. Skipping...")
            continue
        video.write(frame)
        print(f"Added {image_file}")

    video.release()
    print(f"Video created successfully: {output_video_file}")

def cache_exists(file_path):
    """Check if a cache file exists for a given file path."""
    return os.path.isfile(file_path)

def main():
    meta_folder = './Meta/SD-100'
    video_folder = './Data/SD-100/Video'
    images_cache_folder = './Data/SD-100/Video/cache'
    
    for file_name in os.listdir(meta_folder):
        output_video_file = os.path.join(video_folder, file_name.replace('.json', '.mp4'))
        if not cache_exists(output_video_file):
            os.makedirs(images_cache_folder, exist_ok=True)
    
            if not file_name.endswith('.json'):
                continue
    
            json_file_path = os.path.join(meta_folder, file_name)
            example = read_json_file(json_file_path)
            house = example
    
            controller = Controller(scene=house, width=764, height=512, makeAgentsVisible=False, fieldOfView=100)
            event = controller.step(dict(action='GetReachablePositions'))
            reachable_positions = event.metadata['actionReturn']
            
            # min_z = min(position['z'] for position in reachable_positions)
            middle_z = event.metadata["sceneBounds"]["size"]["z"] / 2
            middle_x = event.metadata["sceneBounds"]["size"]["x"] / 2
            middle_position = min(reachable_positions, key=lambda pos: abs(pos['z'] - middle_z) and abs(pos['x'] - middle_x))
        
            for i, rotation in enumerate(range(0, 360, 1)):
                output_image_path = os.path.join(images_cache_folder, f"{i}.jpg")
                event = controller.step(action="Teleport", position=middle_position, rotation=dict(x=0, y=int(rotation), z=0), horizon=0)
                image = Image.fromarray(event.frame)
                image.save(output_image_path)
        
            controller.stop()
        
            create_video_from_images(images_cache_folder, output_video_file)
            
            shutil.rmtree(images_cache_folder)


if __name__ == "__main__":
    main()