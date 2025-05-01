import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Azure OpenAI settings
AZURE_OPENAI_MODEL = os.environ.get("AZURE_OPENAI_MODEL", "gpt-4.1-mini")
OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", "2024-12-01-preview")
AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")

# Validate required settings
if not all([AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY]):
    raise ValueError("Missing required Azure OpenAI environment variables. Please check your .env file.") 