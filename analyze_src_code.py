import os
import shutil
import gpt_api as gpt_api
import subprocess
from dotenv import load_dotenv
import re

load_dotenv()
# Get the API key from the environment variable
api_key = os.getenv("OPENAI_KEY")

def create_platform_src_code(variant_names):
    """
    Central function which calls all other helper functions in this file.
    """
    delete_build_dir_in_spl_output()
    # create a list of all variable- files in the spl_output directory
    variable_files = find_variable_files("spl_output")
    print(variable_files)
    gen_fail_flag = False
    # for each file in the above list
        # stitch file into prompt_platform.txt
        # send prompt_platform.txt to LLM
        # copy response to the original file location and remove variable- from the filename
    stitch_prompts_from_variable_files(variable_files, "prompts/prompt_platform.txt", "spl_output/prompts_responses/response_platform.txt")

    # for each item in variant_names list
        # build the variant
        # if build fails
            # identify which file to send to LLM
            # stitch file into feedback_prompt_platform_build.txt
            # send feedback to LLM
            # copy response to the identified file
            # build the variant AGAIN
        # if build succeeds
            # test the variant
            # if test fails
                # identify which file to send to LLM
                # stitch file into feedback_prompt_platform_test.txt
                # send feedback to LLM
                # copy response to the identified file
                # test the variant AGAIN
            # if test succeeds
                # continue to the next item in variant_names list
    max_feedback_attempts = 5
    for variant in variant_names:
        delete_build_dir_in_spl_output()
        # Initial build attempt outside the loop
        build_success, build_error = build_variant(variant)
  
        # If the build fails, enter the loop
        if not build_success:
            for attempts in range(max_feedback_attempts):
                print("Build Error: ", build_error)
                file_with_build_error = identify_file_with_error(build_error)
                stitch_feedback_prompt_platform_build(variant, build_error, file_with_build_error, "prompts/feedback_prompt_platform_build.txt")
                gpt_api.send_platformfeedback_prompt(api_key, "spl_output/prompts/feedback_prompt_platform_build.txt", "spl_output/prompts_responses/feedback_response_platform_build.txt")
                copy_llm_response_back_to_file("spl_output/prompts_responses/feedback_response_platform_build.txt", file_with_build_error)
                delete_build_dir_in_spl_output()
                # Attempt another build after applying feedback
                build_success, build_error = build_variant(variant)
                
                # Break the loop if the build succeeds
                if build_success:
                    print(f"Build successful after {attempts + 1} feedback attempts for variant {variant}")
                    break
            if not build_success:
                # Print statement for exceeding max build feedback attempts
                print(f"Max feedback build attempts reached: Build failed after {max_feedback_attempts} feedback attempts for variant {variant}")
                gen_fail_flag = True
                continue  # Skip testing if build failed
        elif build_success:
            print(f"Build successful after 0 feedback attempts for variant {variant}")
            failed_test, failed_test_log = test_variant(variant)
            if failed_test is not None:
                for attempts in range(max_feedback_attempts):
                    print(f"Test failed for variant {variant} in test {failed_test}")
                    # need to add logic here to identfy the file which contains the error which causes to test to fail
                    # search the failed_test string in all of the test_temp/variant folder and find the file which contains the test
                    test_file_with_error = identify_test_file_with_error(failed_test, f'spl_output/test_temp/{variant}')
                    print("Test file with error: ", test_file_with_error)
                    src_code_file_with_error = identify_src_code_file_with_error(test_file_with_error)
                    print("Source code file causing test error: ", src_code_file_with_error)
                    # search src_code_file_with_error in the spl_output directory and find its path
                    src_code_file_with_error_path = search_output_dir_for_file("spl_output", src_code_file_with_error, exclude_dirs=["spl_output/build", "spl_output/test_temp"])
                    stitch_feedback_prompt_platform_test(variant, failed_test, failed_test_log, src_code_file_with_error_path, test_file_with_error, "prompts/feedback_prompt_platform_test.txt")
                    # send the prompt to LLM
                    gpt_api.send_platformfeedback_prompt(api_key, "spl_output/prompts/feedback_prompt_platform_test.txt", "spl_output/prompts_responses/feedback_response_platform_test.txt")
                    # copy the response to the identified file
                    copy_llm_response_back_to_file("spl_output/prompts_responses/feedback_response_platform_test.txt", src_code_file_with_error_path)
                    # build the variant again
                    delete_build_dir_in_spl_output()
                    build_success, build_error = build_variant(variant)

                    if not build_success:
                        for build_attempts in range(max_feedback_attempts):
                            print("Build Error: ", build_error)
                            file_with_build_error = identify_file_with_error(build_error)
                            stitch_feedback_prompt_platform_build(variant, build_error, file_with_build_error, "prompts/feedback_prompt_platform_build.txt")
                            gpt_api.send_platformfeedback_prompt(api_key, "spl_output/prompts/feedback_prompt_platform_build.txt", "spl_output/prompts_responses/feedback_response_platform_build.txt")
                            copy_llm_response_back_to_file("spl_output/prompts_responses/feedback_response_platform_build.txt", file_with_build_error)
                            
                            # Attempt another build after applying feedback
                            delete_build_dir_in_spl_output()
                            build_success, build_error = build_variant(variant)
                            
                            # Break the loop if the build succeeds
                            if build_success:
                                print(f"Build successful after {build_attempts + 1} feedback attempts for variant {variant}")
                                break
                    if not build_success:
                        print(f"Max feedback build attempts reached: Build failed after {max_feedback_attempts} feedback attempts for variant {variant}")
                        print(f"Tests failed after {attempts + 1} feedback attempts for variant {variant}")
                        break
                    else: 
                        failed_test, failed_test_log = test_variant(variant)
                        if failed_test is None:
                            print(f"Tests successful after {attempts + 1} feedback attempts for variant {variant}")
                            break
                if not failed_test is None:
                    # Print statement for exceeding max test feedback attempts
                    print(f"Max feedback test attempts reached: Tests failed after {max_feedback_attempts} feedback attempts for variant {variant}")
                    gen_fail_flag = True
            else:
                print(f"Tests successful after 0 feedback attempts for variant {variant}")
      
    return gen_fail_flag

