"""
Subagent pattern: isolate context by splitting 23 tools into 6 domain specialists.

Without subagents (test_loop_agent.py):
  Orchestrator context = system + messages + ALL 23 tool defs + every tool call & result
  → context grows with every iteration across all domains

With subagents (this file):
  Orchestrator context = system + messages + 6 delegation tools + subagent summaries only
  Each subagent context = isolated per-request loop with 3–5 domain tools only
  → orchestrator stays small; subagent contexts are short-lived and never merged back
"""

import anthropic
import json
from datetime import datetime
from test_simple_agent_more_functions import tools as all_tools, execute_function_call

client = anthropic.Anthropic()

# ── Domain tool subsets ────────────────────────────────────────────────────────

TRANSPORTATION_TOOL_NAMES = {"search_flights", "book_flight", "search_trains", "book_train", "rent_car"}
ACCOMMODATION_TOOL_NAMES  = {"search_hotels", "book_hotel", "check_hotel_availability"}
DINING_TOOL_NAMES         = {"search_restaurants", "make_restaurant_reservation", "get_food_recommendations"}
PLANNING_TOOL_NAMES       = {"create_itinerary", "calculate_budget", "get_packing_suggestions", "get_visa_requirements"}
LOCAL_INFO_TOOL_NAMES     = {"convert_currency", "translate_phrase", "get_local_customs", "get_emergency_contacts", "find_nearby_pharmacy"}
EVENTS_TOOL_NAMES         = {"search_events", "search_tours", "book_tour"}

def _filter_tools(names):
    return [t for t in all_tools if t["name"] in names]

transportation_tools = _filter_tools(TRANSPORTATION_TOOL_NAMES)
accommodation_tools  = _filter_tools(ACCOMMODATION_TOOL_NAMES)
dining_tools         = _filter_tools(DINING_TOOL_NAMES)
planning_tools       = _filter_tools(PLANNING_TOOL_NAMES)
local_info_tools     = _filter_tools(LOCAL_INFO_TOOL_NAMES)
events_tools         = _filter_tools(EVENTS_TOOL_NAMES)


# ── Generic subagent loop ─────────────────────────────────────────────────────

def run_subagent(task: str, domain_tools: list, system_prompt: str, max_iterations: int = 5) -> str:
    """Run an isolated agentic loop with a domain-specific tool subset.

    The loop is self-contained: its messages list never merges back into the
    orchestrator context. Only the final text summary is returned.
    """
    messages = [{"role": "user", "content": task}]

    for _ in range(max_iterations):
        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system_prompt,
            messages=messages,
            tools=domain_tools,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks     = [b for b in response.content if b.type == "text"]

        if not tool_use_blocks:
            return text_blocks[0].text if text_blocks else "(no result)"

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_call in tool_use_blocks:
            try:
                result = execute_function_call(tool_call)
            except (KeyError, TypeError) as e:
                result = f"Error: missing required field {e}. Please retry with all required parameters."
            tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})
        messages.append({"role": "user", "content": tool_results})

    return "(subagent reached max iterations without a final response)"


# ── Subagent wrappers ─────────────────────────────────────────────────────────

def call_transportation_agent(task: str) -> str:
    system = "You are a transportation specialist. Use your tools to help with flights, trains, and car rentals. Be concise and include booking confirmations when applicable."
    return run_subagent(task, transportation_tools, system)

def call_accommodation_agent(task: str) -> str:
    system = "You are an accommodation specialist. Use your tools to search for and book hotels. Be concise and include booking confirmations when applicable."
    return run_subagent(task, accommodation_tools, system)

def call_dining_agent(task: str) -> str:
    system = "You are a dining specialist. Use your tools to find restaurants, make reservations, and suggest local food experiences. Be concise."
    return run_subagent(task, dining_tools, system)

def call_planning_agent(task: str) -> str:
    system = "You are a trip planning specialist. Use your tools for itineraries, budgets, packing lists, and visa requirements. Be concise."
    return run_subagent(task, planning_tools, system)

def call_local_info_agent(task: str) -> str:
    system = "You are a local information specialist. Use your tools for currency conversion, translation, customs, emergency contacts, and pharmacies. Be concise."
    return run_subagent(task, local_info_tools, system)

def call_events_agent(task: str) -> str:
    system = "You are an events and tours specialist. Use your tools to find events, tours, and handle bookings. Be concise and include booking confirmations when applicable."
    return run_subagent(task, events_tools, system)


# ── Orchestrator tool definitions ──────────────────────────────────────────────
# The orchestrator only sees these 6 delegation tools — never the underlying 23.

