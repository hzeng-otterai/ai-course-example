from anthropic import AsyncAnthropic
import asyncio
from datetime import datetime

client = AsyncAnthropic()

# Construct the system prompt
system_prompt_template = """You are Bobby, a virtual assistant create by Huajun. Today is {today}. You provide responses to questions that are clear, straightforward, and factually accurate."""

system_prompt = system_prompt_template.format(
    today=datetime.today().strftime('%Y-%m-%d')
)

async def chat_func(history):

    messages = [{"role": "system", "content": system_prompt}] + history
    GREY_BG = "\033[48;5;252m\033[38;5;17m"
    RESET = "\033[0m"
    print(f"\n{GREY_BG}--- Context window ({len(messages)} messages) ---{RESET}")
    for msg in messages:
        print(f"{GREY_BG}[{msg['role']}]: {msg['content']}{RESET}")
    print(f"{GREY_BG}---{RESET}\n")

    buffer = ""
    async with client.messages.stream(
        model="claude-sonnet-4-6",
        max_tokens=4096,
        system=system_prompt,
        messages=history,
        temperature=0.5,
    ) as stream:
        async for text in stream.text_stream:
            print(text, flush=True, end="")
            buffer += text

    print("\n", flush=True)

    return buffer

async def continous_chat():
    history = []

    # Loop to receive user input continously
    while(True):
        user_input = input("> ")
        if user_input == "exit":
            break

        history.append({"role": "user", "content": user_input})

        # notice every time we call the chat function
        # we pass all the history to the API
        bot_response = await chat_func(history)

        history.append({"role": "assistant", "content": bot_response})

asyncio.run(continous_chat())

