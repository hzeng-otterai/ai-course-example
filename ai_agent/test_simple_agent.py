from openai import OpenAI
import json
import random

client = OpenAI()

tools = [{
    "type": "function",
    "function": {
        "name": "get_weather",
        "description": "Get current weather for a given location.",
        "parameters": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "City and country e.g. Paris, France"
                },
                "day": {
                    "type": "string",
                    "description": "Optional day for the weather forecast, e.g. 'Friday', '2024-06-14'."
                }
            },
            "required": ["location"],
            "additionalProperties": False
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "suggest_poi",
        "description": "Suggest points of interest based on location and preferences.",
        "parameters": {
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
    }
},
{
    "type": "function",
    "function": {
        "name": "buy_ticket",
        "description": "Purchase tickets for attractions that require them.",
        "parameters": {
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
}]

def execute_function_call(tool_call):
    """Execute the function call and return the result"""
    tool_call_name = tool_call.function.name
    arguments = json.loads(tool_call.function.arguments)
    
    if tool_call_name == "get_weather":
        # Mock weather API call
        location = arguments["location"]
        day = arguments.get("day")

        # In a real implementation, you would call an actual weather API
        weather_conditions = ["Sunny", "Cloudy", "Rainy", "Partly cloudy"]
        result = f"Weather in {location} on {day}: {random.choice(weather_conditions)}, 22°C"
        return result
        
    elif tool_call_name == "suggest_poi":
        # Mock POI suggestion
        location = arguments["location"]
        preference = arguments["preference"]
        category = arguments.get("category")
        
        # Sample POI suggestions based on city and preference
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
        # Default POIs if city not recognized
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
        else:  # both
            suggestions = indoor_pois[:2] + outdoor_pois[:2]
            
        result = f"Suggested POIs in {location} ({preference}): {', '.join(suggestions)}"
        return result
        
    elif tool_call_name == "buy_ticket":
        # Mock ticket purchase
        attraction = arguments["attraction"]
        location = arguments["location"]
        date = arguments["date"]
        quantity = arguments["quantity"]
        
        # Simulate ticket purchase
        ticket_price = 25  # Mock price
        total_cost = ticket_price * quantity
        result = f"Successfully purchased {quantity} ticket(s) for {attraction} in {location} on {date}. Total cost: ${total_cost}"
        return result
    
    return "Function not implemented"

def trip_planner_agent(user_message):
    """Main trip planner function"""
    messages = [
        {
            "role": "system", 
            "content": "You are a helpful trip planning assistant. Help users plan their trips by checking weather, suggesting points of interest, and buying tickets when needed. Always be friendly and provide comprehensive travel advice."
        },
        {"role": "user", "content": user_message}
    ]
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        tools=tools
    )
    
    print("Assistant:", completion.choices[0].message.content)
    
    # Handle tool calls if any
    if completion.choices[0].message.tool_calls:
        print("\nExecuting functions...")
        
        # Add assistant message with tool calls to conversation
        messages.append(completion.choices[0].message)
        
        # Execute each tool call
        for tool_call in completion.choices[0].message.tool_calls:
            print(f"Calling: {tool_call.function.name}")
            result = execute_function_call(tool_call)
            print(f"Result: {result}")
            
            # Add function result to messages
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": result
            })
        
        # Get final response with function results
        final_completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools
        )
        
        print("\nFinal response:")
        print("Assistant:", final_completion.choices[0].message.content)

# Example usage
if __name__ == "__main__":
    # Test cases for the trip planner
    test_queries = [
        "Any suggestions for a trip to Paris?",
        "I want to plan a trip to New York. Can you check the weather and suggest some outdoor attractions?",
    ]
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*50}")
        print(f"TEST QUERY {i}: {query}")
        print('='*50)
        trip_planner_agent(query)