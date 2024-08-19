#%%
import logging
import random
from typing import Optional, Tuple

import numpy as np

from procthor.constants import OUTDOOR_ROOM_ID

DEFAULT_AVERAGE_ROOM_SIZE = 3
"""Average room size in meters"""

DEFAULT_MIN_HOUSE_SIDE_LENGTH = 2
"""Min length of a side of the house (in meters)."""

DEFAULT_MAX_BOUNDARY_CUT_AREA = 6
"""Max area of a single chop along the boundary."""


def get_n_cuts(num_rooms: int) -> int:
    return round(np.random.beta(a=0.5 * num_rooms, b=6) * 10)


def sample_interior_boundary(num_rooms, average_room_size, dims):
    """Sample a rectangular boundary for the interior of a house."""
    assert num_rooms > 0

    # If dimensions are not provided, calculate them based on the number of rooms and average room size
    if dims is None:
        x_size, z_size = calculate_interior_dimensions(num_rooms, average_room_size)
    else:
        x_size, z_size = dims

    # Create a boundary with all zeros (indicating empty space)
    boundary = np.zeros((z_size, x_size), dtype=int)

    return boundary

def calculate_interior_dimensions(num_rooms, average_room_size):
    # Calculate dimensions based on number of rooms and average room size
    # This is a placeholder - implement according to how you want to organize rooms
    x_size = int(np.sqrt(num_rooms) * average_room_size)
    z_size = x_size  # Assuming square layout for simplicity
    return x_size, z_size




   
