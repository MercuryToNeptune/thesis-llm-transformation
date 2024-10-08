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
        for dirpath, dirnames, filenames in os.walk(variant):
            relative_path = os.path.relpath(dirpath, variant)
            spl_dir = os.path.join(spl_output, relative_path)

            # Create directories in SPL if not present
            if not os.path.exists(spl_dir):
                os.makedirs(spl_dir)

            # Process each file
            for filename in filenames:
                src_file = os.path.join(dirpath, filename)
                dest_file = os.path.join(spl_dir, filename)

                # Track occurrences of each file
                if (relative_path, filename) not in file_occurrences:
                    file_occurrences[(relative_path, filename)] = []
                file_occurrences[(relative_path, filename)].append((variant_index, src_file))

                # If the file hasn't been copied to SPL yet, copy it
                if len(file_occurrences[(relative_path, filename)]) == 1:
                    shutil.copy2(src_file, dest_file)

    # Process files that exist in multiple variants and check for markers
    for (relative_path, filename), occurrences in file_occurrences.items():
        if len(occurrences) > 1:  # File exists in more than one variant
            # Check for markers in all occurences
            if any(file_contains_markers(src_file) for _, src_file in occurrences) or filename == "CMakeLists.txt":
                create_variable_file(occurrences, spl_output, relative_path, filename)
                delete_original_file(spl_output, relative_path, filename)


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

def create_variable_file(occurrences, spl_output, relative_path, original_name):
    """
    Creates a variable file by combining contents of the file from multiple variants.
    
    Parameters:
    occurrences (list): List of tuples containing (variant_index, file_path).
    spl_output (str): Path where the SPL directory is created.
    relative_path (str): Relative path in the SPL directory.
    original_name (str): Name of the original file.
    """
    variable_file_name = f"variable-{original_name}"
    variable_file_path = os.path.join(spl_output, relative_path, variable_file_name)

    # Ensure the directory exists
    spl_dir = os.path.join(spl_output, relative_path)
    if not os.path.exists(spl_dir):
        os.makedirs(spl_dir)

    with open(variable_file_path, 'w', encoding='utf-8') as variable_file:
        for variant_index, src_file in occurrences:
            # Write content of each variant's file
            with open(src_file, 'r', encoding='utf-8', errors='ignore') as f:
                variable_file.write(f"// Content from variant {variant_index + 1}\n")
                variable_file.write(f.read())
                variable_file.write("\n// ------------\n")  # Insert comment delimiter

    print(f"Created {variable_file_name} with contents from {len(occurrences)} variants.")

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
        print(f"Deleted original file: {original_file_path}")
    else:
        print(f"File not found for deletion: {original_file_path}")

# Example usage
variant_paths = [
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/SPLedFork/variant-1',
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/SPLedFork/variant-5',
    'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/SPLedFork/variant-4',
]
spl_output = 'C:/Users/aatra/Desktop/2022- Deutschland/Uni Stuttgart/Sem 4/MA/code/dir-struct-generation/spl_output'

create_spl_directory(variant_paths, spl_output)
