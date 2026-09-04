"""Hello-world Strands agent — confirm Bedrock credentials work."""
import sys
sys.path.insert(0, str(__import__("pathlib").Path(__file__).parent.parent))

from strands import Agent
from config import BEDROCK_MODEL_ID


def main():
    agent = Agent(model=f"bedrock/{BEDROCK_MODEL_ID}")
    result = agent("Say hello and confirm you are working. Keep it to one sentence.")
    print(f"\nAgent response: {result}")
    print("\nBedrock credentials are working!")


if __name__ == "__main__":
    main()
