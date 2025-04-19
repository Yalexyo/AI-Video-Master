import os
from dotenv import load_dotenv

# Load .env file
load_dotenv()

# Print environment variables
print(f"DASHSCOPE_API_KEY: {os.getenv('DASHSCOPE_API_KEY', 'Not found')}")
