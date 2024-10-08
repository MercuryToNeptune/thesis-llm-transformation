import os
import shutil
import gpt_api as gpt_api
import subprocess
from dotenv import load_dotenv

load_dotenv()
# Get the API key from the environment variable
api_key = os.getenv("OPENAI_KEY")

def create_platform_cmake():
    """
    Central function which calls all other helper functions in this file.
    """
    gen_fail_flag = False
    gpt_api.send_cmake_prompt(api_key, "spl_output/prompts/prompt_cmake.txt", "spl_output/prompts_responses/response_cmake.txt")
    copy_llmresponse_to_builder_testbench("spl_output/prompts_responses/response_cmake.txt")
    cmakeGenComplete, variant_failed, errorMsg = build_using_llm_cmake('spl_output/builder_testbench/')
    print(f"LLM CMake generation {'succeeded' if cmakeGenComplete else 'failed'}.")
    max_feedback_attempts = 5
    for attempt in range(max_feedback_attempts):
        if not cmakeGenComplete: 
            print(f"Attempt {attempt + 1} to fix build file using feedback.")
            stitch_feedback_prompt_cmake(variant_failed, errorMsg)
            gpt_api.send_cmakefeedback_prompt(api_key, "spl_output/prompts/feedback_prompt_cmake.txt", "spl_output/prompts_responses/feedback_response_cmake.txt")
            copy_llmresponse_to_builder_testbench("spl_output/prompts_responses/feedback_response_cmake.txt")
            cmakeGenComplete, variant_failed, errorMsg = build_using_llm_cmake('spl_output/builder_testbench/')
            print(f"LLM CMake generation {'succeeded' if cmakeGenComplete else 'failed'}.")
            if cmakeGenComplete:
                break  # Exit loop if generation succeeds
    
    if not cmakeGenComplete:
        print(f"Maximum feedback attempts ({max_feedback_attempts}) exceeded. CMake generation failed.")
        gen_fail_flag = True
    # copy working CMakeLists.txt to the main CMakeLists.txt of spl_output
    if cmakeGenComplete:
        find_and_copy_file("CMakeLists.txt", "spl_output/builder_testbench", "spl_output")
        shutil.rmtree("spl_output/builder_testbench")
    
    return gen_fail_flag


def find_and_copy_file(filename, search_dir, dest_dir):
    """
    Finds the first occurrence of the file with the specified filename in the search directory 
    and copies it to the destination directory.

    :param filename: Name of the file to search for.
    :param search_dir: Directory to search within.
    :param dest_dir: Destination directory to copy the file to.
    :return: Full path of the copied file if found and copied, None otherwise.
    """
    for root, dirs, files in os.walk(search_dir):
        if filename in files:
            source_path = os.path.join(root, filename)
            dest_path = os.path.join(dest_dir, filename)
            shutil.copy(source_path, dest_path)
            print(f"File '{filename}' found at '{source_path}' and copied to '{dest_path}'")
            return dest_path
    print(f"File '{filename}' not found in '{search_dir}'")
    return None

def stitch_variablecmake_into_prompt():
    spl_output_dir = "spl_output"
    prompt_file_relative_path = "prompts/prompt_cmake.txt"

    # Step 1: Search for variable-CMakeLists.txt inside the spl_output directory (without subdirectories)
    cmake_file_path = None
    for item in os.listdir(spl_output_dir):
        if item == "variable-CMakeLists.txt":
            cmake_file_path = os.path.join(spl_output_dir, item)
            break

    if not cmake_file_path:
        raise FileNotFoundError("variable-CMakeLists.txt not found in the spl_output directory.")

    # Step 2: Read the contents of variable-CMakeLists.txt
    with open(cmake_file_path, 'r') as cmake_file:
        cmake_content = cmake_file.read()

    # Step 3: Search for the prompts/prompt_cmake.txt in the current directory
    prompt_file_source = os.path.join(os.getcwd(), prompt_file_relative_path)

    if not os.path.exists(prompt_file_source):
        raise FileNotFoundError(f"{prompt_file_relative_path} not found in the current directory.")

    # Step 4: Copy the prompts/prompt_cmake.txt to spl_output/prompts/prompt_cmake.txt
    prompt_file_destination = os.path.join(spl_output_dir, prompt_file_relative_path)
    os.makedirs(os.path.dirname(prompt_file_destination), exist_ok=True)
    shutil.copy(prompt_file_source, prompt_file_destination)

    # Step 5: Open the copied file and replace the occurrence of the placeholder
    with open(prompt_file_destination, 'r') as prompt_file:
        prompt_content = prompt_file.read()

    updated_content = prompt_content.replace('{{replace with variable-CMakeLists.txt}}', cmake_content)

    # Write the updated content back to the file
    with open(prompt_file_destination, 'w') as prompt_file:
        prompt_file.write(updated_content)

    print(f"Processed file and updated {prompt_file_destination} successfully.")


