from openai import OpenAI
import os

SystemPrompt = """
Your task is to help in migrating several CMakeLists.txt files for cloned software variants into a single file for a software product line. 
Only one of these variants is going to be built from the file you generate at a time. 
You must include all the common dependencies from the input cloned variants into the final CMakeLists.txt file, so that the generated file can build the selected variant without errors. 
main.c file should always be excluded from all the test executables of all the variants.  
Knowledge cutoff: 2023-10 Current date: 2024-10-04
"""

# Below prompt also working with one iteration of build feedback 
SystemPromptPlatformGen = """
Your task is to help in migrating several cloned software variants into a software product line using conditional compilation directives. 
Pay special attention to the instructions which the user has provided.  
Knowledge cutoff: 2023-10 Current date: 2024-10-03
"""

def send_cmake_prompt(api_key, prompt_file_path, response_file_path):
    # Initialize the OpenAI client
    client = OpenAI(api_key=api_key)

    # Read the file contents
    with open(prompt_file_path, 'r') as file:
        file_content = file.read()

    # Use the file contents as the user's message content
    completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.1,
        messages=[
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": file_content}
        ]
    )

    # Get the response from the assistant
    response_content = completion.choices[0].message.content

    # Print the response to the terminal
    print("Assistant: " + response_content)

    # Write the response to a file called response.txt
    with open(response_file_path, "w") as response_file:
        response_file.write(response_content)


def send_cmakefeedback_prompt(api_key, feedback_prompt_file_path, response_file_path):
    # Initialize the OpenAI client
    client = OpenAI(api_key=api_key)

    # Read the file contents
    with open(feedback_prompt_file_path, 'r') as file:
        file_content = file.read()

    # Use the file contents as the user's message content
    completion = client.chat.completions.create(
        model="gpt-4o",
        temperature=0.1,
        messages=[
            {"role": "system", "content": SystemPrompt},
            {"role": "user", "content": file_content}
        ]
    )

    # Get the response from the assistant
    response_content = completion.choices[0].message.content

    # Print the response to the terminal
    print("Assistant: " + response_content)

    # Write the response to a file called response.txt
    with open(response_file_path, "w") as response_file:
        response_file.write(response_content)

def send_platformgen_prompt(api_key, prompt_file_path, response_file_path):
    # Initialize the OpenAI client
    client = OpenAI(api_key=api_key)

    # Read the file contents
    with open(prompt_file_path, 'r') as file:
        file_content = file.read()

    # Use the file contents as the user's message content
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SystemPromptPlatformGen},
            {"role": "user", "content": file_content}
        ]
    )

    # Get the response from the assistant
    response_content = completion.choices[0].message.content

    # Print the response to the terminal
    print("Assistant: " + response_content)

    # Write the response to a file called response.txt
    with open(response_file_path, "w") as response_file:
        response_file.write(response_content)

def send_platformfeedback_prompt(api_key, feedback_prompt_file_path, response_file_path):
    # Initialize the OpenAI client
    client = OpenAI(api_key=api_key)

    # Read the file contents
    with open(feedback_prompt_file_path, 'r') as file:
        file_content = file.read()

    # Use the file contents as the user's message content
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SystemPromptPlatformGen},
            {"role": "user", "content": file_content}
        ]
    )

    # Get the response from the assistant
    response_content = completion.choices[0].message.content

    # Print the response to the terminal
    print("Assistant: " + response_content)

    # Write the response to a file called response.txt
    with open(response_file_path, "w") as response_file:
        response_file.write(response_content)




# send_cmake_prompt(api_key, "prompt_cmake.txt")
# send_cmakefeedback_prompt(api_key, "feedback_prompt_cmake.txt")

# send_platformgen_prompt(api_key, "prompt_platform.txt")
# send_platformfeedback_prompt(api_key, "feedback_prompt_platform.txt")