orchestrator_tools = [
    {
        "name": "call_transportation_agent",
        "description": "Delegate transportation tasks to a specialist subagent. Handles: search_flights, book_flight, search_trains, book_train, rent_car.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Detailed description of the transportation task to accomplish"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_accommodation_agent",
        "description": "Delegate accommodation tasks to a specialist subagent. Handles: search_hotels, book_hotel, check_hotel_availability.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Detailed description of the accommodation task to accomplish"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_dining_agent",
        "description": "Delegate dining tasks to a specialist subagent. Handles: search_restaurants, make_restaurant_reservation, get_food_recommendations.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Detailed description of the dining task to accomplish"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_planning_agent",
        "description": "Delegate trip planning tasks to a specialist subagent. Handles: create_itinerary, calculate_budget, get_packing_suggestions, get_visa_requirements.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Detailed description of the planning task to accomplish"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_local_info_agent",
        "description": "Delegate local information tasks to a specialist subagent. Handles: convert_currency, translate_phrase, get_local_customs, get_emergency_contacts, find_nearby_pharmacy.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Detailed description of the local info task to accomplish"}
            },
            "required": ["task"]
        }
    },
    {
        "name": "call_events_agent",
        "description": "Delegate events and tours tasks to a specialist subagent. Handles: search_events, search_tours, book_tour.",
        "input_schema": {
            "type": "object",
            "properties": {
                "task": {"type": "string", "description": "Detailed description of the events/tours task to accomplish"}
            },
            "required": ["task"]
        }
    },
]

_SUBAGENT_DISPATCHERS = {
    "call_transportation_agent": lambda args: call_transportation_agent(args["task"]),
    "call_accommodation_agent":  lambda args: call_accommodation_agent(args["task"]),
    "call_dining_agent":         lambda args: call_dining_agent(args["task"]),
    "call_planning_agent":       lambda args: call_planning_agent(args["task"]),
    "call_local_info_agent":     lambda args: call_local_info_agent(args["task"]),
    "call_events_agent":         lambda args: call_events_agent(args["task"]),
}

def execute_orchestrator_tool(tool_call):
    handler = _SUBAGENT_DISPATCHERS.get(tool_call.name)
    if handler:
        return handler(tool_call.input)
    return f"Unknown orchestrator tool: {tool_call.name}"


# ── Context window visualiser (orchestrator view) ──────────────────────────────

GREY_BG = "\033[48;5;252m\033[38;5;17m"
RESET   = "\033[0m"

def print_orchestrator_context(system, messages):
    print(f"\n{GREY_BG}--- Orchestrator context ({len(messages) + 1} messages) ---{RESET}")
    for t in orchestrator_tools:
        print(f"{GREY_BG}[subagent_tool] {t['name']} — {t['description']}{RESET}")
    print(f"{GREY_BG}[system]: {system}{RESET}")
    for msg in messages:
        role    = msg["role"]
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
                        # Show only a preview — the subagent's full tool history is NOT here
                        preview = str(block["content"])[:150]
                        print(f"{GREY_BG}[{role} (subagent_result id={block['tool_use_id']})]: {preview}…{RESET}")
                else:
                    if block.type == "text":
                        print(f"{GREY_BG}[{role}]: {block.text}{RESET}")
                    elif block.type == "tool_use":
                        print(f"{GREY_BG}  ↳ delegate (id={block.id}): {block.name}({json.dumps(block.input)[:100]}){RESET}")
    print(f"{GREY_BG}---{RESET}\n")


# ── Orchestrator agentic loop ─────────────────────────────────────────────────

def trip_planner_with_subagents(user_message: str):
    """Coordinator that delegates to specialist subagents to keep its own context small.

    Key property: the orchestrator's context only ever contains the 6 delegation
    tool definitions and the text summaries returned by each subagent — never
    the 23 underlying tool definitions or the raw tool call/result pairs.
    """
    system = (
        f"Today is {datetime.today().strftime('%Y-%m-%d')}. You are a travel coordinator. "
        "Delegate tasks to the appropriate specialist subagent(s) and synthesise their "
        "results into a final response. Each subagent runs its own tool calls internally — "
        "you only receive their final text summaries."
    )

    messages  = [{"role": "user", "content": user_message}]
    max_iters = 8

    for iteration in range(1, max_iters + 1):
        print(f"\n--- Orchestrator Iteration {iteration} ---")
        print_orchestrator_context(system, messages)

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=2048,
            system=system,
            messages=messages,
            tools=orchestrator_tools,
        )

        tool_use_blocks = [b for b in response.content if b.type == "tool_use"]
        text_blocks     = [b for b in response.content if b.type == "text"]

        if not tool_use_blocks:
            print("Assistant:", text_blocks[0].text if text_blocks else "(no response)")
            messages.append({"role": "assistant", "content": response.content})
            user_input = input("\n> ")
            if user_input.lower() == "exit":
                break
            messages.append({"role": "user", "content": user_input})
            continue

        messages.append({"role": "assistant", "content": response.content})
        tool_results = []
        for tool_call in tool_use_blocks:
            print(f"  → Delegating to: {tool_call.name}")
            print(f"    task: {tool_call.input['task']}")
            result = execute_orchestrator_tool(tool_call)
            print(f"  ← Subagent summary: {result[:120]}…")
            tool_results.append({"type": "tool_result", "tool_use_id": tool_call.id, "content": result})
        messages.append({"role": "user", "content": tool_results})

    else:
        print(f"\nMax iterations ({max_iters}) reached.")


if __name__ == "__main__":
    user_input = input("> ")
    trip_planner_with_subagents(user_input)
