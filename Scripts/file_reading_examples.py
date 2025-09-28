#!/usr/bin/env python3
"""
Examples of reading files and saving as strings
"""

import os
from pathlib import Path


def read_file_method1(file_path):
    """Method 1: Using open() with read()"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        return content
    except FileNotFoundError:
        return "File not found!"
    except Exception as e:
        return f"Error: {e}"


def read_file_method2(file_path):
    """Method 2: Using pathlib (modern Python)"""
    try:
        content = Path(file_path).read_text(encoding='utf-8')
        return content
    except FileNotFoundError:
        return "File not found!"
    except Exception as e:
        return f"Error: {e}"


def read_file_lines(file_path):
    """Read file and return as list of lines"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        return lines
    except FileNotFoundError:
        return ["File not found!"]
    except Exception as e:
        return [f"Error: {e}"]


def read_file_with_strip(file_path):
    """Read file and strip whitespace"""
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read().strip()
        return content
    except FileNotFoundError:
        return "File not found!"
    except Exception as e:
        return f"Error: {e}"


def main():
    # Example file path
    file_path = "article_sim_trials/iter_2/system_prompt.txt"
    
    print("=== Different Ways to Read Files ===\n")
    
    # Method 1: Basic read
    print("Method 1 - Basic read():")
    content1 = read_file_method1(file_path)
    print(f"Length: {len(content1)} characters")
    print(f"First 100 chars: {content1[:100]}...\n")
    
    # Method 2: Using pathlib
    print("Method 2 - Using pathlib:")
    content2 = read_file_method2(file_path)
    print(f"Length: {len(content2)} characters")
    print(f"First 100 chars: {content2[:100]}...\n")
    
    # Method 3: Read as lines
    print("Method 3 - Read as lines:")
    lines = read_file_lines(file_path)
    print(f"Number of lines: {len(lines)}")
    print(f"First line: {lines[0].strip()}\n")
    
    # Method 4: Read with strip
    print("Method 4 - Read with strip():")
    content4 = read_file_with_strip(file_path)
    print(f"Length: {len(content4)} characters")
    print(f"First 100 chars: {content4[:100]}...\n")
    
    # Practical example: Load system prompt for ChatGPT
    print("=== Practical Example: Loading System Prompt ===")
    system_prompt = read_file_method1(file_path)
    
    if system_prompt and not system_prompt.startswith("File not found"):
        print("✅ System prompt loaded successfully!")
        print(f"📄 Prompt length: {len(system_prompt)} characters")
        print(f"📝 First line: {system_prompt.split('\\n')[0]}")
        
        # You can now use this in your ChatGPT calls
        # from basic_chatgpt import BasicChatGPT
        # chatgpt = BasicChatGPT()
        # response = chatgpt.chat_with_system_prompt(system_prompt, "Your question here")
    else:
        print("❌ Failed to load system prompt")


if __name__ == "__main__":
    main()