def stitch_feedback_prompt_cmake(variant_failed, errorMsg):
    feedback_prompt_file_path = 'prompts/feedback_prompt_cmake.txt'
    updated_feedback_prompt_file_path = 'spl_output/prompts/feedback_prompt_cmake.txt'
    llm_response_file_path = 'spl_output/prompts_responses/response_cmake.txt'
    
    # Read the feedback prompt template
    with open(feedback_prompt_file_path, 'r') as file:
        feedback_prompt_content = file.read()

    # Read the LLM response content
    with open(llm_response_file_path, 'r') as file:
        llm_response_content = file.read()

    # Extract content between ```cmake and ```
    start_delim = "```cmake"
    end_delim = "```"
    start_index = llm_response_content.find(start_delim)
    end_index = llm_response_content.find(end_delim, start_index + len(start_delim))
    
    if start_index == -1 or end_index == -1:
        print("Delimiters not found in the input file.")
        return
    
    llm_response_content = llm_response_content[start_index + len(start_delim):end_index].strip()

    # Replace the placeholders
    updated_feedback_prompt = feedback_prompt_content.replace('{{replace with llm-create CMakeLists}}', llm_response_content)
    updated_feedback_prompt = updated_feedback_prompt.replace('{{replace with variant name which error occurs}}', variant_failed)
    updated_feedback_prompt = updated_feedback_prompt.replace('{{replace with error msg encountered during build}}', errorMsg)

    # Write the updated feedback prompt to a new file in the specified location
    with open(updated_feedback_prompt_file_path, 'w') as file:
        file.write(updated_feedback_prompt)

def copy_llmresponse_to_builder_testbench(response_file_path):
    # Define file paths
    input_file_path = response_file_path
    builder_testbench_dir = 'spl_output/builder_testbench'
    
    # Read the input file and extract the content between the delimiters
    try:
        with open(input_file_path, 'r') as file:
            data = file.read()
    except FileNotFoundError:
        print(f"File not found: {input_file_path}")
        return
    
    # Extract content between ```cmake and ```
    start_delim = "```cmake"
    end_delim = "```"
    start_index = data.find(start_delim)
    end_index = data.find(end_delim, start_index + len(start_delim))
    
    if start_index == -1 or end_index == -1:
        print("Delimiters not found in the input file.")
        return
    
    cmake_content = data[start_index + len(start_delim):end_index].strip()
    
    # Get all subdirectories under builder_testbench
    variant_directories = [d for d in os.listdir(builder_testbench_dir) if os.path.isdir(os.path.join(builder_testbench_dir, d))]
    
    # Write the extracted cmake content to CMakeLists.txt in each subdirectory
    for variant in variant_directories:
        output_file_path = os.path.join(builder_testbench_dir, variant, 'CMakeLists.txt')
        
        try:
            with open(output_file_path, 'w') as output_file:
                output_file.write(cmake_content)
            print(f"Written CMake content to: {output_file_path}")
        except IOError as e:
            print(f"Failed to write to {output_file_path}: {e}")

def build_using_llm_cmake(parent_dir): 
    # Get the list of subdirectories under the parent directory
    try:
        for dir_name in os.listdir(parent_dir):
            dir_path = os.path.join(parent_dir, dir_name)
            
            # Ensure it is a directory
            if os.path.isdir(dir_path):
                try:
                    print(f"Running cmake build commands in directory: {dir_path}")
                    
                    # Run cmake to generate build files
                    cmake_command = f'cmake -S . -B build -G "Visual Studio 17 2022" -DVariant_name=' + dir_name
                    subprocess.run(cmake_command, cwd=dir_path, check=True, shell=True, capture_output=True, text=True)
                    # print("CMake configuration output:", result.stdout)
                    
                    # Build the project
                    build_command = f'cmake --build build'
                    subprocess.run(build_command, cwd=dir_path, check=True, shell=True, capture_output=True, text=True)
                    # print("Build output:", result.stdout)

                    print(f"Build succeeded in {dir_path} without errors.\n")

                except subprocess.CalledProcessError as e:
                    # Stop further execution and return failure with the directory name
                    failed_command = " ".join(cmake_command) if 'cmake' in str(e.cmd) else " ".join(build_command)
                    print(f"CMake Build failed for variant: {dir_name}")
                    print(f"Command which failed: {failed_command}")
                    # Check if e.stderr (from the build command) is empty using is_string_empty
                    if is_string_empty(e.stderr):
                        # print("stderr is empty, printing stdout instead:")
                        # print(e.stdout)  # Print stdout from the build command
                        return False, dir_name, e.stderr  # Return stdout instead of stderr
                    else:
                        print(f"Error log:\n{e.stderr}\n")
                        return False, dir_name, e.stderr
    finally:
        # Cleanup: Iterate over all subdirectories and delete the build directory if it exists
        for dir_name in os.listdir(parent_dir):
            dir_path = os.path.join(parent_dir, dir_name)
            
            # Ensure it is a directory
            if os.path.isdir(dir_path):
                build_dir = os.path.join(dir_path, 'build')
                if os.path.exists(build_dir):
                    shutil.rmtree(build_dir)
                    print(f"Deleted build directory inside: {dir_path}")


    return True, None, None

def is_string_empty(s: str) -> bool:
    # Strip all leading and trailing whitespace characters and check if the string is empty
    return len(s.strip()) == 0
