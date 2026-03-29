from openai import OpenAI
import json

from test_simple_agent import tools, execute_function_call

client = OpenAI()

def trip_planner_agent(user_message):
    """Enhanced trip planner with continuous tool calling loop"""
    messages = [
        {
            "role": "system", 
            "content": """You are a helpful trip planning assistant. Help users plan their trips by:
            1. Checking weather conditions for destinations
            2. Suggesting relevant points of interest based on preferences
            3. Purchasing tickets for attractions when requested
            
            Always provide comprehensive advice and feel free to use multiple tools in sequence to give complete trip planning assistance. 
            For example, you might check weather first, then suggest appropriate POIs based on conditions, and finally help purchase tickets for recommended attractions."""
        },
        {"role": "user", "content": user_message}
    ]
    
    max_iterations = 10  # Prevent infinite loops
    iteration = 0
    
    while iteration < max_iterations:
        iteration += 1
        print(f"\n--- Iteration {iteration} ---")
        
        completion = client.chat.completions.create(
            model="gpt-4o",
            messages=messages,
            tools=tools
        )
        
        assistant_message = completion.choices[0].message
        
        # Always print assistant's message if it has content
        if assistant_message.content:
            print("Assistant:", assistant_message.content)
        
        # Check if there are tool calls to execute
        if assistant_message.tool_calls:
            print(f"\nExecuting {len(assistant_message.tool_calls)} function(s)...")
            
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

                # Prompt and wait for key press to continue
                input("Press Enter to continue...")
            
            # Continue the loop to get next response
            continue
        else:
            # No more tool calls, we have the final response
            print(f"\n🎯 Final response (after {iteration} iteration(s)):")
            print("Assistant:", assistant_message.content or "Trip planning complete!")
            break
    
    if iteration >= max_iterations:
        print(f"\n⚠️ Maximum iterations ({max_iterations}) reached. Ending conversation.")

# Enhanced test queries that trigger multiple tool calls
test_queries = [
    # Complex multi-step planning
    "I'm planning a 2 days' trip to New York, including Friday and Saturday. Please arrange the trip for me.",
    
    # Conditional logic trigger
    #"Help me plan a 3 days' trip to Paris. Date is flexible. Find at least 2 Sunny or Cloudy day in the next week. Buy tickets for me.",
]

if __name__ == "__main__":
    for i, query in enumerate(test_queries, 1):
        print(f"\n{'='*60}")
        print(f"TEST QUERY {i}: {query}")
        print('='*60)
        trip_planner_agent(query)
        print("\n" + "="*60)