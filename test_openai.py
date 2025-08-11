from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

response = client.responses.create(
    model="gpt-4o-mini",
    input="Say hello from the OpenAI API!"
)

print(response.output_text)

