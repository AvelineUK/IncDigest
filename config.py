"""
Configuration Module
Loads environment variables from .env file
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Get API key
ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')

def check_api_key():
    """Check if API key is set"""
    if not ANTHROPIC_API_KEY:
        raise ValueError(
            "ANTHROPIC_API_KEY not found!\n"
            "Please create a .env file in the project directory with:\n"
            "ANTHROPIC_API_KEY=sk-ant-your-key-here"
        )
    return ANTHROPIC_API_KEY
