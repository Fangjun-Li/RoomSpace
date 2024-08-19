#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Apr 18, 2024

@author: Fangjun
"""

from constraint import Problem
import time
import numpy as np

# Domain size for the grid (width, height)
def generate_grid_points(domain_size= (12, 12), res= 1):
    x_values = np.arange(0, domain_size[0], res)
    y_values = np.arange(0, domain_size[1], res)
    return [(x, y) for x in x_values for y in y_values]

# Room boundary constraints
def touch_room(pos, domain_size):
    max_x, max_y = domain_size[0] - 1, domain_size[1] - 1
    return pos[0] == 0 or pos[0] == max_x or pos[1] == 0 or pos[1] == max_y

def not_touch_room(pos, domain_size):
    max_x, max_y = domain_size[0], domain_size[1]
    return 0 < pos[0] < max_x and 0 < pos[1] < max_y

# Positional constraints within a room divided into nine regions
def north_room(pos, domain_size): return domain_size[0] / 3 <= pos[0] < domain_size[0] * 2 / 3 and pos[1] >= domain_size[1] * 2 / 3
def south_room(pos, domain_size): return domain_size[0] / 3 <= pos[0] < domain_size[0] * 2 / 3 and pos[1] < domain_size[1] / 3
def east_room(pos, domain_size): return pos[0] >= domain_size[0] * 2 / 3 and domain_size[1] / 3 <= pos[1] < domain_size[1] * 2 / 3
def west_room(pos, domain_size): return pos[0] < domain_size[0] / 3 and domain_size[1] / 3 <= pos[1] < domain_size[1] * 2 / 3
def center_room(pos, domain_size): return domain_size[0] / 3 <= pos[0] < domain_size[0] * 2 / 3 and domain_size[1] / 3 <= pos[1] < domain_size[1] * 2 / 3
def northeast_room(pos, domain_size): return pos[0] >= domain_size[0] * 2 / 3 and pos[1] >= domain_size[1] * 2 / 3
def northwest_room(pos, domain_size): return pos[0] < domain_size[0] / 3 and pos[1] >= domain_size[1] * 2 / 3
def southeast_room(pos, domain_size): return pos[0] >= domain_size[0] * 2 / 3 and pos[1] < domain_size[1] / 3
def southwest_room(pos, domain_size): return pos[0] < domain_size[0] / 3 and pos[1] < domain_size[1] / 3
def in_room(pos, domain_size): return pos[0] < domain_size[0] and pos[1] < domain_size[1]

# Cardinal direction constraints between objects
def north(pos1, pos2): return pos1[1] > pos2[1] and pos1[0] == pos2[0]
def south(pos1, pos2): return pos1[1] < pos2[1] and pos1[0] == pos2[0]
def east(pos1, pos2): return pos1[0] > pos2[0] and pos1[1] == pos2[1]
def west(pos1, pos2): return pos1[0] < pos2[0] and pos1[1] == pos2[1]
def northeast(pos1, pos2): return pos1[1] > pos2[1] and pos1[0] > pos2[0]
def northwest(pos1, pos2): return pos1[1] > pos2[1] and pos1[0] < pos2[0]
def southeast(pos1, pos2): return pos1[1] < pos2[1] and pos1[0] > pos2[0]
def southwest(pos1, pos2): return pos1[1] < pos2[1] and pos1[0] < pos2[0]
def overlap(pos1, pos2): return pos1[0] == pos2[0] and pos1[1] == pos2[1]

# Distance-based constraints
def close_3(pos1, pos2, domain_size):
    max_distance = np.sqrt((domain_size[0] - 1) ** 2 + (domain_size[1] - 1) ** 2) / 3
    distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return distance <= max_distance

def medium_3(pos1, pos2, domain_size):
    min_distance = np.sqrt((domain_size[0] - 1) ** 2 + (domain_size[1] - 1) ** 2) / 3
    max_distance = np.sqrt((domain_size[0] - 1) ** 2 + (domain_size[1] - 1) ** 2) * 2 / 3
    distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return min_distance < distance <= max_distance

def far_3(pos1, pos2, domain_size):
    min_distance = np.sqrt((domain_size[0] - 1) ** 2 + (domain_size[1] - 1) ** 2) * 2 / 3
    distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return distance > min_distance

def close_2(pos1, pos2, domain_size):
    boundary_distance = (domain_size[0] - 1) / 2
    distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return distance <= boundary_distance

def far_2(pos1, pos2, domain_size):
    boundary_distance = (domain_size[0] - 1) / 2
    distance = np.sqrt((pos1[0] - pos2[0]) ** 2 + (pos1[1] - pos2[1]) ** 2)
    return distance > boundary_distance

# Directional constraints dictionary
def get_direction_constraints(domain_size):
    return {
        'N': north,
        'S': south,
        'E': east,
        'W': west,
        'NE': northeast,
        'NW': northwest,
        'SE': southeast,
        'SW': southwest,
        'O': overlap,

        'NR': lambda pos: north_room(pos, domain_size),
        'SR': lambda pos: south_room(pos, domain_size),
        'ER': lambda pos: east_room(pos, domain_size),
        'WR': lambda pos: west_room(pos, domain_size),
        'NER': lambda pos: northeast_room(pos, domain_size),
        'NWR': lambda pos: northwest_room(pos, domain_size),
        'SER': lambda pos: southeast_room(pos, domain_size),
        'SWR': lambda pos: southwest_room(pos, domain_size),
        'CR': lambda pos: center_room(pos, domain_size),

        'INR': lambda pos: in_room(pos, domain_size),
        'TPP': lambda pos: touch_room(pos, domain_size),
        'NTPP': lambda pos: not_touch_room(pos, domain_size),

        'CL3': lambda pos1, pos2: close_3(pos1, pos2, domain_size),
        'MD3': lambda pos1, pos2: medium_3(pos1, pos2, domain_size),
        'FR3': lambda pos1, pos2: far_3(pos1, pos2, domain_size),

        'CL2': lambda pos1, pos2: close_2(pos1, pos2, domain_size),
        'FR2': lambda pos1, pos2: far_2(pos1, pos2, domain_size),
    }

# Function to generate abbreviations
def generate_abbreviation(direction):
    return ''.join(word[0].upper() for word in direction.split('-'))


def solve_single_candidate(example,relation_description, domain_size):
    relation_candidate = generate_abbreviation(relation_description)
    all_objects = set(obj for fact in example['facts'] for obj in [fact[0], fact[2]] if obj != "room")
    
    grid_points = generate_grid_points(domain_size)
    direction_constraints = get_direction_constraints(domain_size)

    problem = Problem()
    for obj in all_objects:
        problem.addVariable(obj, grid_points)
    
    for fact in example['facts']:
        obj1, relation, obj2 = fact
        if obj2 == "room":
            problem.addConstraint(direction_constraints[relation], [obj1])
        else:
            problem.addConstraint(direction_constraints[relation], [obj1, obj2])
    
    start_time = time.time()
    if example.get('query') and isinstance(example['query'][-1], tuple):
        obj_query = example['query'][-1][0]
        obj2_query= example['query'][-1][-1]
        if obj2_query != 'room':
            problem.addConstraint(direction_constraints[relation_candidate], [obj_query, obj2_query])

    solution = problem.getSolution()
    solution_time = time.time() - start_time
    
    if solution:
        return 'Yes', solution_time
    else:
        return 'No', solution_time    
    
    

def solve_all_candidates(example, domain_size):
    relation_candidates = ['N', 'S', 'E', 'W', 'NE', 'NW', 'SE', 'SW', 'O']
    solvable_relations = []    
    all_objects = set(obj for fact in example['facts'] for obj in [fact[0], fact[2]] if obj != "room")
    
    grid_points = generate_grid_points(domain_size)
    direction_constraints = get_direction_constraints(domain_size)
    start_time = time.time()

    for relation in relation_candidates:
        problem = Problem()
        for obj in all_objects:
            problem.addVariable(obj, grid_points)

        for fact in example['facts']:
            obj1, relation_type, obj2 = fact
            if obj2 == "room":
                problem.addConstraint(direction_constraints[relation_type], [obj1])
            else:
                problem.addConstraint(direction_constraints[relation_type], [obj1, obj2])

        if example.get('query') and isinstance(example['query'][-1], tuple):
            obj_query = example['query'][-1][0]
            obj2_query= example['query'][-1][-1]
            if obj2_query != 'room':
                problem.addConstraint(direction_constraints[relation], [obj_query, obj2_query])

            solution = problem.getSolution()
            if solution:
                solvable_relations.append(relation)

    solution_time = time.time() - start_time
    return solvable_relations, solution_time