def search_output_dir_for_file(directory, filename, exclude_dirs=[]):
    """
    Searches the specified directory and its subdirectories for a file, excluding some subdirectories.

    Args:
    directory (str): The root directory where the search will start.
    filename (str): The name of the file to search for.
    exclude_dirs (list): A list of full or relative subdirectory paths to exclude from the search.

    Returns:
    str: The full path to the file if found, otherwise None.
    """
    # Normalize the excluded directories to their absolute paths
    exclude_dirs = [os.path.abspath(exclude) for exclude in exclude_dirs]

    for root, dirs, files in os.walk(directory):
        # Normalize the current directory to an absolute path
        current_dir = os.path.abspath(root)

        # Remove excluded directories from the dirs list if they're in the current directory
        dirs[:] = [d for d in dirs if os.path.abspath(os.path.join(root, d)) not in exclude_dirs]

        if filename in files:
            return os.path.join(root, filename)

    return None

def stitch_feedback_prompt_platform_test(variant_name, failed_test, failed_test_log, src_file_with_error, test_file_with_error, prompt_path):
    # Create destination directory if it doesn't exist
    output_dir = os.path.join('spl_output', os.path.dirname(prompt_path))
    os.makedirs(output_dir, exist_ok=True)

    # Copy the file to the spl_output directory
    dest_file_path = os.path.join(output_dir, os.path.basename(prompt_path))
    shutil.copy(prompt_path, dest_file_path)

    # Read the contents of the source and test files causing the error
    with open(src_file_with_error, 'r') as src_file:
        src_file_content = src_file.read()
    
    with open(test_file_with_error, 'r') as test_file:
        test_file_content = test_file.read()

    # Read the content of the copied prompt file
    with open(dest_file_path, 'r') as dest_file:
        dest_content = dest_file.read()

    # Replace the placeholders in the file
    dest_content = dest_content.replace('{{replace with source-code file causing test error}}', src_file_content)
    dest_content = dest_content.replace('{{replace with variant for which error occurs}}', variant_name)
    dest_content = dest_content.replace('{{replace with failed test name}}', failed_test)
    dest_content = dest_content.replace('{{replace with test file with error}}', test_file_content)
    dest_content = dest_content.replace('{{replace with failed test execution log}}', failed_test_log)

    # Write the modified content back to the copied file
    with open(dest_file_path, 'w') as dest_file:
        dest_file.write(dest_content)

    print(f"Prompt file updated and saved at: {dest_file_path}")

def identify_src_code_file_with_error(test_file_with_error):
    # Extract the filename from the full path
    filename = os.path.basename(test_file_with_error)
    
    # Remove the prefix "test_" from the filename
    src_file = filename.removeprefix("test_")
    
    # Remove the file extension
    src_file_no_ext = os.path.splitext(src_file)[0]
    
    # Add ".c" extension to the modified filename
    modified_filename = src_file_no_ext + ".c"
    
    # Return the modified filename with ".c" extension
    return modified_filename

