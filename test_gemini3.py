import os
import asyncio
from dotenv import load_dotenv
from magi_orchestrator import GeminiNativeClient

load_dotenv()
api_key = os.environ.get("MAGI_GEMINI_API_KEY")


async def test_gemini_3():
    print("Testing gemini-3-flash-preview...")
    client = GeminiNativeClient(api_key=api_key)
    try:
        response = await client.generate_content(
            model="gemini-3-flash-preview",
            contents="Hello, identify yourself.",
            system_instruction="You are a test bot.",
        )
        print(f"Success! Response: {response}")
    except Exception as e:
        print(f"Failed: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_gemini_3())
