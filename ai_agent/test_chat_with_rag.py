from openai import AsyncOpenAI
from tavily import AsyncTavilyClient
import asyncio
import os
from datetime import datetime

client = AsyncOpenAI()
tavily = AsyncTavilyClient(api_key=os.environ["TAVILY_API_KEY"])

system_prompt_template = """You are Bobby, a virtual assistant created by Huajun. Today is {today}. You provide responses to questions that are clear, straightforward, and factually accurate.

When answering, use the web search results provided in the context if they are relevant. Cite information from the search results when appropriate."""

system_prompt = system_prompt_template.format(
    today=datetime.today().strftime('%Y-%m-%d')
)

GREY_BG = "\033[48;5;252m\033[38;5;17m"
RESET = "\033[0m"


async def web_search(query: str, max_results: int = 3) -> str:
    response = await tavily.search(query, max_results=max_results)
    results = response.get("results", [])
    if not results:
        return "No search results found."
    formatted = []
    for i, r in enumerate(results, 1):
        formatted.append(f"[{i}] {r['title']}\nURL: {r['url']}\n{r['content']}")
    return "\n\n".join(formatted)


async def chat_func(history):
    messages = [{"role": "system", "content": system_prompt}] + history

    print(f"\n{GREY_BG}--- Context window ({len(messages)} messages) ---{RESET}")
    for msg in messages:
        print(f"{GREY_BG}[{msg['role']}]: {msg['content']}{RESET}")
    print(f"{GREY_BG}---{RESET}\n")

    result = await client.chat.completions.create(
        model="gpt-5.4-mini",
        messages=messages,
        temperature=0.5,
        stream=True,
    )

    buffer = ""
    async for r in result:
        next_token = r.choices[0].delta.content
        if next_token:
            print(next_token, flush=True, end="")
            buffer += next_token

    print("\n", flush=True)

    return buffer


async def continous_chat():
    history = []

    while True:
        user_input = input("> ")
        if user_input == "exit":
            break

        # Retrieve web search results and inject as context
        print("Searching the web...", flush=True)
        search_results = await web_search(user_input)
        rag_content = f"Web search results for '{user_input}':\n\n{search_results}"

        # Build message: inject search results before the user question
        augmented_user_message = f"{rag_content}\n\nUser question: {user_input}"
        history.append({"role": "user", "content": augmented_user_message})

        bot_response = await chat_func(history)

        history.append({"role": "assistant", "content": bot_response})

asyncio.run(continous_chat())