def identify_test_file_with_error(failed_test, search_directory):
    # Loop through all files in the specified directory and subdirectories
    for root, dirs, files in os.walk(search_directory):
        for file in files:
            file_path = os.path.join(root, file)
            try:
                # Open each file in read mode and search for the string
                with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                    for line_number, line in enumerate(f, 1):
                        if failed_test in line:
                            return file_path  # Return the file path when the string is found
            except Exception as e:
                # Skip any files that cannot be opened/read
                print(f"Error opening/reading file {file_path}: {e}")
                continue
    
    return None  # Return None if the string is not found in any file

def test_variant(variant):
    # Define the directory path
    directory = os.path.join('spl_output', 'build', 'Debug')
    
    # Check if the directory exists
    if not os.path.exists(directory):
        print(f"The directory {directory} does not exist.")
        return
    
    # Get all files in the directory
    files = os.listdir(directory)
    
    # Filter executable files containing the word "test" (case-insensitive)
    exe_files = [f for f in files if f.lower().endswith('.exe') and 'test' in f.lower()]
    
    if not exe_files:
        print(f"No test executables found in {directory}.")
        return
    
    # Execute each test executable and capture output
    for exe in exe_files:
        exe_path = os.path.join(directory, exe)
        print(f"Running {exe_path}...")
        try:
            # Execute the file and capture the output and errors as binary
            result = subprocess.run([exe_path], capture_output=True, text=False)  # text=False for binary capture
            
            # Safely decode stdout and stderr using 'replace' for invalid characters
            stdout = result.stdout.decode('utf-8', errors='replace')
            stderr = result.stderr.decode('utf-8', errors='replace')
            
            # Print the output and any error messages
            # print(f"Output of {exe}:\n{stdout}")
            if stderr:
                print(f"Error while running {exe}:\n{stderr}")
            
            if detect_test_failure(stdout):
                failed_test_name_raw, failed_test_log = detect_failed_test(stdout)
                print(f"Failed test name raw: {failed_test_name_raw}, Failed test log: {failed_test_log}")
                return extract_failed_test_name(failed_test_name_raw), failed_test_log   

        except Exception as e:
            print(f"Failed to execute {exe}: {e}")
    return None, None

def detect_test_failure(test_log):
    if "[  FAILED  ]" in test_log:
        return True
    else:
        return False


def extract_failed_test_name(input_string):
    # Check if there's a period in the string and split at the first period
    if '.' in input_string:
        after_dot = input_string.split('.', 1)[-1]
    else:
        after_dot = input_string
    
    # This pattern will match only valid characters (alphabetic characters and underscores)
    pattern = r'[a-zA-Z_]+'
    
    # Filter out any invalid characters by matching valid ones and joining them back in their original order
    result = ''.join(re.findall(pattern, after_dot))
    
    return result

def detect_failed_test(input_string: str) -> str:
    # Define the start and end delimiters
    start_delimiter = "[ RUN      ]"
    end_delimiter = "[  FAILED  ]"
    
    current_pos = 0
    
    while True:
        # Find the first occurrence of the end delimiter starting from current position
        end_index = input_string.find(end_delimiter, current_pos)
        
        # If no end delimiter is found, we're done
        if end_index == -1:
            return None, None
        
        # Search backward from the found end delimiter to find the nearest start delimiter
        start_index = input_string.rfind(start_delimiter, 0, end_index)
        
        # If no start delimiter is found before the end delimiter, skip this end delimiter and keep searching
        if start_index == -1:
            current_pos = end_index + len(end_delimiter)
            continue
        
        # Move the start_index past the start delimiter for extraction
        start_index = input_string.find(start_delimiter, start_index) + len(start_delimiter)
        
        # Check that there are no additional start or end delimiters in the range between start and end delimiters
        if input_string.find(start_delimiter, start_index, end_index) == -1 and input_string.find(end_delimiter, start_index, end_index) == -1:
            print(f"Test Log before extraction between delims: {input_string[start_index:end_index]}")
            # Extract the text between the start and end delimiters
            extracted_text = input_string[start_index:end_index].strip()
            print(f"Test Log after extraction between delims: {extracted_text}")
            # Split the extracted text by line breaks
            lines = extracted_text.splitlines()
            
            # Get the first line
            first_line = lines[0] if lines else None
            
            # Get the rest of the lines (from the second line onwards)
            remaining_lines = "\n".join(lines[1:]) if len(lines) > 1 else None
            print(f"Test Log lines from second line after delim: {remaining_lines}")
            return first_line, remaining_lines
        
        # Move the current position past the current end delimiter to continue searching
        current_pos = end_index + len(end_delimiter)



