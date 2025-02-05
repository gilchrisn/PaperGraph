from openai import OpenAI
import os
from dotenv import load_dotenv

load_dotenv()

# Fetch the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

def prompt_chatgpt(messages, model="gpt-4o-mini"):
    """
    Sends a series of messages to ChatGPT and returns the response.

    Parameters:
        messages (list of dict): A list of messages in the format 
                                 [{"role": "system", "content": "..."},
                                  {"role": "user", "content": "..."}].
        model (str): The OpenAI model to use, default is "gpt-4o-mini".

    Returns:
        dict: The response from ChatGPT.
    """
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages
        )

        return parse_response(completion.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}
    
def parse_response(response):
    cleaned_response = response.strip().strip('```json')

    import json
    # Parse response into a dictionary
    response_dict = json.loads(cleaned_response)
    return response_dict

# Example Usage
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about recursion in programming."}
    ]
    response = prompt_chatgpt(messages)
    print("Response from ChatGPT:")
    print(response)
