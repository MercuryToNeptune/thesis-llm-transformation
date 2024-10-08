import os
import shutil

def create_spl_directory(variant_paths, spl_output):
    """
    Creates the SPL directory by merging multiple variant directories.
    
    Parameters:
    variant_paths (list of str): List of paths to variant directories.
    spl_output (str): Path where the SPL directory will be created.
    """
    if not os.path.exists(spl_output):
        os.makedirs(spl_output)

    # Dictionary to track files across all variants
    file_occurrences = {}

    # Traverse each variant directory
    for variant_index, variant in enumerate(variant_paths):
        variant_name = os.path.basename(variant)  # Get the variant's folder name
        for dirpath, dirnames, filenames in os.walk(variant):
            relative_path = os.path.relpath(dirpath, variant)

            # Skip files in the "build" or "doc" directories
            if should_exclude_directory(relative_path):
                continue

            spl_dir = os.path.join(spl_output, relative_path)

            # Create directories in SPL if not present
            if not os.path.exists(spl_dir):
                os.makedirs(spl_dir)

            # Process each file
            for filename in filenames:
                src_file = os.path.join(dirpath, filename)
                dest_file = os.path.join(spl_dir, filename)

                # Check if the file is in a test directory or has 'test' in its name
                if is_test_file(relative_path, filename):
                    # Track occurrences of each file (for "test" cases)
                    if (relative_path, filename) not in file_occurrences:
                        file_occurrences[(relative_path, filename)] = []
                    file_occurrences[(relative_path, filename)].append((variant_index, variant_name, src_file))

                    # If the file hasn't been copied to SPL yet, copy it
                    if len(file_occurrences[(relative_path, filename)]) == 1:
                        shutil.copy2(src_file, dest_file)
                    
                    # Additionally copy the test file to test_temp/{variant-name} directory at root level
                    test_temp_output_dir = os.path.join(spl_output, "test_temp", variant_name)
                    if not os.path.exists(test_temp_output_dir):
                        os.makedirs(test_temp_output_dir)
                    test_temp_dest_file = os.path.join(test_temp_output_dir, filename)
                    shutil.copy2(src_file, test_temp_dest_file)
                    # print(f"Copied {filename} to {test_temp_dest_file}")
                else:
                    # Execute original logic for non-"test" files
                    if (relative_path, filename) not in file_occurrences:
                        file_occurrences[(relative_path, filename)] = []
                    file_occurrences[(relative_path, filename)].append((variant_index, variant_name, src_file))

                    # If the file hasn't been copied to SPL yet, copy it
                    if len(file_occurrences[(relative_path, filename)]) == 1:
                        shutil.copy2(src_file, dest_file)

    # Process files that exist in multiple variants
    for (relative_path, filename), occurrences in file_occurrences.items():
        if is_test_file(relative_path, filename):
            if len(occurrences) > 1:  # File exists in more than one variant for "test" files
                # Check if all files have the same content
                first_file_content = get_file_content(occurrences[0][2])
                all_same_content = all(
                    first_file_content == get_file_content(src_file)
                    for _, _, src_file in occurrences
                )

                if all_same_content:
                    # If all files have the same content, only keep one
                    dest_file = os.path.join(spl_output, relative_path, filename)
                    shutil.copy2(occurrences[0][2], dest_file)
                    # print(f"Kept single copy of {filename} with identical content.")
                else:
                    # If files have different content, keep all with variant-specific names
                    for variant_index, variant_name, src_file in occurrences:
                        renamed_file = f"{variant_name}-{filename}"
                        dest_file = os.path.join(spl_output, relative_path, renamed_file)
                        shutil.copy2(src_file, dest_file)
                        # print(f"Copied {filename} as {renamed_file} due to differing content.")
                    
                    # After creating renamed files, delete the original file if it exists
                    original_file_path = os.path.join(spl_output, relative_path, filename)
                    if os.path.exists(original_file_path):
                        os.remove(original_file_path)
                        # print(f"Deleted original file: {original_file_path}")

                # Check for markers in the files
                if any(file_contains_markers(src_file) for _, _, src_file in occurrences) or filename == "CMakeLists.txt":
                    create_variable_file(occurrences, spl_output, relative_path, filename, is_test=True)
                    delete_original_file(spl_output, relative_path, filename)
        else:
            # Original behavior for non-"test" files
            if len(occurrences) > 1:  # File exists in more than one variant
                # Check for markers in all occurrences
                if any(file_contains_markers(src_file) for _, _, src_file in occurrences) or filename == "CMakeLists.txt":
                    create_variable_file(occurrences, spl_output, relative_path, filename, is_test=False)
                    delete_original_file(spl_output, relative_path, filename)

    # Copy all .h files from spl_output to test_temp/headers
    headers_output_dir = os.path.join(spl_output, "test_temp", "headers")
    if not os.path.exists(headers_output_dir):
        os.makedirs(headers_output_dir)

    for dirpath, dirnames, filenames in os.walk(spl_output):
        for filename in filenames:
            if filename.endswith(".h"):
                src_file = os.path.join(dirpath, filename)
                dest_file = os.path.join(headers_output_dir, filename)

                # Only copy if the source and destination are not the same file
                if os.path.abspath(src_file) != os.path.abspath(dest_file):
                    shutil.copy2(src_file, dest_file)
                    # print(f"Copied {filename} to {dest_file}")
                # else:
                    # print(f"Skipped copying {filename} as source and destination are the same.")

        # New logic: Create spl_output/builder_testbench and copy each variant directory
   
    # Define the path to the test_temp directory
    test_temp_dir = os.path.join(spl_output, "test_temp")
    builder_testbench_dir = os.path.join(spl_output, "builder_testbench")
    if not os.path.exists(builder_testbench_dir):
        os.makedirs(builder_testbench_dir)

    # Copy each variant directory to builder_testbench
    for variant in variant_paths:
        variant_name = os.path.basename(variant)  # Get the variant's folder name
        destination_variant_dir = os.path.join(builder_testbench_dir, variant_name)
        if not os.path.exists(destination_variant_dir):
            shutil.copytree(variant, destination_variant_dir, ignore=shutil.ignore_patterns('build', 'doc', '.git', '.vscode'))
            # print(f"Copied {variant_name} to {destination_variant_dir}")

            # Check if test_temp exists and copy it to the variant directory
            destination_test_temp_dir = os.path.join(destination_variant_dir, "test_temp")
            if os.path.exists(test_temp_dir):
                shutil.copytree(test_temp_dir, destination_test_temp_dir)
                # print(f"Copied test_temp to {destination_test_temp_dir}")
            # else:
                # print(f"test_temp does not exist in {spl_output}, skipping copy.")
        # else:
            # print(f"{destination_variant_dir} already exists, skipping copy.")
    
    print("Finished pre-processing.")


