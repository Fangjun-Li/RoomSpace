#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18, 2024

@author: Fangjun
"""

import json
import os
import re
import random
import inflect
import argparse
from pathlib import Path
from collections import Counter
from solver import solve_single_candidate, solve_all_candidates

def read_json_file(file_path):
    """Read and return the content of a JSON file."""
    with open(file_path, 'r') as file:
        return json.load(file)

def load_data(files):
    """Load multiple JSON files and return their contents."""
    return {name: read_json_file(path) for name, path in files.items()}

def read_and_concatenate_json_files(directory, data_version):
    output_file = Path(f'./Data/{data_version}/{data_version}.json')
    
    if output_file.exists():
        print(f"Concatenation Data '{output_file.name}'.")
        return

    json_files = sorted(Path(directory).glob("*.json"), key=lambda x: int(x.stem))  # Sort files based on the number in the filename
    
    all_data = []
    for json_file in json_files:
        with json_file.open('r') as file:
            all_data.append(json.load(file))
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with output_file.open('w') as outfile:
        json.dump(all_data, outfile, indent=4)
    
    print(f"Concatenation complete. Data written to '{output_file.name}'.")


def relationship_between_objects(solution, obj1, obj2, direction_constraints):
    for direction, constraint in direction_constraints.items():
        if constraint(solution[obj1], solution[obj2]):
            return direction  # Return the direction if the constraint is satisfied
    # return None  # Return None if no relationship is found

# Function to generate abbreviations
def generate_abbreviation(direction):
    # Split the direction into words and capitalize the first letter of each
    parts = direction.split('-')
    # Join the first character of each word
    abbreviation = ''.join(part[0].upper() for part in parts)
    return abbreviation


def number_to_word(number):
    p = inflect.engine()
    return p.number_to_words(number)

def build_asset_mapping(asset_database):
    """Create a mapping from assetId to objectType."""
    return {
        candidate['assetId']: object_type 
        for object_type, candidates in asset_database.items()
        for candidate in candidates
    }

def build_boundingBox_mapping(asset_database):
    """Create a mapping from assetId to objectType."""
    return {
        candidate['assetId']: candidate['boundingBox'] 
        for object_type, candidates in asset_database.items()
        for candidate in candidates
    }

def map_coordinates_to_position(coordinates):
    """Map coordinate values to descriptive wall positions."""
    x1, y1, x2, y2 = map(float, coordinates)
    
    if x1 < 0.01 and x2 < 0.01:
        position = 'west'
    elif x1 > 0.01 and x2 > 0.01:
        position = 'east'
    elif y1 < 0.01 and y2 < 0.01:
        position = 'south'
    elif y1 > 0.01 and y2 > 0.01:
        position = 'north'
    else:
        position = 'unspecified'
    return position


def get_room_segment(coordinate, room_dimension, segments):
    """
    Determine the segment of the room where the object is located.

    :param coordinate: Position coordinate of the object (x or y).
    :param room_dimension: Maximum dimension of the room.
    :param segments: List of segment labels.
    :return: Segment label where the object is located.
    """
    for i, segment in enumerate(segments):
        if coordinate <= (i + 1) * room_dimension / 3:
            return segment
    return ""


def get_room_connect(x, y, rx, ry, object_type, boundingBox, room_dimensions):
    # print(x, y, rx, ry, object_type, room_dimensions)
    # print(boundingBox)
    angel = rx+ry

    if angel == 90 or angel == 270:
        max_x = x + boundingBox['z']/2
        max_y = y + boundingBox['x']/2
        min_x = x - boundingBox['z']/2
        min_y = y - boundingBox['x']/2
    elif angel == 0 or angel == 180:
        max_x = x + boundingBox['x']/2
        max_y = y + boundingBox['z']/2
        min_x = x - boundingBox['x']/2
        min_y = y - boundingBox['z']/2    
    else:
        max_x = x + boundingBox['x']/2
        max_y = y + boundingBox['z']/2
        min_x = x - boundingBox['x']/2
        min_y = y - boundingBox['z']/2   
        
    # print (max_x, max_y, min_x, min_y)
    if abs(max_x-room_dimensions)<0.1:
        connect_x = 'east'
    elif abs(min_x) < 0.1:
        connect_x = 'west'
    else:
        connect_x = ''
        
    if abs(max_y-room_dimensions)<0.1:
        connect_y = 'north'
    elif abs(min_y) < 0.1:
        connect_y = 'south'
    else:
        connect_y = ''
    # print(connect_x, connect_y)
    if connect_x == '' and connect_y == '':
        return ''
    elif connect_x == '' or connect_y == '':
        return connect_x + connect_y
    else:
        return f"{connect_y} and {connect_x}"    


    
def describe_object_room(item, asset_mapping, room_dimensions, object_ids, object_counts, object_ids_up, object_counts_up):
    object_type = format_object_type(item.get('assetId'), asset_mapping)
    position = item.get('position', {})
    x, z, y = position.get('x', 0), position.get('y', 0), position.get('z', 0)

    # Calculate relative position
    x_segment = get_room_segment(x, room_dimensions, ['west', '', 'east'])
    y_segment = get_room_segment(y, room_dimensions, ['south', '', 'north'])
    spatial_description = f"{y_segment}-{x_segment}" if y_segment and x_segment else x_segment or y_segment or "center"
    spatial_fact = f"{y_segment[0].upper()}{x_segment[0].upper()}R" if y_segment and x_segment else x_segment or y_segment or "CR"
    if len(spatial_fact) > 3:
        spatial_fact = spatial_fact[0].upper() + 'R'
    description = ''
    
    
    # Generate the object name
    if object_counts[object_type] > 1:
    	update_object_counts(object_type, object_ids_up, object_counts_up) 
    	
    	object_name = f"{object_type} {object_counts_up[object_type]}"
    	if object_counts_up[object_type] == 1:
    	    #description = f"{object_counts[object_type] } {object_type}: "
    	    description = f"some {object_type}s: "
    	else:
    	    description = ''
    	pos_text = f"placed in the {spatial_description}" #at coordinate ({x}, {y}, {z})
    	description += f"{object_name} {pos_text}, "
    else:
        object_counts[object_type] = 1
        object_name = f"{object_type}"
        article = 'an' if object_type[0] in 'aeiou' else 'a'
        # article = 'one'
        pos_text = f"placed in the {spatial_description}" #at coordinate ({x}, {y}, {z})
        description += f"{article} {object_name} {pos_text}, "        
    fact = (object_name, spatial_fact, 'room')

    return description, fact


def describe_object_room_tpp(item, asset_mapping, boundingBox_mapping, room_dimensions, object_ids, object_counts, object_ids_up, object_counts_up):
    object_type = format_object_type(item.get('assetId'), asset_mapping)
    boundingBox = format_bounding_box(item.get('assetId'), boundingBox_mapping)
    position = item.get('position', {})
    x, z, y = position.get('x', 0), position.get('y', 0), position.get('z', 0)
    rotation = item.get('rotation', {})
    rx, ry, rz = rotation.get('x', 0), rotation.get('y', 0), rotation.get('z', 0)

    # Calculate relative position
    x_segment = get_room_segment(x, room_dimensions, ['west', '', 'east'])
    y_segment = get_room_segment(y, room_dimensions, ['south', '', 'north'])
    spatial_description = f"{y_segment}-{x_segment}" if y_segment and x_segment else x_segment or y_segment or "center"
    spatial_fact = f"{y_segment[0].upper()}{x_segment[0].upper()}R" if y_segment and x_segment else x_segment or y_segment or "CR"
    if len(spatial_fact) > 3:
        spatial_fact = spatial_fact[0].upper() + 'R'
        
    pure_object_description = ''
    description = ''
    description_tpp = ''
    # Calculate TPP/NTPP
    connect = get_room_connect(x, y, rx, ry, object_type, boundingBox, room_dimensions)
    if connect == '':
        tpp_text = 'away from walls' #, away from walls. without touching the walls
        tpp_fact = 'NTPP'
    else:
        tpp_text = 'against the wall'
        tpp_fact = 'TPP'
    

    
    # Generate the object name
    if object_counts[object_type] > 1:
    	update_object_counts(object_type, object_ids_up, object_counts_up) 
    	
    	object_name = f"{object_type} {object_counts_up[object_type]}"
    	if object_counts_up[object_type] == 1:
            pure_object_description = f"some {object_type}s: "
            description = f"some {object_type}s: "
    	    #description = f"{object_counts[object_type] } {object_type}: "
            if 'painting' in object_name: 
                description_tpp = f"some {object_type}s hanging on the wall: "
            else:
                description_tpp = f"some {object_type}s: "
    	else:
    	    description_tpp = ''
    	    description = ''
    	    pure_object_description = ''
            
    	pos_text = f"placed in the {spatial_description}" #at coordinate ({x}, {y}, {z})
    	description += f"{object_name} {pos_text}, "
    	pure_object_description += f"{object_name}, "
        
    	if 'painting' in object_name: 
            pos_text_tpp = f"in the {spatial_description} of the room" #at coordinate ({x}, {y}, {z})
            description_tpp += f"{object_name} {pos_text_tpp}, "
    	else:
            pos_text_tpp = f"placed in the {spatial_description}" #at coordinate ({x}, {y}, {z})
            description_tpp += f"{object_name} {pos_text_tpp}, {tpp_text}; "
    else:
        object_counts[object_type] = 1
        object_name = f"{object_type}"
        article = 'an' if object_type[0] in 'aeiou' else 'a'
        # article = 'one'
        
        pos_text = f"placed in the {spatial_description}" #at coordinate ({x}, {y}, {z})
        description += f"{article} {object_name} {pos_text}, "  
        pure_object_description += f"{article} {object_name}, " 
        
        if 'painting' in object_name: 
            pos_text_tpp = f"in the {spatial_description}"
            description_tpp += f"{article} {object_name} hanging on the wall, {pos_text_tpp} of the room; " 
        else:
            pos_text_tpp = f"placed in the {spatial_description}" #at coordinate ({x}, {y}, {z})
            description_tpp += f"{article} {object_name} {pos_text_tpp}, {tpp_text}; "        
    fact_direction = (object_name, spatial_fact, 'room')
    fact_object = (object_name, 'INR', 'room')
    fact_tpp = (object_name, tpp_fact, 'room')
    return pure_object_description, fact_object, description, fact_direction, description_tpp, fact_tpp, 



def describe_objects(objects, asset_mapping, boundingBox_mapping, room_dimensions):
    facts_object = []
    facts = []
    facts_tpp = []
    object_ids, object_counts = {}, {}  # Dictionary to store object counts
    object_ids_up, object_counts_up = {}, {}  # Dictionary to store object counts

    for obj in objects:
        # Count objects
        object_type = format_object_type(obj.get('assetId'), asset_mapping)
        if object_type in object_counts:
            update_object_counts(object_type, object_ids, object_counts)
        else:
            update_object_counts(object_type, object_ids, object_counts)
    
    summary_object_description = "This room contains a collection of furniture, including "
    summary_layout_description = "This room contains a collection of furniture, including "
    summary_layout_tpp_description = "This room contains a collection of furniture, including "
    
    for obj in objects:
        # Generate the detailed description for each object
        pure_object_description, fact_object, object_description, fact_direction, object_description_tpp, fact_tpp = describe_object_room_tpp(obj, asset_mapping, boundingBox_mapping, room_dimensions, object_ids, object_counts, object_ids_up, object_counts_up)
        
        summary_object_description = summary_object_description + pure_object_description
        summary_layout_description = summary_layout_description + object_description
        summary_layout_tpp_description = summary_layout_tpp_description + object_description_tpp
        
        facts_object.append(fact_object)      
        facts.append(fact_direction)
        facts_tpp.append(fact_tpp)
        
    summary_object_description = summary_object_description[:-2] +'.'
    summary_layout_description = summary_layout_description[:-2] +'.'
    summary_layout_tpp_description = summary_layout_tpp_description[:-2] +'.'
    
    last_comma_index = summary_object_description.rfind(',')
    if last_comma_index != -1:
        summary_object_description = summary_object_description[:last_comma_index + 1] + ' and' + summary_object_description[last_comma_index + 1:]
        
    return summary_object_description, facts_object, summary_layout_description, facts, summary_layout_tpp_description, facts_tpp



def describe_door(door, asset_mapping):
    # object_type = asset_mapping.get(door.get('assetId'), asset_mapping)
    id_parts = door.get('wall0').split('|')
    # position = door.get('assetPosition', {})
    if len(id_parts) >= 5:
        # Mapping the coordinate values to wall positions
        coordinates = id_parts[2:6]
        wall_position = map_coordinates_to_position(coordinates)
    pos_text = f"positioned along the {wall_position}-hand wall."
    return f"You'll find the door {pos_text}"

def describe_room(room):
    words = re.findall('[A-Z][a-z]*', room['roomType'])
    room_type = ' '.join(words).lower()
    return f"Imagine a square-shaped {room_type}, bordered by four walls."

def describe_wall(wall, asset_mapping):
    # Extracting wall details from the ID
    id_parts = wall['id'].split('|')
    if len(id_parts) >= 5:
        # Mapping the coordinate values to wall positions
        coordinates = id_parts[2:6]
        wall_position = map_coordinates_to_position(coordinates)
        wall_desc = f"A {wall_position} wall(ID: {wall['id']}) is present in the room."
    else:
        wall_desc = f"A wall (ID: {wall['id']}) is present in the scene."
    return wall_desc


def describe_window(window, asset_mapping):
    words = window['assetId'].split('_')[:-1]
    window_type = ' '.join(reversed(words)).lower()
    id_parts = window.get('wall0').split('|')
    # position = window.get('assetPosition', {})
    if len(id_parts) >= 5:
        # Mapping the coordinate values to wall positions
        coordinates = id_parts[2:6]
        wall_position = map_coordinates_to_position(coordinates)
    pos_text = f"on the {wall_position}-hand wall."
    return f"There is a {window_type} (Window {window['id'].split('|')[-1]}) located {pos_text}"


# Function to select combinations based on khop
def select_combinations(khop, object_list):
    # Dictionary to hold combinations of different levels
    all_combinations = {}
    
    # Create combinations for different k values
    for k in range(1, len(object_list) - 1):
        all_combinations[k] = [(object_list[i], object_list[i + k]) for i in range(len(object_list) - k)]

    if khop < len(object_list) - 1 or khop > len(object_list) * (len(object_list) - 1) // 2:
        raise ValueError("khop is out of the allowable range")

    selected_combinations = []
    cumulative_length = 0

    # Add combinations until we reach or exceed khop
    for k in range(1, len(object_list) - 1):
        next_combinations = all_combinations[k]
        if cumulative_length + len(next_combinations) < khop:
            selected_combinations.extend(next_combinations)
            cumulative_length += len(next_combinations)
        else:
            remaining_length = khop - cumulative_length
            selected_combinations.extend(next_combinations[:remaining_length])
            break

    return selected_combinations

def describe_two_objects_relations(objects, room_dimensions, asset_mapping, m):
    """Generate descriptions for spatial relations between every two objects."""
    descriptions, object_positions = {}, {}
    object_ids, object_counts = {}, {}
    facts =[]
    facts_d2 = []
    facts_d3 = []
    query = []
    
    for obj in objects:
        object_type = format_object_type(obj.get('assetId'), asset_mapping)
        object_counts[object_type] = object_counts.get(object_type, 0) + 1
            
    for obj in objects:
        object_type = format_object_type(obj.get('assetId'), asset_mapping)
        if object_counts[object_type] > 1:
            object_ids[object_type] = object_ids.get(object_type, 0) + 1
            object_name = f"{object_type} {object_ids[object_type]}"
        else:
            object_name = f"the {object_type}"

        position = tuple(obj.get('position', {}).values())
        object_positions[object_name] = position

    relation_descriptions_sd = {}
    relation_descriptions_td = {}
    relation_descriptions_sd_d = {}
    relation_descriptions_td_d = {}
    
    
    # Randomly choose a pair for the question if there are at least two objects
    object_items = list(object_positions.items())
    
    if len(object_items) > 1:
        obj1 = object_items[0]
        obj2 = object_items[-1]
        
        question_fact = symbol_spatial_relationship(obj1[1], obj2[1])
        answer_fr_config_sd = answer_spatial_relationship_sd(obj1[1], obj2[1])
        answer_fr_config_td = analyze_spatial_relationship_td(obj1[1], obj2[1])     

    khop = m

    all_combinations = [((obj_name1, pos1), (obj_name2, pos2)) 
                        for i, (obj_name1, pos1) in enumerate(object_positions.items())
                        for j, (obj_name2, pos2) in enumerate(object_positions.items())
                        if i < j and not ((obj_name1 == obj1[0] and obj_name2 == obj2[0]) or (obj_name1 == obj2[0] and obj_name2 == obj1[0]))]


    # Randomly select khop number of combinations
    # selected_combinations = random.sample(all_combinations, khop)
    
    # Convert the dictionary to a list of tuples
    object_list = list(object_positions.items())
    
    # Create the consecutive pairings
    initial_combinations = [(object_list[i], object_list[i+1]) for i in range(len(object_list)-1)]
    
    # if khop == len(initial_combinations):
    #     selected_combinations = initial_combinations    
    selected_combinations = select_combinations(khop, object_list)
    # print(selected_combinations)
    
    for i in range(len(selected_combinations)):
        (obj_name1, pos1), (obj_name2, pos2) = selected_combinations[i]

        relation_facts = symbol_spatial_relationship(pos1, pos2)

        
        #sd
        relation_sd = analyze_spatial_relationship_sd(pos1, pos2)
        key_sd = (obj_name1, relation_sd, relation_facts)
        if key_sd not in relation_descriptions_sd:
            relation_descriptions_sd[key_sd] = []
        relation_descriptions_sd[key_sd].append(obj_name2)
        
        #td
        relation_td = analyze_spatial_relationship_td(pos1, pos2)
        key_td = (obj_name1, relation_td, relation_facts)
        if key_td not in relation_descriptions_td:
            relation_descriptions_td[key_td] = []
        relation_descriptions_td[key_td].append(obj_name2)                    

        #sd_d
        distance_3_relation_sd, distance_3_fact= get_distance_relation_3_sd(pos1, pos2, room_dimensions)  
        distance_2_relation_sd, distance_2_fact = get_distance_relation_2_sd(pos1, pos2, room_dimensions) 
        relation_sd = analyze_spatial_relationship_sd(pos1, pos2)
        key_sd_d = (obj_name1, relation_sd, distance_3_relation_sd, distance_2_relation_sd, relation_facts, distance_3_fact, distance_2_fact)
        if key_sd_d not in relation_descriptions_sd_d:
            relation_descriptions_sd_d[key_sd_d] = []
        relation_descriptions_sd_d[key_sd_d].append(obj_name2)

        #td_d
        distance_3_relation, distance_3_fact= get_distance_relation_3(pos1, pos2, room_dimensions)  
        distance_2_relation, distance_2_fact = get_distance_relation_2(pos1, pos2, room_dimensions) 
        relation_sd = analyze_spatial_relationship_sd(pos1, pos2)
        key_td_d = (obj_name1, relation_td, distance_3_relation, distance_2_relation, relation_facts, distance_3_fact, distance_2_fact)
        if key_td_d not in relation_descriptions_td_d:
            relation_descriptions_td_d[key_td_d] = []
        relation_descriptions_td_d[key_td_d].append(obj_name2)                    
                    
    
    # generate objects relations -- south door
    relation_description_all_sd = "Imagine yourself at the southern wall's door, looking inwards. From this perspective,"
    i = 0
    for (obj_name1, relation_sd, relation_facts), obj_names2 in relation_descriptions_sd.items():
        for obj_names2_each in obj_names2:
            facts.append((obj_name1.replace('the ', ''), relation_facts, obj_names2_each.replace('the ', '')))
        # obj_list = " and the ".join(obj_names2)
        obj_list = " and ".join(obj_names2)
        relation_description = f"{obj_name1} is {relation_sd} {obj_list}."
        if i == 0:
            relation_description_all_sd = relation_description_all_sd + ' ' + relation_description
        else:
            relation_description_all_sd = relation_description_all_sd + ' ' + relation_description[0].upper() + relation_description[1:]   
        i += 1
    
    # generate objects relations -- top down
    relation_description_all_td = "" 
    i = 0
    for (obj_name1, relation_td, relation_facts), obj_names2 in relation_descriptions_td.items():
        # obj_list = " and the ".join(obj_names2)
        obj_list = " and ".join(obj_names2)
        relation_description = f"{obj_name1} is placed to the {relation_td} of {obj_list}."
        if i == 0:
            relation_description_all_td = relation_description[0].upper() + relation_description[1:]   
        else:
            relation_description_all_td = relation_description_all_td + ' ' + relation_description[0].upper() + relation_description[1:]   
        i += 1
        
    # generate objects relations -- south door + distance
    relation_description_all_sd_d2 = "Imagine yourself at the southern wall's door, looking inwards. From this perspective,"
    relation_description_all_sd_d3 = "Imagine yourself at the southern wall's door, looking inwards. From this perspective,"
    i = 0
    for (obj_name1, relation_sd_d, distance_3_relation_sd, distance_2_relation_sd, relation_facts, distance_3_fact, distance_2_fact), obj_names2 in relation_descriptions_sd_d.items():
        for obj_names2_each in obj_names2:
            facts_d2.append((obj_name1.replace('the ', ''), distance_2_fact, obj_names2_each.replace('the ', '')))
            facts_d3.append((obj_name1.replace('the ', ''), distance_3_fact, obj_names2_each.replace('the ', '')))
            
        # obj_list = " and the ".join(obj_names2)
        obj_list = " and ".join(obj_names2)
        relation_d2_description = f"{obj_name1} is {relation_sd_d} {obj_list}, {distance_2_relation_sd}."
        relation_d3_description = f"{obj_name1} is {relation_sd_d} {obj_list}, {distance_3_relation_sd}."
        if i == 0:
            relation_description_all_sd_d2 = relation_description_all_sd_d2 + ' ' + relation_d2_description
            relation_description_all_sd_d3 = relation_description_all_sd_d3 + ' ' + relation_d3_description
        else:
            relation_description_all_sd_d2 = relation_description_all_sd_d2 + ' ' + relation_d2_description[0].upper() + relation_d2_description[1:]   
            relation_description_all_sd_d3 = relation_description_all_sd_d3 + ' ' + relation_d3_description[0].upper() + relation_d3_description[1:]   
        i += 1
    
    # generate objects relations -- top down + distance
    relation_description_all_td_d2 = ""
    relation_description_all_td_d3 = ""
    i = 0
    for (obj_name1, relation_td_d, distance_3_relation, distance_2_relation, relation_facts, distance_3_fact, distance_2_fact), obj_names2 in relation_descriptions_td_d.items():
        # obj_list = " and the ".join(obj_names2)
        obj_list = " and ".join(obj_names2)
        relation_d2_description = f"{obj_name1} is placed to the {relation_td_d} of {obj_list}, {distance_2_relation}."
        relation_d3_description = f"{obj_name1} is placed to the {relation_td_d} of {obj_list}, {distance_3_relation}."
        if i == 0:
            relation_description_all_td_d2 = relation_d2_description[0].upper() + relation_d2_description[1:]   
            relation_description_all_td_d3 = relation_d3_description[0].upper() + relation_d3_description[1:]   
        
        else:
            relation_description_all_td_d2 = relation_description_all_td_d2 + ' ' + relation_d2_description[0].upper() + relation_d2_description[1:]   
            relation_description_all_td_d3 = relation_description_all_td_d3 + ' ' + relation_d3_description[0].upper() + relation_d3_description[1:]   
        i += 1
        
          
    descriptions['objects_td'] = relation_description_all_td      
    descriptions['objects_sd'] = relation_description_all_sd
    
    descriptions['objects_td_d2'] = relation_description_all_td_d2 
    descriptions['objects_sd_d2'] = relation_description_all_sd_d2    
    descriptions['objects_td_d3'] = relation_description_all_td_d3      
    descriptions['objects_sd_d3'] = relation_description_all_sd_d3  
    
    descriptions['image_fr_o2_sd'] = answer_fr_config_sd
    descriptions['image_fr_o2_td'] = answer_fr_config_td
    
    
    query.append((obj1[0].replace('the ', ''), question_fact, obj2[0].replace('the ', '')))
    
    return descriptions, facts, facts_d2, facts_d3, query 

# Helper functions
def format_object_type(asset_id, asset_mapping):
    """Format object type from assetId."""
    exceptions = {'tvstand': 'TV stand', 'cd': 'CD', 'tabletopdecor': 'tabletop decor'}  # Add more exceptions if needed

    object_type = asset_mapping.get(asset_id, asset_id)

    # Check if object_type is in exceptions
    if object_type.lower() in exceptions:
        return exceptions[object_type.lower()]
    else:
        # Split object_type using regular expressions and add spaces
        words = re.findall('[A-Z][a-z]*', object_type)
        return ' '.join(words).lower()
    
def format_bounding_box(asset_id, boundingBox_mapping):
    """Format object type from assetId."""

    boundingBox = boundingBox_mapping.get(asset_id, boundingBox_mapping)
    return boundingBox
    

def update_object_counts(object_type, object_ids, object_counts):
    """Update counts of objects."""
    if object_type in object_ids:
        object_ids[object_type] += 1
    else:
        object_ids[object_type] = 1
    if object_type in object_counts:
        object_counts[object_type] += 1
    else:
        object_counts[object_type] = 1

def abbreviate_direction(direction):
    # Split the direction string by hyphens
    parts = direction.split('-')
    # Take the first letter of each part, convert to uppercase, and join them
    abbreviation = ''.join(part[0].upper() for part in parts)
    return abbreviation

def analyze_spatial_relationship_sd(pos1, pos2):
    """
    For generating stor
    """
    x1, y1, z1 = pos1
    x2, y2, z2 = pos2

    horizontal_relation = ""
    if x1 < x2:
        horizontal_relation = "to the left of"
    elif x1 > x2:
        horizontal_relation = "to the right of"

    vertical_relation = ""
    if z1 < z2:
        vertical_relation = "behind"
    elif z1 > z2:
        vertical_relation = "in front of" #"front" typically refers to the direction you are facing

    if horizontal_relation and vertical_relation:
        return f"{vertical_relation} and {horizontal_relation}"
    elif horizontal_relation or vertical_relation:
        return horizontal_relation if horizontal_relation else vertical_relation
    else:
        return "at the same position"
    
def analyze_spatial_relationship_td(pos1, pos2):
    """
    For generating stor
    """
    x1, y1, z1 = pos1
    x2, y2, z2 = pos2

    horizontal_relation = ""
    if x1 < x2:
        horizontal_relation = "west"
    elif x1 > x2:
        horizontal_relation = "east"

    vertical_relation = ""
    if z1 < z2:
        vertical_relation = "south"
    elif z1 > z2:
        vertical_relation = "north" #"front" typically refers to the direction you are facing

    if horizontal_relation and vertical_relation:
        return f"{vertical_relation}-{horizontal_relation}"
    elif horizontal_relation or vertical_relation:
        return horizontal_relation if horizontal_relation else vertical_relation
    else:
        return "at the same position"


def answer_spatial_relationship_sd(pos1, pos2):
    """
    For generating stor
    """
    x1, y1, z1 = pos1
    x2, y2, z2 = pos2

    horizontal_relation = ""
    if x1 < x2:
        horizontal_relation = "left"
    elif x1 > x2:
        horizontal_relation = "right"

    vertical_relation = ""
    if z1 < z2:
        vertical_relation = "behind"
    elif z1 > z2:
        vertical_relation = "front" #"front" typically refers to the direction you are facing

    if horizontal_relation and vertical_relation:
        return f"{vertical_relation}-{horizontal_relation}"
    elif horizontal_relation or vertical_relation:
        return horizontal_relation if horizontal_relation else vertical_relation
    else:
        return "at the same position"


def get_distance_relation_3(pos1, pos2, room_dimensions):
    # Calculate Euclidean distance between two objects
    x1, _, z1 = pos1
    x2, _, z2 = pos2

    # Calculate Euclidean distance between two objects on the x-z plane
    distance = ((x1 - x2)**2 + (z1 - z2)**2)**0.5

    # Max distance as the diagonal of the room on the x-z plane
    max_distance = (room_dimensions**2 + room_dimensions**2)**0.5
    # max_distance = room_dimensions

    # Determine the thresholds for 'close', 'medium', and 'far'
    close_threshold = max_distance / 3
    medium_threshold = 2 * max_distance / 3

    if distance <= close_threshold:
        return "at a short distance", "CL3"  #, at a short distance , closely situated  , very close  , nearby
    elif close_threshold < distance <= medium_threshold:
        return "at a moderate distance", "MD3"
    elif distance > medium_threshold:
        # print(distance, close_threshold, medium_threshold)
        return "at a far distance", "FR3"


def get_distance_relation_2(pos1, pos2, room_dimensions):
    # Calculate Euclidean distance between two objects
    x1, _, z1 = pos1
    x2, _, z2 = pos2

    # Calculate Euclidean distance between two objects on the x-z plane
    distance = ((x1 - x2)**2 + (z1 - z2)**2)**0.5

    # Max distance as the diagonal of the room on the x-z plane
    # max_distance = (room_dimensions**2 + room_dimensions**2)**0.5
    max_distance = room_dimensions

    # Determine the thresholds for 'close', 'medium', and 'far'
    close_threshold = max_distance / 2

    # Determine the distance relation
    if distance < close_threshold:
        return "at a short distance", "CL2"  #, at a short distance , closely situated  , very close  , nearby
    elif distance >= close_threshold:
        return "at a far distance", "FR2" # , at a far distance.
    



def get_distance_relation_3_sd(pos1, pos2, room_dimensions):
    # Calculate Euclidean distance between two objects
    x1, _, z1 = pos1
    x2, _, z2 = pos2

    # Calculate Euclidean distance between two objects on the x-z plane
    distance = ((x1 - x2)**2 + (z1 - z2)**2)**0.5

    # Max distance as the diagonal of the room on the x-z plane
    max_distance = (room_dimensions**2 + room_dimensions**2)**0.5
    # max_distance = room_dimensions

    # Determine the thresholds for 'close', 'medium', and 'far'
    close_threshold = max_distance / 3
    medium_threshold = 2 * max_distance / 3

    # Determine the distance relation
    if distance <= close_threshold:
        return "at a short distance", "CL3"  #, at a short distance , closely situated  , very close  , nearby
    elif close_threshold < distance <= medium_threshold:
        return "at a moderate distance", "MD3"
    elif distance > medium_threshold:
        return "at a far distance", "FR3"

def get_distance_relation_2_sd(pos1, pos2, room_dimensions):
    # Calculate Euclidean distance between two objects
    x1, _, z1 = pos1
    x2, _, z2 = pos2

    # Calculate Euclidean distance between two objects on the x-z plane
    distance = ((x1 - x2)**2 + (z1 - z2)**2)**0.5

    # Max distance as the diagonal of the room on the x-z plane
    # max_distance = (room_dimensions**2 + room_dimensions**2)**0.5
    max_distance = room_dimensions

    # Determine the thresholds for 'close', 'medium', and 'far'
    close_threshold = max_distance / 2

    # Determine the distance relation
    if distance <= close_threshold:
        # print('short')
        return "at a short distance", "CL2"  #, at a short distance , closely situated  , very close  , nearby
    elif distance > close_threshold:
        return "at a far distance", "FR2" # , at a far distance.
    

def symbol_spatial_relationship(pos1, pos2):
    """
    For generating stor
    """
    x1, y1, z1 = pos1
    x2, y2, z2 = pos2

    horizontal_relation = ""
    if x1 < x2:
        horizontal_relation = "W"
    elif x1 > x2:
        horizontal_relation = "E"

    vertical_relation = ""
    if z1 < z2:
        vertical_relation = "S"
    elif z1 > z2:
        vertical_relation = "N" #"front" typically refers to the direction you are facing

    if horizontal_relation and vertical_relation:
        return f"{vertical_relation}{horizontal_relation}"
    elif horizontal_relation or vertical_relation:
        return horizontal_relation if horizontal_relation else vertical_relation
    else:
        return "O"
    

def generate_example_descriptions(example, asset_mapping, boundingBox_mapping, n, m):
    """Generate descriptions for all components in an example, including spatial relations between objects."""
    descriptions = {}
    facts_object = []
    facts_layout = []
    facts_o2= []
    facts_tpp = []
    facts_d2 = []
    facts_d3 = []

    # Describe rooms, doors, walls, and windows
    for room in example.get('rooms', []):
        descriptions['room'] = describe_room(room)

    # Extract maximum dimensions for the room
    parts = example.get('doors', [])[0]["wall0"].split('|')
    room_dimensions = max([float(part) for part in parts[-4:]])

    # Describe objects
    objects_all = example.get('objects', [])
    objects = []
    object_ids, object_counts = {}, {}  # Dictionary to store object counts
    
    for obj in objects_all:
        # Count objects
        object_type = format_object_type(obj.get('assetId'), asset_mapping)
        if object_type in object_counts:
            update_object_counts(object_type, object_ids, object_counts)
        else:
            update_object_counts(object_type, object_ids, object_counts)
    
    objects_all.sort(key=lambda obj: object_counts[format_object_type(obj.get('assetId'), asset_mapping)])

    if len(objects_all) >= n:
        # objects = random.sample(objects_all, n)
        objects = objects_all[:n]
        objects.sort(key=lambda obj: object_counts[format_object_type(obj.get('assetId'), asset_mapping)])
        object_descriptions, object_facts, object_room_relations_descriptions, object_room_facts, object_room_relations_descriptions_tpp, object_room_facts_tpp = describe_objects(objects, asset_mapping, boundingBox_mapping, room_dimensions)
        facts_object.extend(object_facts)
        facts_layout.extend(object_room_facts)
        facts_tpp.extend(object_room_facts_tpp)

        descriptions['object'] = object_descriptions
        descriptions['object_room'] = object_room_relations_descriptions
        descriptions['object_room_tpp'] = object_room_relations_descriptions_tpp
        objects_relations_descriptions, objects_facts, objects_facts_d2, objects_facts_d3, query = describe_two_objects_relations(objects, room_dimensions, asset_mapping, m)
        descriptions.update(objects_relations_descriptions)

        facts_o2.extend(objects_facts)
        facts_d2.extend(objects_facts_d2)
        facts_d3.extend(objects_facts_d3)   
        
        return descriptions, facts_object, facts_layout, facts_tpp, facts_o2, facts_d2, facts_d3, query

    else:      
        return '', '', '', '', '', '', '', ''
    

def generate_descriptions_facts(data, asset_mapping, boundingBox_mapping, n, m, test_num, test_num_start, k_start, domain_size):
    """Generate descriptions for all examples in '.json', excluding those with empty descriptions."""
    descriptions_list = []
    facts_list = []
    times = {}
    times_yn = {}
    answers_length = {}
    skip_id_list = []
    solution_id_list = []
    
    conversion_dict_sd = {
    'N': 'front',
    'S': 'behind',
    'E': 'right',
    'W': 'left',
    'O': 'overlap'
    }
    
    conversion_dict_td = {
    'N': 'north',
    'S': 'south',
    'E': 'east',
    'W': 'west',
    'O': 'overlap'
    }
    
    ful_k = k_start
    
    for i, example in enumerate(data['example'][test_num_start:], start=test_num_start):
        restory = True
        ful_k = ful_k + 1

        descriptions, facts_object, facts_layout, facts_tpp, facts_o2, facts_d2, facts_d3, query = generate_example_descriptions(example, asset_mapping, boundingBox_mapping, n, m)
        
        if not descriptions:
            skip_id_list.append(i)
            print('skip:', i)
            if ful_k == test_num:
                return descriptions_list, facts_list, answers_length, times, times_yn, skip_id_list, solution_id_list
            continue
        
        test_layout = {
            'example_id': i,
            'facts': facts_object + facts_layout,
            'query': query,
        }
        test_layout_tpp = {
            'example_id': i,
            'facts':  facts_object + facts_layout + facts_tpp,
            'query': query, 
        }
        test_o2 = {
            'example_id': i,
            'facts': facts_object + facts_o2,
            'query': query,
        }
        test_o2_d2 = {
            'example_id': i,
            'facts': facts_object + facts_o2 + facts_d2,
            'query': query, 
        }
        test_o2_d3 = {
            'example_id': i,
            'facts': facts_object + facts_o2 + facts_d3,
            'query': query, 
        }            
        test_layout_o2  = {
            'example_id': i,
            'facts': facts_object  +  facts_layout + facts_o2,
            'query': query, 
        }         
        test_layout_o2_d2 = {
            'example_id': i,
            'facts': facts_object  + facts_layout + facts_o2 + facts_d2,
            'query': query, 
        }
        test_layout_o2_d3 = {
            'example_id': i,
            'facts': facts_object  + facts_layout + facts_o2 + facts_d3,
            'query': query, 
        }  
        
        result_layout, time_layout = solve_all_candidates(test_layout, domain_size)
        result_layout_tpp, time_layout_tpp = solve_all_candidates(test_layout_tpp, domain_size)
        result_o2, time_o2 = solve_all_candidates(test_o2, domain_size)
        result_o2_d2, time_o2_d2 = solve_all_candidates(test_o2_d2, domain_size)
        result_o2_d3, time_o2_d3 = solve_all_candidates(test_o2_d3, domain_size)   
        result_layout_o2, time_layout_o2 = solve_all_candidates(test_layout_o2, domain_size)
        result_layout_o2_d2, time_layout_o2_d2 = solve_all_candidates(test_layout_o2_d2, domain_size)
        result_layout_o2_d3, time_layout_o2_d3 = solve_all_candidates(test_layout_o2_d3, domain_size)               
        
        print(len(result_layout), len(result_layout_tpp), len(result_o2), len(result_o2_d2), len(result_o2_d3), len(result_layout_o2), len(result_layout_o2_d2), len(result_layout_o2_d3))

        if len(result_layout) > 0 and len(result_layout_tpp) > 0 and len(result_o2) > 0  and len(result_o2_d2) > 0 and len(result_o2_d3) > 0 and len(result_layout_o2) > 0 and len(result_layout_o2_d2) > 0 and len(result_layout_o2_d3) > 0:                
            restory = False

        if descriptions and restory == False:  
            solution_id_list.append(i)
        if descriptions:  # Check if descriptions is not empty
            answers_length[i] = [len(result_layout), len(result_layout_tpp),len(result_o2), len(result_o2_d2),len(result_o2_d3), len(result_layout_o2), len(result_layout_o2_d2),len(result_layout_o2_d3)]
            times[i] = [time_layout, time_layout_tpp, time_o2, time_o2_d2, time_o2_d3, time_layout_o2, time_layout_o2_d2, time_layout_o2_d3]            
            
            relation_candidates =['north', 'south', 'east', 'west','north-west', 'north-east', 'south-west', 'south-east']
            results_list_layout = []
            if len(result_o2) > 0:
                for k in result_layout:
                    if len(k) == 1:
                        results_list_layout.append(conversion_dict_td[k])
                    else:
                        results_list_layout.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
            descriptions['question_fr'] = f"Where is the {query[0][0]} positioned in relation to the {query[0][2]}?"                
            descriptions['solver_fr_layout'] = results_list_layout
                    
            results_list_layout_tpp = []        
            if len(result_layout_tpp) > 0:
                for k in result_layout_tpp:
                    if len(k) == 1:
                        results_list_layout_tpp.append(conversion_dict_td[k])
                    else:
                        results_list_layout_tpp.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
            descriptions['solver_fr_layout_tpp'] = results_list_layout_tpp 
            
            # for comparing top-down view and south-door view
            results_list_o2_td = []
            results_list_o2_sd = []
            if len(result_o2) > 0:
                for k in result_o2:
                    if len(k) == 1:
                        results_list_o2_td.append(conversion_dict_td[k])
                        results_list_o2_sd.append(conversion_dict_sd[k])
                    else:
                        results_list_o2_td.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
                        results_list_o2_sd.append(f"{conversion_dict_sd[k[0]]}-{conversion_dict_sd[k[1]]}")
            descriptions['solver_fr_o2_td'] = results_list_o2_td  
            descriptions['solver_fr_o2_sd'] = results_list_o2_sd
            
            results_list_o2_d2 = []
            results_list_o2_d2_sd = []
            if len(result_o2_d2) > 0:
                for k in result_o2_d2:
                    if len(k) == 1:
                        results_list_o2_d2.append(conversion_dict_td[k])
                        results_list_o2_d2_sd.append(conversion_dict_sd[k])
                    else:
                        results_list_o2_d2.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
                        results_list_o2_d2_sd.append(f"{conversion_dict_sd[k[0]]}-{conversion_dict_sd[k[1]]}")
            descriptions['solver_fr_o2_d2'] = results_list_o2_d2
            descriptions['solver_fr_o2_d2_sd'] = results_list_o2_d2_sd
            
            
            results_list_o2_d3 = []
            results_list_o2_d3_sd = []
            if len(result_o2_d3) > 0:
                for k in result_o2_d3:
                    if len(k) == 1:
                        results_list_o2_d3.append(conversion_dict_td[k])
                        results_list_o2_d3_sd.append(conversion_dict_sd[k])
                    else:
                        results_list_o2_d3.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
                        results_list_o2_d3_sd.append(f"{conversion_dict_sd[k[0]]}-{conversion_dict_sd[k[1]]}")
            descriptions['solver_fr_o2_d3'] = results_list_o2_d3
            descriptions['solver_fr_o2_d3_sd'] = results_list_o2_d3_sd
            
            
            # for comparing o2 without and with layout descriptions
            results_list_layout_o2=[]
            results_list_layout_o2_sd=[]
            if len(result_layout_o2) > 0:
                for k in result_layout_o2:
                    if len(k) == 1:
                        results_list_layout_o2.append(conversion_dict_td[k])
                        results_list_layout_o2_sd.append(conversion_dict_sd[k])
                    else:
                        results_list_layout_o2.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
                        results_list_layout_o2_sd.append(f"{conversion_dict_sd[k[0]]}-{conversion_dict_sd[k[1]]}")
            descriptions['solver_fr_layout_o2'] = results_list_layout_o2
            descriptions['solver_fr_layout_o2_sd'] = results_list_layout_o2_sd


            results_list_layout_o2_d2 = []
            results_list_layout_o2_d2_sd = []
            if len(result_layout_o2_d2) > 0:
                for k in result_layout_o2_d2:
                    if len(k) == 1:
                        results_list_layout_o2_d2.append(conversion_dict_td[k])
                        results_list_layout_o2_d2_sd.append(conversion_dict_sd[k])
                    else:
                        results_list_layout_o2_d2.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
                        results_list_layout_o2_d2_sd.append(f"{conversion_dict_sd[k[0]]}-{conversion_dict_sd[k[1]]}")
            descriptions['solver_fr_layout_o2_d2'] = results_list_layout_o2_d2
            descriptions['solver_fr_layout_o2_d2_sd'] = results_list_layout_o2_d2_sd


            results_list_layout_o2_d3 = []
            results_list_layout_o2_d3_sd = []
            if len(result_layout_o2_d3) > 0:
                for k in result_layout_o2_d3:
                    if len(k) == 1:
                        results_list_layout_o2_d3.append(conversion_dict_td[k])
                        results_list_layout_o2_d3_sd.append(conversion_dict_sd[k])
                    else:
                        results_list_layout_o2_d3.append(f"{conversion_dict_td[k[0]]}-{conversion_dict_td[k[1]]}")
                        results_list_layout_o2_d3_sd.append(f"{conversion_dict_sd[k[0]]}-{conversion_dict_sd[k[1]]}")
            descriptions['solver_fr_layout_o2_d3'] = results_list_layout_o2_d3
            descriptions['solver_fr_layout_o2_d3_sd'] = results_list_layout_o2_d3_sd


            replacements = {
                'north-east': 'in front of and to the right of',
                'east': 'to the right of',
                'west': 'to the left of',
                'north-west': 'in front of and to the left of',
                'south-east': 'behind and to the right of',
                'south-west': 'behind and to the left of',
                'north': 'in front of',
                'south': 'behind'
            }
            
            relation_uni = random.sample(relation_candidates, k =1)[0]
            descriptions['question_yn_uni'] = f"Could the {query[0][0]} be placed to the {relation_uni} of the {query[0][2]}?" if relation_uni != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"               
            descriptions['question_yn_uni_sd'] = f"Could the {query[0][0]} be positioned {replacements[relation_uni]} of the {query[0][2]}?" if relation_uni != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"               
            descriptions['answer_yn_uni_layout'] = "Yes" if relation_uni in  results_list_layout else "No"
            descriptions['answer_yn_uni_layout_tpp'] = "Yes" if relation_uni in  results_list_layout_tpp else "No"
            descriptions['answer_yn_uni_o2_td'] = "Yes" if relation_uni in  results_list_o2_td else "No"
            descriptions['answer_yn_uni_o2_d2'] = "Yes" if relation_uni in  results_list_o2_d2 else "No"
            descriptions['answer_yn_uni_o2_d3'] = "Yes" if relation_uni in  results_list_o2_d3 else "No"
            descriptions['answer_yn_uni_layout_o2_td'] = "Yes" if relation_uni in  results_list_layout_o2 else "No"
            descriptions['answer_yn_uni_layout_o2_d2'] = "Yes" if relation_uni in  results_list_layout_o2_d2 else "No"
            descriptions['answer_yn_uni_layout_o2_d3'] = "Yes" if relation_uni in  results_list_layout_o2_d3 else "No"

            query_yn_uni_logic = [(query[0][0], abbreviate_direction(relation_uni) ,query[0][2])]
 
            _, time_layout_yn = solve_single_candidate(test_layout, relation_uni, domain_size)
            _, time_layout_tpp_yn = solve_single_candidate(test_layout_tpp, relation_uni, domain_size)
            _, time_o2_yn = solve_single_candidate(test_o2, relation_uni, domain_size)
            _, time_o2_d2_yn = solve_single_candidate(test_o2_d2, relation_uni, domain_size)
            _, time_o2_d3_yn = solve_single_candidate(test_o2_d3, relation_uni, domain_size)   
            _, time_layout_o2_yn = solve_single_candidate(test_layout_o2, relation_uni, domain_size)
            _, time_layout_o2_d2_yn = solve_single_candidate(test_layout_o2_d2, relation_uni, domain_size)
            _, time_layout_o2_d3_yn = solve_single_candidate(test_layout_o2_d3, relation_uni, domain_size)   

            times_yn[i] = [time_layout_yn, time_layout_tpp_yn, time_o2_yn, time_o2_d2_yn, time_o2_d3_yn, time_layout_o2_yn, time_layout_o2_d2_yn, time_layout_o2_d3_yn]            


            # for comparing wether can take full use of tpp
            if len(results_list_layout_tpp) != len(results_list_layout) and len(results_list_layout_tpp) > 0:
                answer_ = 'Yes' if len(results_list_layout) == 9 else random.sample(['Yes', 'No'], k =1)[0]
                if answer_ == 'Yes':
                    relation_ =  random.sample(results_list_layout, k =1)
                else:
                    filtered_candidates = [item for item in relation_candidates if item not in results_list_layout]
                    relation_ =  random.sample(filtered_candidates, k =1)
                descriptions['question_yn_layout'] = f"Could the {query[0][0]} be placed to the {relation_[0]} of the {query[0][2]}?"  if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                               
                descriptions['answer_yn_layout'] = answer_
                descriptions['answer_yn_layout_tpp'] = "Yes" if relation_[0] in results_list_layout_tpp else "No"                                

            # for comparing distance info with pure o2
            if len(results_list_o2_d2) != len(results_list_o2_td) and len(results_list_o2_d2) > 0:
                answer_ = random.sample(['Yes', 'No'], k =1)[0]
                if answer_ == 'Yes':
                    relation_ =  random.sample(results_list_o2_d2, k =1)
                else:
                    unique_elements_list = [item for item in results_list_o2_td if item not in results_list_o2_d2]
                    relation_ =  random.sample(unique_elements_list, k =1)
                relation_sd = relation_[0].replace('north','in front of').replace('south','behind').replace('east','to the right of').replace('west','to the left of').replace('-', ' and ')
                descriptions['question_use_d2'] = f"Could the {query[0][0]} be placed to the {relation_[0]} of the {query[0][2]}?" if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                              
                descriptions['question_use_d2_sd'] = f"Could the {query[0][0]} be placed {relation_sd} the {query[0][2]}?" if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                                
                descriptions['answer_use_d2'] = answer_
                descriptions['answer_use_d2_sd'] = answer_
                descriptions['answer_without_use_d2'] = "Yes" if relation_[0] in results_list_o2_td else "No"
                descriptions['answer_without_use_d2_sd'] = "Yes" if relation_[0] in results_list_o2_td else "No"
                
            # for comparing distance info with pure o3
            if len(results_list_o2_d3) != len(results_list_o2_td) and len(results_list_o2_d3) > 0:
                answer_ = random.sample(['Yes', 'No'], k =1)[0]
                if answer_ == 'Yes':
                    relation_ =  random.sample(results_list_o2_d3, k =1)
                else:
                    unique_elements_list = list( set(results_list_o2_td) - set(results_list_o2_d3))
                    relation_ =  random.sample(unique_elements_list, k =1)
                relation_sd = relation_[0].replace('north','in front of').replace('south','behind').replace('east','to the right of').replace('west','to the left of').replace('-', ' and ')
                descriptions['question_use_d3'] = f"Could the {query[0][0]} be placed to the {relation_[0]} of the {query[0][2]}?"   if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                             
                descriptions['question_use_d3_sd'] = f"Could the {query[0][0]} be placed {relation_sd} the {query[0][2]}?"  if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                                
                descriptions['answer_use_d3'] = answer_
                descriptions['answer_use_d3_sd'] = answer_
                descriptions['answer_without_use_d3'] = "Yes" if relation_[0] in results_list_o2_td else "No"
                descriptions['answer_without_use_d3_sd'] = "Yes" if relation_[0] in results_list_o2_td else "No"
        
            # for comparing wether can take full use of layout and o2
            if Counter(results_list_layout_o2) != Counter(results_list_layout) and Counter(results_list_layout_o2) != Counter(results_list_o2_td)  and len(results_list_layout_o2) > 0:
                answer_ = random.sample(['Yes', 'No'], k =1)[0]
                if answer_ == 'Yes':
                    relation_ =  random.sample(results_list_layout_o2, k =1)
                else:
                    unique_elements_list = list((set(results_list_layout) | set(results_list_o2_td)) - set(results_list_layout_o2))
                    relation_ =  random.sample(unique_elements_list, k =1) 
                relation_sd = relation_[0].replace('north','in front of').replace('south','behind').replace('east','to the right of').replace('west','to the left of').replace('-', ' and ')
                descriptions['question_use_layout_o2'] = f"Could the {query[0][0]} be placed to the {relation_[0]} of the {query[0][2]}?" if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"               
                descriptions['question_use_layout_o2_sd'] = f"Could the {query[0][0]} be placed {relation_sd} the {query[0][2]}?" if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                              
                descriptions['answer_use_layout_o2'] = answer_ 
                descriptions['answer_use_layout_o2_sd'] = answer_ 
                descriptions['answer_with_layout_without_o2'] =  "Yes" if relation_[0] in results_list_layout else "No"
                descriptions['answer_with_layout_without_o2_sd'] = "Yes" if relation_[0] in results_list_layout else "No"       
                descriptions['answer_without_layout_with_o2'] =  "Yes" if relation_[0] in results_list_o2_td else "No"
                descriptions['answer_without_layout_with_o2_sd'] =  "Yes" if relation_[0] in results_list_o2_td else "No"
                
            # for comparing distance_2 info with and without layout                    
            if Counter(results_list_layout_o2_d2) != Counter(results_list_layout) and Counter(results_list_layout_o2_d2) != Counter(results_list_o2_d2) and len(results_list_layout_o2_d2) > 0:
                answer_ = random.sample(['Yes', 'No'], k =1)[0]
                if answer_ == 'Yes':
                    relation_ =  random.sample(results_list_layout_o2_d2, k =1)
                else:
                    unique_elements_list = list((set(results_list_layout) | set(results_list_o2_d2)) - set(results_list_layout_o2_d2))
                    relation_ =  random.sample(unique_elements_list, k =1)
                relation_sd = relation_[0].replace('north','in front of').replace('south','behind').replace('east','to the right of').replace('west','to the left of').replace('-', ' and ')
                descriptions['question_use_layout_o2_d2'] = f"Could the {query[0][0]} be placed to the {relation_[0]} of the {query[0][2]}?"  if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                               
                descriptions['question_use_layout_o2_d2_sd'] = f"Could the {query[0][0]} be placed {relation_sd} the {query[0][2]}?"  if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                                
                descriptions['answer_use_layout_o2_d2'] = answer_
                descriptions['answer_use_layout_o2_d2_sd'] = answer_
                descriptions['answer_without_layout_with_o2_d2'] = "Yes" if relation_[0] in results_list_layout_o2_d2 else "No"
                descriptions['answer_without_layout_with_o2_d2_sd'] = "Yes" if relation_[0] in results_list_layout_o2_d2 else "No"
                descriptions['answer_with_layout_without_o2_d2'] = "Yes" if relation_[0] in results_list_layout else "No"
                descriptions['answer_with_layout_without_o2_d2_sd'] = "Yes" if relation_[0] in results_list_layout else "No"                
                
            # for comparing distance_3 info with and without layout                    
            if Counter(results_list_layout_o2_d3) != Counter(results_list_layout) and Counter(results_list_layout_o2_d3) != Counter(results_list_o2_d3) and len(results_list_layout_o2_d3) > 0:
                answer_ = random.sample(['Yes', 'No'], k =1)[0]
                if answer_ == 'Yes':
                    relation_ =  random.sample(results_list_layout_o2_d3, k =1)
                else:
                    unique_elements_list = list((set(results_list_layout) | set(results_list_o2_d3)) - set(results_list_layout_o2_d3))
                    relation_ =  random.sample(unique_elements_list, k =1)
                relation_sd = relation_[0].replace('north','in front of').replace('south','behind').replace('east','to the right of').replace('west','to the left of').replace('-', ' and ')
                descriptions['question_use_layout_o2_d3'] = f"Could the {query[0][0]} be placed to the {relation_[0]} of the {query[0][2]}?"  if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                              
                descriptions['question_use_layout_o2_d3_sd'] = f"Could the {query[0][0]} be placed {relation_sd} the {query[0][2]}?"  if relation_[0] != 'overlap' else f"Could the {query[0][0]} be placed in the same location as the {query[0][2]}?"                                
                descriptions['answer_use_layout_o2_d3'] = answer_
                descriptions['answer_use_layout_o2_d3_sd'] = answer_
                descriptions['answer_without_layout_with_o2_d3'] = "Yes" if relation_[0] in results_list_layout_o2_d3 else "No"
                descriptions['answer_without_layout_with_o2_d3_sd'] = "Yes" if relation_[0] in results_list_layout_o2_d3 else "No"
                descriptions['answer_with_layout_without_o2_d3'] = "Yes" if relation_[0] in results_list_layout else "No"
                descriptions['answer_with_layout_without_o2_d3_sd'] = "Yes" if relation_[0] in results_list_layout else "No"   


            descriptions_list.append({
                'example_id': i,
                'descriptions': descriptions,
            })

        if facts_object and restory == False:  # Check if descriptions is not empty
            facts_list.append({
                'example_id': i,
                
                'query_o2': [(tup[0], tup[-1]) for tup in query],  ##    
                'query_o2_yn': query_yn_uni_logic, ## 

                'facts_layout': facts_object + facts_layout,               
                'solver_fr_layout': result_layout,
                
                'facts_layout_tpp': facts_object + facts_layout + facts_tpp,                
                'solver_fr_layout_tpp': result_layout_tpp,           
                
                'facts_o2': facts_object + facts_o2,
                'solver_fr_o2': result_o2,
                
                'facts_o2_d2': facts_object + facts_o2 + facts_d2,
                'solver_fr_o2_d2': result_o2_d2,       
                
                'facts_o2_d3': facts_object + facts_o2 + facts_d3,
                'solver_fr_o2_d3': result_o2_d3,

                'facts_layout_o2': facts_object  + facts_layout + facts_o2,
                'solver_fr_layout_o2': result_layout_o2,  
                                
                'facts_layout_o2_d2': facts_object  + facts_layout + facts_o2 + facts_d2,
                'solver_fr_layout_o2_d2': result_layout_o2_d2,   

                'facts_layout_o2_d3': facts_object  + facts_layout + facts_o2 + facts_d3,
                'solver_fr_layout_o2_d3': result_layout_o2_d3,           
                
                'answers_length_layout': len(result_layout),
                'answers_length_layout_tpp': len(result_layout_tpp),
                'answers_length_o2': len(result_o2),
                'answers_length_o2_d2': len(result_o2_d2),
                'answers_length_o2_d3': len(result_o2_d3),
                'answers_length_layout_o2': len(result_o2),
                'answers_length_layout_o2_d2': len(result_layout_o2_d2),
                'answers_length_layout_o2_d3': len(result_layout_o2_d3),              

                'time_layout': time_layout,
                'time_layout_tpp': time_layout_tpp,
                'time_o2': time_o2,
                'time_o2_d2': time_o2_d2,
                'time_o2_d3': time_o2_d3,
                'time_layout_o2': time_layout_o2,
                'time_layout_o2_d2': time_layout_o2_d2,
                'time_layout_o2_d3': time_layout_o2_d3,               

                
                'time_layout_yn': time_layout_yn,
                'time_layout_tpp_yn': time_layout_tpp_yn,
                'time_o2_yn': time_o2_yn,
                'time_o2_d2_yn': time_o2_d2_yn,
                'time_o2_d3_yn': time_o2_d3_yn,
                'time_layout_o2_yn': time_layout_o2_yn,
                'time_layout_o2_d2_yn': time_layout_o2_d2_yn,
                'time_layout_o2_d3_yn': time_layout_o2_d3_yn,                            
            })
            
                        
        if ful_k == test_num:
            return descriptions_list, facts_list, answers_length, times, times_yn, skip_id_list, solution_id_list
    # return descriptions_list, facts_list, answers_length, times, skip_id_list


def cache_exists(file_path):
    """Check if a cache file exists for a given file path."""
    return os.path.isfile(file_path)

def load_cache(file_path):
    """Load data from a cache file if it exists."""
    with open(file_path, 'r') as file:
        return json.load(file)

def save_cache(data, file_path):
    """Save data to a cache file."""
    with open(file_path, 'w') as file:
        json.dump(data, file)

def convert_str_to_number(s):
    try:
        return int(s)
    except ValueError:
        return float(s)

def load_answers(answers_file):
    with open(answers_file, 'r') as infile:
        answers_lengths_str_keys = json.load(infile)
        answers_lengths = {tuple(map(convert_str_to_number, key.split('_'))): value for key, value in answers_lengths_str_keys.items()}
        # answers_lengths = {convert_str_to_number(key): value for key, value in answers_lengths_str_keys.items()}
    return answers_lengths


def save_descriptions_facts(descriptions, filename):
    """Save the generated descriptions to a JSON file."""
    if not os.path.exists(filename):
        directory = os.path.dirname(filename)
        os.makedirs(directory, exist_ok= True)
    with open(filename, 'w') as outfile:
        json.dump(descriptions, outfile, indent=4)
    # print(f"Descriptions generated and saved to '{filename}'.")

def save_answers(answers_lengths, answers_file):
    with open(answers_file, 'w') as outfile:
        # Convert tuple keys to a consistent string format
        answers_lengths_str_keys = {'_'.join(map(str, key)): value for key, value in answers_lengths.items()}
        json.dump(answers_lengths_str_keys, outfile, indent=4)

def main(args):
    # Extract the arguments
    data_version = args.data_version
    test_num = args.test_num
    test_num_start = args.test_num_start
    domain_size = tuple(args.domain_size)
    n_range = args.n_range
    m_range = args.m_range
    
    directory = './Meta/SD-100'  # Replace with the path to your JSON files
    read_and_concatenate_json_files(directory, data_version)
    
    file_paths = {
    	'example': f'./Data/{data_version}/{data_version}.json', 
    	'material': './databases/material-database.json',
    	'objects': './databases/object-groups.json',
    	'receptacles': './databases/receptacles.json',
    	'assets': './databases/asset-database.json'
    }  

    data = load_data(file_paths)
    asset_mapping = build_asset_mapping(data['assets'])
    boundingBox_mapping = build_boundingBox_mapping(data['assets'])

    answers_lengths = {}
    times_take = {}
    times_yn_take = {}
    skip_id_dic = {}
    solution_id_dic = {}
    
    
    for n in n_range:  # Iterate n from 3 to 10  3, 11
        if n > 2:
            m_range = range(n-1, n*(n-1)//2)
        for m in m_range:
            print('n:', n, 'm:', m)
            description_file = f'./Data/{data_version}/Text/n{n}_m{m}_d{domain_size[0]*domain_size[1]}.json'
            facts_file = f'./Data/{data_version}/Logic/n{n}_m{m}_d{domain_size[0]*domain_size[1]}.json'
            answers_file = f'./Data/{data_version}/Logic/answers_lengths_d{domain_size[0]*domain_size[1]}.json'
            times_file = f'./Data/{data_version}/Logic/times_fr_take_d{domain_size[0]*domain_size[1]}.json'
            times_yn_file = f'./Data/{data_version}/Logic/times_yn_take_d{domain_size[0]*domain_size[1]}.json'
            skip_id_file = f'./Data/{data_version}/Logic/skip_id_d{domain_size[0]*domain_size[1]}.json'
            solution_id_file = f'./Data/{data_version}/Logic/solution_id_d{domain_size[0]*domain_size[1]}.json'
            # Check if cache exists
            if cache_exists(description_file) and cache_exists(facts_file):
                # Load cache
                all_descriptions = load_cache(description_file)
                all_facts = load_cache(facts_file)
                # if len(all_descriptions) == test_num:
                if all_descriptions[-1].get("example_id") == test_num - 1:
                    answers_lengths = load_answers(answers_file)
                    times_take = load_answers(times_file)
                    times_yn_take = load_answers(times_yn_file)
                    skip_id_dic = load_answers(skip_id_file)
                    solution_id_dic  = load_answers(solution_id_file)
                else:
                    test_num_start = all_descriptions[-1]['example_id'] + 1
                    k_start = len(all_descriptions)
                    all_descriptions_new, all_facts_new, answers_length_new, times_take_new, times_take_yn_new, skip_id_list_new, solution_id_list_new = generate_descriptions_facts(data, asset_mapping, boundingBox_mapping, n, m, test_num, test_num_start, k_start, domain_size)
                    all_descriptions += all_descriptions_new
                    all_facts += all_facts_new
                    answers_lengths = load_answers(answers_file)
                    times_take = load_answers(times_file)
                    times_yn_take = load_answers(times_yn_file)
                    skip_id_dic = load_answers(skip_id_file)
                    solution_id_dic= load_answers(solution_id_file)
                    answers_length = answers_lengths[n,m] 
                    times_take_ = times_take[n,m] 
                    times_yn_take_ = times_yn_take[n,m] 
                    skip_id_list = skip_id_dic[n,m] 
                    solution_id_list = solution_id_dic[n,m] 
                    answers_length.update(answers_length_new)
                    times_take_.update(times_take_new)
                    times_yn_take_.update(times_take_yn_new)
                    skip_id_list += (skip_id_list_new)
                    solution_id_list += (solution_id_list_new)
                    answers_lengths[n,m]  = answers_length
                    times_take[n,m]  = times_take_
                    times_yn_take[n,m]  = times_yn_take_
                    skip_id_dic[n,m]  = skip_id_list
                    solution_id_dic[n,m]  = solution_id_list
            else:
                k_start = 0
                all_descriptions, all_facts, answers_length, times, times_yn, skip_id_list, solution_id_list = generate_descriptions_facts(data, asset_mapping, boundingBox_mapping, n, m, test_num, test_num_start, k_start, domain_size)
                if os.path.exists(answers_file):
                    answers_lengths = load_answers(answers_file)
                    times_take = load_answers(times_file)
                    times_yn_take = load_answers(times_yn_file)
                    skip_id_dic = load_answers(skip_id_file)
                    solution_id_dic  = load_answers(solution_id_file)
                answers_lengths[n,m]  = answers_length
                times_take[n,m]  = times
                times_yn_take[n,m]  = times_yn
                skip_id_dic[n,m]  = skip_id_list
                solution_id_dic[n,m]  = solution_id_list
            save_descriptions_facts(all_descriptions, description_file)
            save_descriptions_facts(all_facts, facts_file)
            save_answers(answers_lengths, answers_file)
            save_answers(times_take, times_file)
            save_answers(times_yn_take, times_yn_file)
            save_answers(skip_id_dic, skip_id_file)
            save_answers(solution_id_dic, solution_id_file)


if __name__ == '__main__':
    # Parse command-line arguments
    parser = argparse.ArgumentParser(description="Generate room descriptions and facts.")
    parser.add_argument('--data_version', type=str, default='SD-100', help="Version of the dataset to use (e.g., SD-100, SD-1K, SD-10k).")
    parser.add_argument('--test_num', type=int, default=1, help="Number of test cases to process.")
    parser.add_argument('--test_num_start', type=int, default=0, help="Index to start processing test cases.")
    parser.add_argument('--domain_size', type=tuple, default=(12, 12), help="Size of the domain grid as two integers (width, height).")
    parser.add_argument('--n_range', type=list, default=[5], help="Number of objects to consider.")
    parser.add_argument('--m_range', type=list, default=[4,5,6,7,8,9], help="Number of object pairs to consider.")
    
    args = parser.parse_args()
    
    # Pass the parsed arguments to the main function
    main(args)
