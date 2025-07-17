import os
from openai import OpenAI, AzureOpenAI
from dotenv import load_dotenv

load_dotenv()

# Get the model provider from environment variable
MODEL_PROVIDER = os.getenv('MODEL_PROVIDER')

if MODEL_PROVIDER == 'azure':
    # Azure OpenAI settings
    AZURE_OPENAI_MODEL = os.environ.get("AZURE_OPENAI_MODEL", "gpt-4.1-mini")
    OPENAI_API_VERSION = os.environ.get("OPENAI_API_VERSION", "2024-12-01-preview")
    AZURE_OPENAI_ENDPOINT = os.environ.get("AZURE_OPENAI_ENDPOINT")
    AZURE_OPENAI_KEY = os.environ.get("AZURE_OPENAI_KEY")

    if not all([AZURE_OPENAI_MODEL, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, OPENAI_API_VERSION]):
        raise ValueError("Missing required Azure OpenAI environment variables. \
                         AZURE_OPENAI_MODEL, AZURE_OPENAI_ENDPOINT, AZURE_OPENAI_KEY, \
                         OPENAI_API_VERSION are required. Please check your .env file.")
    CLIENT = AzureOpenAI(
        api_key=AZURE_OPENAI_KEY,
        api_version=OPENAI_API_VERSION,
        azure_endpoint=AZURE_OPENAI_ENDPOINT
    )
    MODEL = AZURE_OPENAI_MODEL
    
elif MODEL_PROVIDER == 'openai':
    # OpenAI settings
    OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
    OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4")

    CLIENT = OpenAI(
        api_key=OPENAI_API_KEY
    )
    MODEL = OPENAI_MODEL

    if not all([OPENAI_API_KEY, OPENAI_MODEL]):
        raise ValueError("Missing required OpenAI environment variables. \
                         OPENAI_API_KEY, OPENAI_MODEL are required. Please check your .env file.") 

else:
    raise ValueError(f"Invalid model provider: {MODEL_PROVIDER}.
                     Must be either 'openai' or 'azure'")