#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18, 2024

@author: Fangjun
"""

import os
import json
from ai2thor.controller import Controller
from PIL import Image

def read_json_file(file_path):
    """Reads a JSON file and returns its content."""
    with open(file_path, 'r') as file:
        return json.load(file)
    
def process_and_save_south_door_image(house, controller, output_path, is_first=False):
    """Processes and saves the robot view image of a room."""
    
    renderDepthImage = True  #@param {type: "boolean"}
    renderInstanceSegmentation = True  #@param {type: "boolean"}
    renderSemanticSegmentation = True  #@param {type: "boolean"}
    renderNormalsImage = True  #@param {type: "boolean"}

    if is_first:
        controller = Controller(scene=house, width=2048, height=1024, makeAgentsVisible=False)  # Create a new controller instance
    else:
        controller.reset(scene=house, width=2048, height=1024, makeAgentsVisible=False)  # Reset the existing controller with the new scene
    
    image = get_ego_frame(controller)    
    image.save(output_path)
    return controller

def get_ego_frame(controller):
    """adds a cameras from a third-person's point of view"""

    event = controller.step(dict(action='GetReachablePositions'))
    reachable_positions = event.metadata['actionReturn']
    
    max_z = min(position['z'] for position in reachable_positions)
    reachable_positions_at_max_z = [position for position in reachable_positions if position['z'] == max_z]
    
    
    middle_x = event.metadata["sceneBounds"]["size"]["x"]/2
    closest_position = min(reachable_positions_at_max_z, key=lambda pos: abs(pos['x'] - middle_x))
    target_position = closest_position

    teleport_action = dict(action='Teleport', x=target_position['x'], y=target_position['y'], z=target_position['z'], rotation=0, horizon=5, standing=True)
    event = controller.step(teleport_action)
    
    ego_frame = event.frame
    return Image.fromarray(ego_frame)
    

def cache_exists(file_path):
    """Check if a cache file exists for a given file path."""
    return os.path.isfile(file_path)

def main():
    meta_folder = './Meta/SD-100'  # Replace with the path to your 'meta' folder
    robot_south_output_folder = './Data/SD-100/Image/robot-south'  

    os.makedirs(robot_south_output_folder, exist_ok=True)  # Ensure the output folder exists
    controller = None
    first = True
    
    i=0
    for file_name in os.listdir(meta_folder):
        i += 1
        if file_name.endswith('.json'):
            json_file_path = os.path.join(meta_folder, file_name)
            south_door_output_image_path = os.path.join(robot_south_output_folder, file_name.replace('.json', '.png'))
            print(i, south_door_output_image_path)
            if not cache_exists(south_door_output_image_path):
                house = read_json_file(json_file_path)
                controller = process_and_save_south_door_image(house, controller, south_door_output_image_path, is_first=first)
                first = False

    if controller:
        controller.stop()  # Stop the controller when done

if __name__ == "__main__":
    main()
