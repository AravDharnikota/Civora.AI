#!/usr/bin/env python3
"""
Basic OpenAI ChatGPT-4-0613 Implementation
A simple script to interact with OpenAI's ChatGPT-4-0613 model
"""

import os
import sys
from openai import OpenAI
from typing import Optional
from dotenv import load_dotenv


class BasicChatGPT:
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the ChatGPT client
        
        Args:
            api_key: OpenAI API key. If not provided, will try to get from environment variable OPENAI_API_KEY
        """
        # Load .env file if it exists
        load_dotenv()
        
        if api_key:
            self.client = OpenAI(api_key=api_key)
        else:
            # Try to get API key from environment variable
            api_key = os.getenv('OPENAI_API_KEY')
            if not api_key:
                raise ValueError(
                    "OpenAI API key not provided. Either pass it as parameter or set OPENAI_API_KEY environment variable"
                )
            self.client = OpenAI(api_key=api_key)
    
    def chat(self, message: str, model: str = "gpt-4-0613", max_tokens: int = 1000, temperature: float = 0.7) -> str:
        """
        Send a message to ChatGPT and get response
        
        Args:
            message: The user message to send
            model: The model to use (default: gpt-4-0613)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 to 1.0)
            
        Returns:
            The assistant's response
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "user", "content": message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def chat_with_system_prompt(self, system_prompt: str, user_message: str, 
                              model: str = "gpt-4-0613", max_tokens: int = 1000, 
                              temperature: float = 0.7) -> str:
        """
        Send a message with a system prompt to ChatGPT
        
        Args:
            system_prompt: The system prompt to set context
            user_message: The user message to send
            model: The model to use (default: gpt-4-0613)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 to 1.0)
            
        Returns:
            The assistant's response
        """
        try:
            response = self.client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            return f"Error: {str(e)}"
    
    def interactive_chat(self, model: str = "gpt-4-0613", max_tokens: int = 1000, temperature: float = 0.7):
        """
        Start an interactive chat session
        
        Args:
            model: The model to use (default: gpt-4-0613)
            max_tokens: Maximum tokens in response
            temperature: Response randomness (0.0 to 1.0)
        """
        print("🤖 Basic ChatGPT-4-0613 Interactive Chat")
        print("Type 'quit', 'exit', or 'bye' to end the conversation")
        print("Type 'clear' to clear conversation history")
        print("-" * 50)
        
        conversation_history = []
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("👋 Goodbye!")
                    break
                
                if user_input.lower() == 'clear':
                    conversation_history = []
                    print("🧹 Conversation history cleared!")
                    continue
                
                if not user_input:
                    continue
                
                # Add user message to history
                conversation_history.append({"role": "user", "content": user_input})
                
                # Get response from ChatGPT
                response = self.client.chat.completions.create(
                    model=model,
                    messages=conversation_history,
                    max_tokens=max_tokens,
                    temperature=temperature
                )
                
                assistant_response = response.choices[0].message.content
                
                # Add assistant response to history
                conversation_history.append({"role": "assistant", "content": assistant_response})
                
                print(f"🤖 ChatGPT: {assistant_response}")
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")


def main():
    """Main function to demonstrate usage"""
    try:
        # Initialize ChatGPT client
        chatgpt = BasicChatGPT()
        
        # Example 1: Simple chat
        print("=== Example 1: Simple Chat ===")
        response = chatgpt.chat("Hello! Can you tell me a fun fact about space?")
        print(f"Response: {response}\n")
        
        # Example 2: Chat with system prompt
        print("=== Example 2: Chat with System Prompt ===")
        system_prompt = "You are a helpful assistant that explains complex topics in simple terms."
        response = chatgpt.chat_with_system_prompt(
            system_prompt, 
            "Explain quantum computing in simple terms"
        )
        print(f"Response: {response}\n")
        
        # Example 3: Interactive chat (uncomment to use)
        # print("=== Example 3: Interactive Chat ===")
        # chatgpt.interactive_chat()
        
    except ValueError as e:
        print(f"❌ Configuration Error: {e}")
        print("\nTo fix this:")
        print("1. Set your OpenAI API key as an environment variable:")
        print("   export OPENAI_API_KEY='your-api-key-here'")
        print("2. Or create a .env file with:")
        print("   OPENAI_API_KEY=your-api-key-here")
        print("3. Or pass it directly when creating the BasicChatGPT instance:")
        print("   chatgpt = BasicChatGPT(api_key='your-api-key-here')")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()