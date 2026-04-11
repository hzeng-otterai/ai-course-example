import anthropic
import random

client = anthropic.Anthropic()

tools = [
    {
        "name": "get_weather",
        "description": "Get current weather for a given location.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country e.g. Paris, France"
                },
                "day": {
                    "type": "string",
                    "description": "Date for the weather forecast, e.g. 'this Friday', '2024-06-14'."
                }
            },
            "required": ["location", "day"],
            "additionalProperties": False
        }
    },
    {
        "name": "suggest_poi",
        "description": "Suggest points of interest based on location and preferences.",
        "input_schema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country where to find POIs"
                },
                "preference": {
                    "type": "string",
                    "enum": ["indoor", "outdoor", "both"],
                    "description": "Type of activities preferred"
                },
                "category": {
                    "type": "string",
                    "description": "Optional category like 'museums', 'parks', 'restaurants', etc."
                }
            },
            "required": ["location", "preference"],
            "additionalProperties": False
        }
    },
    {
        "name": "buy_ticket",
        "description": "Purchase tickets for attractions that require them.",
        "input_schema": {
            "type": "object",
            "properties": {
                "attraction": {
                    "type": "string",
                    "description": "Name of the attraction or point of interest"
                },
                "location": {
                    "type": "string",
                    "description": "City where the attraction is located"
                },
                "date": {
                    "type": "string",
                    "description": "Date for the visit in YYYY-MM-DD format"
                },
                "quantity": {
                    "type": "number",
                    "description": "Number of tickets to purchase"
                }
            },
            "required": ["attraction", "location", "date", "quantity"],
            "additionalProperties": False
        }
    }
]

def execute_function_call(tool_call):
    """Execute the function call and return the result"""
    tool_call_name = tool_call.name
    arguments = tool_call.input

    if tool_call_name == "get_weather":
        location = arguments["location"]
        day = arguments.get("day")
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Partly cloudy"]
        return f"Weather in {location} on {day}: {random.choice(weather_conditions)}, 22°C"

    elif tool_call_name == "suggest_poi":
        location = arguments["location"]
        preference = arguments["preference"]

        city = location.split(',')[0].strip().lower()
        poi_by_city = {
            "paris": {
                "indoor": ["Louvre Museum", "Musée d'Orsay", "Notre-Dame Cathedral"],
                "outdoor": ["Eiffel Tower", "Seine River Cruise", "Champs-Élysées"]
            },
            "new york": {
                "indoor": ["Metropolitan Museum", "Museum of Modern Art", "Broadway Theater"],
                "outdoor": ["Central Park", "Statue of Liberty", "Brooklyn Bridge"]
            }
        }
        default_indoor = ["National Gallery", "Science Museum", "Shopping Mall"]
        default_outdoor = ["Golden Gate Bridge", "Beach Promenade", "City Park"]

        if city in poi_by_city:
            indoor_pois = poi_by_city[city]["indoor"]
            outdoor_pois = poi_by_city[city]["outdoor"]
        else:
            indoor_pois = default_indoor
            outdoor_pois = default_outdoor

        if preference == "indoor":
            suggestions = indoor_pois[:3]
        elif preference == "outdoor":
            suggestions = outdoor_pois[:3]
        else:
            suggestions = indoor_pois[:2] + outdoor_pois[:2]

        return f"Suggested POIs in {location} ({preference}): {', '.join(suggestions)}"

    elif tool_call_name == "buy_ticket":
        attraction = arguments["attraction"]
        location = arguments["location"]
        date = arguments["date"]
        quantity = arguments["quantity"]
        total_cost = 25 * quantity
        return f"Successfully purchased {quantity} ticket(s) for {attraction} in {location} on {date}. Total cost: ${total_cost}"

    return "Function not implemented"


def trip_planner_single_round(user_message):
    """Main trip planner function"""
    system = "You are a helpful trip planning assistant. Help users plan their trips by checking weather, suggesting points of interest, and buying tickets. Always be friendly and provide comprehensive travel advice."
    messages = [{"role": "user", "content": user_message}]

    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=system,
        messages=messages,
        tools=tools
    )

    text_blocks = [b for b in response.content if b.type == "text"]
    tool_use_blocks = [b for b in response.content if b.type == "tool_use"]

    if text_blocks:
        print("Assistant:", text_blocks[0].text)

    if tool_use_blocks:
        print("\nExecuting functions...")
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for tool_call in tool_use_blocks:
            print(f"Calling: {tool_call.name}")
            result = execute_function_call(tool_call)
            print(f"Result: {result}")
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": tool_call.id,
                "content": result
            })

        messages.append({"role": "user", "content": tool_results})

        final_response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=system,
            messages=messages,
            tools=tools
        )

        final_text = [b for b in final_response.content if b.type == "text"]
        print("\nFinal response:")
        if final_text:
            print("Assistant:", final_text[0].text)


if __name__ == "__main__":
    test_queries = [
        "Any suggestions for a trip to Paris?",
        "I want to plan a trip to New York. Can you check the weather and suggest some outdoor attractions?",
    ]

    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"TEST QUERY {i}: {query}")
        print('='*50)
        trip_planner_single_round(query)
