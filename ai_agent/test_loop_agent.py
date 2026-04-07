from openai import OpenAI
import json
import time
from datetime import datetime

from test_simple_agent import tools, execute_function_call

client = OpenAI()

def trip_planner_agentic_loop(user_message):
    """Enhanced trip planner with continuous tool calling loop"""
    messages = [
        {
            "role": "system", 
            "content": f"""Today is {datetime.today().strftime('%Y-%m-%d')}. You are a helpful trip planning assistant. Help users plan their trips by:
            1. Checking weather conditions for destinations
            2. Suggesting relevant points of interest based on preferences
            3. Purchasing tickets for attractions when requested

            IMPORTANT: Before doing anything else, you MUST confirm that the user has provided both:
            - Travel destination (required)
            - Travel dates (required)

            If either is missing, ask the user for the missing information before proceeding with any planning.

            Once both are provided, provide comprehensive advice and feel free to use multiple tools in sequence to give complete trip planning assistance.
            For example, you might check weather first, then suggest appropriate POIs based on conditions, and finally help purchase tickets for recommended attractions."""
        },
        {"role": "user", "content": user_message}
    ]
    
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        GREY_BG = "\033[48;5;252m\033[38;5;17m"
        RESET = "\033[0m"
        print(f"\n{GREY_BG}--- Context window ({len(messages)} messages) ---{RESET}")
        for msg in messages:
            role = msg["role"] if isinstance(msg, dict) else msg.role
            content = msg["content"] if isinstance(msg, dict) else msg.content
            print(f"{GREY_BG}[{role}]: {content}{RESET}")
        print(f"{GREY_BG}---{RESET}\n")

        completion = client.chat.completions.create(
            model="gpt-5.4-mini",
            messages=messages,
            tools=tools
        )
        
        assistant_message = completion.choices[0].message
        
        # Print assistant's message if it has content and no tool calls
        if assistant_message.content and not assistant_message.tool_calls:
            print("Assistant:", assistant_message.content)
        
        # Check if there are tool calls to execute
        if assistant_message.tool_calls:            
            # Add assistant message with tool calls to conversation
            messages.append(assistant_message)
            
            # Execute each tool call
            for tool_call in assistant_message.tool_calls:
                print(f"  → Calling: {tool_call.function.name}")
                result = execute_function_call(tool_call)
                print(f"  ← Result: {result}")
                
                # Add function result to messages
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result
                })

                time.sleep(1)
            
            # Continue the loop to get next response
            continue
        else:
            # No tool calls — output response and wait for user input
            messages.append(assistant_message)
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                break
            messages.append({"role": "user", "content": user_input})
    
    if iteration >= max_iterations:
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached. Ending conversation.")

if __name__ == "__main__":
    user_input = input("> ")
    trip_planner_agentic_loop(user_input)