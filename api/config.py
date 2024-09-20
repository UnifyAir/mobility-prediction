from dotenv import load_dotenv
import os

# Load the .env file into environment variables
load_dotenv()

def get_openai_api_key():
    return os.getenv("OPENAI_API_KEY")

def get_gemini_api_key():
    return os.getenv("GEMINI_API_KEY")


