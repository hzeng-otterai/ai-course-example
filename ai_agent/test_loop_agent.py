import anthropic
import json
import time
from datetime import datetime

from test_simple_agent import tools, execute_function_call

client = anthropic.Anthropic()

def trip_planner_agentic_loop(user_message):
    """Enhanced trip planner with continuous tool calling loop"""
    system = f"""Today is {datetime.today().strftime('%Y-%m-%d')}. You are a helpful trip planning assistant. Help users plan their trips by:
            1. Checking weather conditions for destinations
            2. Suggesting relevant points of interest based on preferences
            3. Purchasing tickets for attractions when requested

            IMPORTANT: Before doing anything else, you MUST confirm that the user has provided both:
            - Travel destination (required)
            - Travel dates (required)

            If either is missing, ask the user for the missing information before proceeding with any planning.

            Once both are provided, provide comprehensive advice and feel free to use multiple tools in sequence to give complete trip planning assistance.
            For example, you might check weather first, then suggest appropriate POIs based on conditions, and finally help purchase tickets for recommended attractions."""

    messages = [{"role": "user", "content": user_message}]

    max_iterations = 10
    iteration = 0

    GREY_BG = "\033[48;5;252m\033[38;5;17m"
    RESET = "\033[0m"

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")

        print(f"\n{GREY_BG}--- Context window ({len(messages) + 1} messages) ---{RESET}")
        print(f"{GREY_BG}[function_call_definitions]: {json.dumps([t['name'] for t in tools])}{RESET}")
        print(f"{GREY_BG}[system]: {system}{RESET}")
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if isinstance(content, str):
                print(f"{GREY_BG}[{role}]: {content}{RESET}")
            elif isinstance(content, list):
                has_text = any(not isinstance(b, dict) and b.type == "text" for b in content)
                if not has_text:
                    print(f"{GREY_BG}[{role}]:{RESET}")
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "tool_result":
                            print(f"{GREY_BG}[{role} (tool_result id={block['tool_use_id']})]: {block['content']}{RESET}")
                    else:
                        if block.type == "text":
                            print(f"{GREY_BG}[{role}]: {block.text}{RESET}")
                        elif block.type == "tool_use":
                            print(f"{GREY_BG}  ↳ tool_use (id={block.id}): {block.name}({json.dumps(block.input)}){RESET}")
        print(f"{GREY_BG}---{RESET}\n")

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks = [b for b in response.content if b.type == "text"]

        if text_blocks and not tool_use_blocks:
            print("Assistant:", text_blocks[0].text)

        if tool_use_blocks:
            messages.append({"role": "assistant", "content": response.content})

            tool_results = []
            for tool_call in tool_use_blocks:
                print(f"  → Calling: {tool_call.name}")
                result = execute_function_call(tool_call)
                print(f"  ← Result: {result}")
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_call.id,
                    "content": result
                })
                time.sleep(1)

            messages.append({"role": "user", "content": tool_results})
            continue
        else:
            messages.append({"role": "assistant", "content": response.content})
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                break
            messages.append({"role": "user", "content": user_input})

    if iteration >= max_iterations:
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached. Ending conversation.")


if __name__ == "__main__":
    user_input = input("> ")
    trip_planner_agentic_loop(user_input)
