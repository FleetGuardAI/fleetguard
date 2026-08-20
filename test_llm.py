import asyncio
import sys
import os

# Add backend to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from backend.infrastructure.llm.openai_provider import OpenAIProvider
from backend.infrastructure.llm.provider import LLMMessage

async def main():
    try:
        provider = OpenAIProvider()
        messages = [LLMMessage(role="user", content="hi")]
        response = await provider.chat(messages=messages)
        print("Success:", response.message.content)
    except Exception as e:
        print("Error:", repr(e))

if __name__ == "__main__":
    asyncio.run(main())
