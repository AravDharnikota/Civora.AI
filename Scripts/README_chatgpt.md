# Basic ChatGPT-4-0613 Usage Guide

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set your OpenAI API key:
```bash
export OPENAI_API_KEY='your-api-key-here'
```

## Usage

### Basic Usage
```python
from basic_chatgpt import BasicChatGPT

# Initialize
chatgpt = BasicChatGPT()

# Simple chat
response = chatgpt.chat("Hello! Tell me a joke.")
print(response)
```

### With System Prompt
```python
system_prompt = "You are a helpful coding assistant."
response = chatgpt.chat_with_system_prompt(
    system_prompt, 
    "How do I create a Python class?"
)
print(response)
```

### Interactive Chat
```python
# Start interactive session
chatgpt.interactive_chat()
```

### Custom Parameters
```python
response = chatgpt.chat(
    "Explain machine learning",
    model="gpt-4-0613",
    max_tokens=500,
    temperature=0.3
)
```

## Features

- ✅ Simple chat interface
- ✅ System prompt support
- ✅ Interactive chat mode
- ✅ Error handling
- ✅ Customizable parameters (model, max_tokens, temperature)
- ✅ Conversation history in interactive mode
- ✅ Clear conversation history option

## Available Models

- `gpt-4-0613` (default)
- `gpt-4-turbo`
- `gpt-3.5-turbo`
- And other OpenAI models
