import os
import shutil

def cleanup_fail():
    folder_name = "spl_output"
    # Get the current working directory
    current_dir = os.getcwd()
    # Full path of the folder
    folder_path = os.path.join(current_dir, folder_name)

    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Delete the folder and all its contents
        shutil.rmtree(folder_path)
        print(f"The folder '{folder_name}' and all its contents have been deleted.")
    else:
        print(f"The folder '{folder_name}' does not exist.")

def cleanup_success():
    folder_name = "spl_output/test_temp"
    # Get the current working directory
    current_dir = os.getcwd()
    # Full path of the folder
    folder_path = os.path.join(current_dir, folder_name)

    # Check if the folder exists
    if os.path.exists(folder_path) and os.path.isdir(folder_path):
        # Delete the folder and all its contents
        shutil.rmtree(folder_path)
        print(f"The folder '{folder_name}' and all its contents have been deleted.")
    else:
        print(f"The folder '{folder_name}' does not exist.")
