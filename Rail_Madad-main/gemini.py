from dotenv import load_dotenv
import os

# Load the .env file
load_dotenv()

# Get the API key
api_key = os.getenv('API_KEY')

import google.generativeai as genai

# Configure the API key
genai.configure(api_key=api_key)

# Create a GenerativeModel instance
model = genai.GenerativeModel('gemini-1.5-flash')

# Generate content
response = model.generate_content("What is Python?")
print(response.text)


