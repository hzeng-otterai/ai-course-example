import anthropic
import json
import re
import time
from datetime import datetime

from test_simple_agent_more_functions import tools as travel_tools, execute_function_call

client = anthropic.Anthropic()

GREY_BG = "\033[48;5;252m\033[38;5;17m"
RESET = "\033[0m"


# ── Skill loading ─────────────────────────────────────────────────────────────

def parse_skill_file(filepath):
    with open(filepath) as f:
        content = f.read()
    match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
    if not match:
        return {"name": filepath, "description": "", "body": content}
    front, body = match.group(1), match.group(2).strip()
    name_match = re.search(r'^name:\s*(.+)$', front, re.MULTILINE)
    desc_match = re.search(r'^description:\s*(.+)$', front, re.MULTILINE)
    return {
        "name": name_match.group(1).strip() if name_match else filepath,
        "description": desc_match.group(1).strip() if desc_match else "",
        "body": body,
    }


SKILLS = [parse_skill_file("flight-ticket-finder.md")]

load_skill_tool = {
    "name": "load_skill",
    "description": "Load the full instructions for a named skill when you need detailed guidance to handle a user request.",
    "input_schema": {
        "type": "object",
        "properties": {
            "skill_name": {
                "type": "string",
                "description": "The name of the skill to load full instructions for"
            }
        },
        "required": ["skill_name"]
    }
}

tools = [load_skill_tool] + travel_tools


def execute_load_skill(skill_name):
    for skill in SKILLS:
        if skill["name"] == skill_name:
            return f"[Skill: {skill['name']}]\n\n{skill['body']}"
    return f"Skill '{skill_name}' not found. Available: {[s['name'] for s in SKILLS]}"


def execute_tool(tool_call):
    if tool_call.name == "load_skill":
        return execute_load_skill(tool_call.input["skill_name"])
    return execute_function_call(tool_call)


# ── Context window display ────────────────────────────────────────────────────

def print_context_window(system, messages):
    print(f"\n{GREY_BG}--- Context window ({len(messages) + 1} messages) ---{RESET}")
    for t in tools:
        params = list(t["input_schema"].get("properties", {}).keys())
        required = t["input_schema"].get("required", [])
        param_str = ", ".join(f"{p}{'*' if p in required else '?'}" for p in params)
        print(f"{GREY_BG}[function_call_definition] {t['name']}({param_str}) — {t['description']}{RESET}")
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


# ── Compression ───────────────────────────────────────────────────────────────

MESSAGE_THRESHOLD = 100


def _has_pending_tool_use(messages):
    if not messages:
        return False
    last = messages[-1]
    if last["role"] != "assistant":
        return False
    content = last.get("content", [])
    if isinstance(content, list):
        return any(
            (isinstance(b, dict) and b.get("type") == "tool_use") or
            (hasattr(b, "type") and b.type == "tool_use")
            for b in content
        )
    return False


def compress_if_needed(messages, original_user_input, threshold=MESSAGE_THRESHOLD):
    if len(messages) < threshold:
        return messages
    if _has_pending_tool_use(messages):
        print("[compress] Skipping — pending tool_use in last assistant message.")
        return messages

    print(f"[compress] Compressing {len(messages)} messages into summary...")

    transcript_lines = []
    for msg in messages:
        role = msg["role"]
        content = msg["content"]
        if isinstance(content, str):
            transcript_lines.append(f"{role.upper()}: {content}")
        elif isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "tool_result":
                        transcript_lines.append(f"TOOL_RESULT: {block['content']}")
                elif hasattr(block, "type"):
                    if block.type == "text":
                        transcript_lines.append(f"{role.upper()}: {block.text}")
                    elif block.type == "tool_use":
                        transcript_lines.append(f"TOOL_USE: {block.name}({json.dumps(block.input)})")

    transcript = "\n".join(transcript_lines)

    try:
        summary_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=512,
            messages=[{"role": "user", "content": (
                "Summarize this travel planning conversation in 200-300 words. "
                "Include: the user's goal, what was accomplished (confirmed bookings, "
                "retrieved data), key facts (dates, prices, names), and what remains to do.\n\n"
                f"<conversation>\n{transcript}\n</conversation>"
            )}]
        )
        summary_text = summary_response.content[0].text
    except Exception as e:
        print(f"[compress] Summarization failed ({e}), keeping original messages.")
        return messages

    compressed = [{"role": "user", "content": (
        f"[Original request]: {original_user_input}\n\n"
        f"[Conversation summary so far]:\n{summary_text}"
    )}]
    print(f"[compress] Compressed {len(messages)} → {len(compressed)} messages.")
    return compressed


# ── Agentic loop ──────────────────────────────────────────────────────────────

def agentic_loop(user_message):
    skills_summary = "\n".join(f"- {s['name']}: {s['description']}" for s in SKILLS)

    system = f"""Today is {datetime.today().strftime('%Y-%m-%d')}. You are a helpful travel assistant.

You have access to specialized skills. When a user request matches a skill, call load_skill first to get the full instructions before proceeding.

Available skills:
{skills_summary}

For requests not covered by a skill, use your available tools directly and apply sensible defaults."""

    messages = [{"role": "user", "content": user_message}]

    max_iterations = 10
    iteration = 0

    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        messages = compress_if_needed(messages, user_message)
        print_context_window(system, messages)

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
                result = execute_tool(tool_call)
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
    agentic_loop(user_input)