def copy_llm_response_back_to_file(response_file_path, file_with_error):
    try:
        # Reading the response file
        with open(response_file_path, 'r') as response_file:
            response_content = response_file.read()
        
        # Extracting content between ```c and ```
        start_delimiter = "```c"
        end_delimiter = "```"
        
        start_index = response_content.find(start_delimiter)
        end_index = response_content.find(end_delimiter, start_index + len(start_delimiter))
        
        if start_index == -1 or end_index == -1:
            raise ValueError("Delimiters not found in the response file")
        
        # Extracting the relevant content
        extracted_code = response_content[start_index + len(start_delimiter):end_index].strip()
        
        # Replacing the entire content of the file_with_error
        with open(file_with_error, 'w') as error_file:
            error_file.write(extracted_code)
        
        print(f"Content successfully replaced in {file_with_error}")
    
    except Exception as e:
        print(f"An error occurred: {e}")

def stitch_feedback_prompt_platform_build(variant_name, build_error, file_with_build_error, prompt_path):
    # Step 1: Copy the file from prompt_path to spl_output directory
    output_dir = "spl_output/prompts"
    os.makedirs(output_dir, exist_ok=True)
    
    # Determine the destination file path inside the spl_output folder
    output_file_path = os.path.join(output_dir, os.path.basename(prompt_path))
    
    # Copy the prompt_path file into spl_output directory
    shutil.copy(prompt_path, output_file_path)
    
    # Step 2: Read the content of file_with_build_error
    with open(file_with_build_error, 'r') as error_file:
        error_file_content = error_file.read()
    
    # Step 3: Read the contents of the file copied to spl_output
    with open(output_file_path, 'r') as output_file:
        output_content = output_file.read()
    
    # Step 4: Replace "{{replace with variable file with error}}" with file_with_build_error content
    output_content = output_content.replace("{{replace with variable file with error}}", error_file_content)
    
    # Step 5: Replace "{{replace with build error}}" with build_error string
    output_content = output_content.replace("{{replace with build error}}", build_error)

    output_content = output_content.replace("{{replace with variant name which error occurs}}", variant_name)
    
    # Step 6: Extract the filename from the file_with_build_error path to search for the "variable-{filename}"
    file_with_error_name = os.path.basename(file_with_build_error)
    variable_file_pattern = f"variable-{file_with_error_name}"
    print("Variable file pattern: ", variable_file_pattern)
    
    # Search for the variable-{filename} file in spl_output directory
    for root, dirs, files in os.walk("spl_output"):
        for filename in files:
            if re.match(variable_file_pattern, filename):
                # Read the content of this matched file
                variable_file_path = os.path.join(root, filename)
                with open(variable_file_path, 'r') as variable_file:
                    cloned_variable_content = variable_file.read()
                
                # Replace "{{replace with cloned variable file}}" with this content
                output_content = output_content.replace("{{replace with cloned variable file}}", cloned_variable_content)
                break

    # Step 7: Write the modified content back to the copied file in spl_output
    with open(output_file_path, 'w') as output_file:
        output_file.write(output_content)
    
    print(f"Updated file written to: {output_file_path}")


def identify_file_with_error(error_msg):
    # Regular expression to find the first file path with line and column numbers
    pattern = r"(C:\\Users\\.*?spl_output.*?\.\w+)\(\d+,\d+\)"
    
    # Search for the first occurrence
    match = re.search(pattern, error_msg)
    
    if match:
        # Extract the full file path with line/column numbers
        full_path_with_location = match.group(1)
        
        # Extract the part starting from "spl_output"
        extracted_path = re.search(r"spl_output.*", full_path_with_location)
        
        if extracted_path:
            # Replace backslashes with forward slashes for the desired format
            return extracted_path.group(0).replace("\\", "/")
    
    return None

def find_variable_files(directory):
    """
    Finds all files in the specified directory whose name contains 'variable-'
    and whose extension is not '.txt'.
    
    Parameters:
        directory (str): The path to the directory to search in.
        
    Returns:
        list: A list of file paths that match the criteria.
    """
    matching_files = []
    
    # Walk through all directories and files recursively
    for root, dirs, files in os.walk(directory):
        for filename in files:
            # Check if the file name contains 'variable-' and does not end with '.txt'
            if "variable-" in filename and not filename.endswith(".txt"):
                file_path = os.path.join(root, filename)
                matching_files.append(file_path)
    
    return matching_files