def is_test_file(relative_path, filename):
    """
    Check if the file is in a test directory or if its name contains 'test'.
    
    Parameters:
    relative_path (str): The relative path where the file is located.
    filename (str): The name of the file.
    
    Returns:
    bool: True if the file is in a 'test' directory or its name contains 'test', False otherwise.
    """
    # Check if any part of the relative path contains 'test' (case-insensitive)
    if 'test' in relative_path.lower():
        return True
    
    # Check if the filename contains 'test' (case-insensitive)
    if 'test' in filename.lower():
        return True
    
    return False

def should_exclude_directory(relative_path):
    """
    Check if the file is in a 'build' or 'doc' directory.
    
    Parameters:
    relative_path (str): The relative path where the file is located.
    
    Returns:
    bool: True if the directory is 'build' or 'doc', False otherwise.
    """
    # Exclude files from 'build' or 'doc' directories (case-insensitive)
    return 'build' in relative_path.lower() or 'doc' in relative_path.lower() or '.git' in relative_path.lower() or '.vscode' in relative_path.lower()

def get_file_content(file_path):
    """
    Reads and returns the content of a file.
    
    Parameters:
    file_path (str): Path to the file.
    
    Returns:
    str: The content of the file.
    """
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            return file.read()
    except UnicodeDecodeError as e:
        print(f"Error decoding file {file_path}: {e}")
        return ""


def file_contains_markers(file_path):
    """
    Check if the file contains both // Start- and // End- markers.
    
    Parameters:
    file_path (str): Path to the file.
    
    Returns:
    bool: True if the markers are found, False otherwise.
    """
    start_marker = "// Start-"
    end_marker = "// End-"
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as file:
            content = file.read()
            return start_marker in content and end_marker in content
    except UnicodeDecodeError as e:
        print(f"Error decoding file {file_path}: {e}")
        return False

def create_variable_file(occurrences, spl_output, relative_path, original_name, is_test):
    """
    Creates a variable file by combining contents of the file from multiple variants.
    
    Parameters:
    occurrences (list): List of tuples containing (variant_index, variant_name, file_path).
    spl_output (str): Path where the SPL directory is created.
    relative_path (str): Relative path in the SPL directory.
    original_name (str): Name of the original file.
    is_test (bool): Whether the file is part of the "test" case.
    """
    variable_file_name = f"variable-{original_name}"
    variable_file_path = os.path.join(spl_output, relative_path, variable_file_name)

    # Ensure the directory exists
    spl_dir = os.path.join(spl_output, relative_path)
    if not os.path.exists(spl_dir):
        os.makedirs(spl_dir)

    with open(variable_file_path, 'w', encoding='utf-8') as variable_file:
        for variant_index, variant_name, src_file in occurrences:
            with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                variable_file.write(f"// content for {variant_name} variant\n")
                variable_file.write(f.read())
                variable_file.write("\n\n")  # Insert comment delimiter

    # print(f"Created {variable_file_name} with contents from {len(occurrences)} variants.")


def delete_original_file(spl_output, relative_path, filename):
    """
    Deletes the original {filename} file from the SPL directory.
    
    Parameters:
    spl_output (str): Path to the SPL directory.
    relative_path (str): Relative path to the file's location.
    filename (str): Name of the file to be deleted.
    """
    original_file_path = os.path.join(spl_output, relative_path, filename)

    if os.path.exists(original_file_path):
        os.remove(original_file_path)
        # print(f"Deleted original file: {original_file_path}")
    else:
        print(f"File not found for deletion: {original_file_path}")

# Create new directories inside spl_output

def create_prompt_dirs():
    parent_dir = "spl_output"
    new_dirs = ["prompts", "prompts_responses"]

    # Check if the parent directory exists, if not, create it
    if not os.path.exists(parent_dir):
        os.mkdir(parent_dir)

    # Now create the subdirectories inside the parent directory
    for dir_name in new_dirs:
        path = os.path.join(parent_dir, dir_name)
        if not os.path.exists(path):
            os.mkdir(path)

def extract_variant_names(variant_paths):
    # Extract the last part of each path
    variant_names = [path.split('/')[-1] for path in variant_paths]
    return variant_names

