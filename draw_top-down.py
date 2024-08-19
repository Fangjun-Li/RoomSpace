import os
import json
from ai2thor.controller import Controller
from PIL import Image

def read_json_file(file_path):
    """Reads a JSON file and returns its content."""
    with open(file_path, 'r') as file:
        return json.load(file)

def process_and_save_top_down_image(house, controller, output_path, is_first=False):
    """Processes and saves the top-down image of a room."""
    if is_first:
        controller = Controller(scene=house, width=1024, height=1024, makeAgentsVisible=False)  # Create a new controller instance
    else:
        controller.reset(scene=house, width=1024, height=1024, makeAgentsVisible=False)  # Reset the existing controller with the new scene


    top_down_image = get_top_down_frame(controller)
    top_down_image.save(output_path)
    return controller
    
def get_top_down_frame(controller):
    """Captures and returns a top-down frame from the given controller."""
    # Setup the top-down camera
    event = controller.step(action="GetMapViewCameraProperties", raise_for_failure=True)
    pose = event.metadata["actionReturn"]

    # Configure camera properties
    bounds = event.metadata["sceneBounds"]["size"]
    max_bound = max(bounds["x"], bounds["z"])
    
    pose["fieldOfView"] = 65
    pose["position"]["y"] += 0.7 * max_bound   
    pose["rotation"]["x"] = 90
    
    pose["orthographic"] = False
    pose["farClippingPlane"] = 50
    del pose["orthographicSize"]

    # Add the camera to the scene and capture the frame
    event = controller.step(action="AddThirdPartyCamera", **pose, skyboxColor="white", raise_for_failure=True)
    top_down_frame = event.third_party_camera_frames[-1]
    return Image.fromarray(top_down_frame)
    

def cache_exists(file_path):
    """Check if a cache file exists for a given file path."""
    return os.path.isfile(file_path)

def main():
    meta_folder = './Meta/SD-100'  # Replace with the path to your 'meta' folder
    top_down_output_folder = './Data/SD-100/Image/top-down'  

    os.makedirs(top_down_output_folder, exist_ok=True)  # Ensure the output folder exists
    controller = None
    first = True

    i = 0 
    for file_name in os.listdir(meta_folder):
        i += 1
        if file_name.endswith('.json'):
            json_file_path = os.path.join(meta_folder, file_name)
            top_down_output_image_path = os.path.join(top_down_output_folder, file_name.replace('.json', '.png'))
            print(i, top_down_output_image_path)
            
            if not cache_exists(top_down_output_image_path):
                house = read_json_file(json_file_path)
                controller = process_and_save_top_down_image(house, controller, top_down_output_image_path, is_first=first)
                first = False

    if controller:
        controller.stop()  # Stop the controller when done

if __name__ == "__main__":
    main()