def stitch_prompts_from_variable_files(file_list, prompt_platform_file, response_file_path):
    """
    Iterates over the list of files, reads the content of each file, stitches the 
    platform gen prompt together and sends it to LLM. 

    Parameters:
        file_list (list): A list of file paths to read content from.
        prompt_platform_file (str): The path to the prompt file to which content will be stitched.
        response_file_path (str): The path to the file in which the LLM response will be stored.
    """
    
    # Create the destination directory if it doesn't exist
    destination_dir = 'spl_output/prompts'
    os.makedirs(destination_dir, exist_ok=True)

    # Iterate over the list of files and replace placeholders in the target content
    for file_path in file_list:
        # Define the destination file path
        dest_prompt_platform_file = os.path.join(destination_dir, os.path.basename(prompt_platform_file))

        # Copy the prompt platform file to the destination directory
        shutil.copyfile(prompt_platform_file, dest_prompt_platform_file)

        # Read the content of the copied target file
        with open(dest_prompt_platform_file, 'r') as tf:
            target_content = tf.read()

        # Read the content of the current file in the list
        with open(file_path, 'r') as f:
            file_content = f.read()

        # Replace the placeholder with the content of the current file
        target_content = target_content.replace("{{replace with variable file content}}", file_content, 1)

        # Write the updated content back to the copied target file
        with open(dest_prompt_platform_file, 'w') as tf:
            tf.write(target_content)

        print(f"Replacements done in {dest_prompt_platform_file}")

        # Send the stitched prompt to LLM
        gpt_api.send_platformgen_prompt(api_key, dest_prompt_platform_file, response_file_path)

        # Copy the LLM response to the original file location and remove 'variable-' from the filename
        copy_llmresponse_to_file(response_file_path, file_path)


def copy_llmresponse_to_file(response_file_path, file_path):
    """
    Copies the response from LLM to the original file location and removes 'variable-' from the filename.

    Parameters:
        file_path (str): The path to the original file.
        target_file (str): The path to the target file where the LLM response is stored.
    """
    # Read the content of the target file
    with open(response_file_path, 'r') as rf:
        response_content = rf.read()
    
    # Extract content between ```cmake and ```
    start_delim = "```c"
    end_delim = "```"
    start_index = response_content.find(start_delim)
    end_index = response_content.find(end_delim, start_index + len(start_delim))
    
    if start_index == -1 or end_index == -1:
        print("Delimiters not found in the input file.")
        return
    
    response_content = response_content[start_index + len(start_delim):end_index].strip()

    # Extract the file name from the original file path
    file_name = os.path.basename(file_path)

    # Remove 'variable-' from the file name
    new_file_name = file_name.replace("variable-", "")

    # Construct the new file path with the updated file name
    new_file_path = os.path.join(os.path.dirname(file_path), new_file_name)

    # Write the response content to the new file
    with open(new_file_path, "w") as nf:
        nf.write(response_content)
    print(f"Response copied to {new_file_path}")

def delete_build_dir_in_spl_output():
    cwd = os.path.join(os.getcwd(), 'spl_output')
    # Define the build directory path
    build_dir = os.path.join(cwd, 'build')

    # Check if the build directory exists and delete it
    if os.path.exists(build_dir) and os.path.isdir(build_dir):
        try:
            shutil.rmtree(build_dir)
            print(f"Build directory '{build_dir}' deleted.")
        except Exception as e:
            print(f"Error deleting build directory: {e}")

def build_variant(variant):
    try:
        # Define the working directory as 'spl_output' in the current directory
        cwd = os.path.join(os.getcwd(), 'spl_output')

        # Run the first cmake command
        command1 = f'cmake -S . -B build -G "Visual Studio 17 2022" -DVariant_name={variant}'
        result1 = subprocess.run(command1, shell=True, cwd=cwd, capture_output=True, text=True)

        # Check if the first command failed
        if result1.returncode != 0:
            print("Error of command1 empty: ", is_string_empty(result1.stderr))
            if(is_string_empty(result1.stderr)):
                return False, result1.stdout

        # Run the second cmake command
        command2 = 'cmake --build build'
        result2 = subprocess.run(command2, shell=True, cwd=cwd, capture_output=True, text=True)

        # Check if the second command failed
        if result2.returncode != 0:
            print("Error of command2 empty: ", is_string_empty(result2.stderr))
            if(is_string_empty(result2.stderr)):
                return False, result2.stdout

        # If both commands are successful, return True
        return True, None

    except Exception as e:
        # Return False with error message in case of an exception
        print("Exception message empty: ", is_string_empty(str(e)))
        return False, str(e)

def is_string_empty(s: str) -> bool:
    # Strip all leading and trailing whitespace characters and check if the string is empty
    return len(s.strip()) == 0
