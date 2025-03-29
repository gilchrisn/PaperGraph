from openai import OpenAI
import tiktoken
import logging
import os
from dotenv import load_dotenv

load_dotenv()

# Fetch the API key from the environment variable
api_key = os.getenv("OPENAI_API_KEY")

# Initialize the OpenAI client with the API key
client = OpenAI(api_key=api_key)

# Configure logging
logger = logging.getLogger(__name__)


def count_tokens(text: str, model: str = "gpt-4o") -> int:
    encoding = tiktoken.encoding_for_model(model)
    tokens = encoding.encode(text)
    return len(tokens)

# Global counters to accumulate token usage
total_prompt_tokens = 0
total_response_tokens = 0
total_embedding_tokens = 0

def prompt_chatgpt(messages, model="gpt-4o"):
    """
    Sends a series of messages to ChatGPT and returns the response.
    Also logs and aggregates token usage.
    """
    global total_prompt_tokens, total_response_tokens
    
    # Combine all message contents for token counting
    prompt_text = "\n".join(message["content"] for message in messages)
    prompt_token_count = count_tokens(prompt_text, model=model)
    total_prompt_tokens += prompt_token_count
    logger.info("Prompt tokens for this call: %d (Total so far: %d)\n\n", prompt_token_count, total_prompt_tokens)
    
    try:
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0
        )
        response_content = completion.choices[0].message.content
        response_token_count = count_tokens(response_content, model=model)
        total_response_tokens += response_token_count
        logger.info("Response tokens for this call: %d (Total so far: %d)\n\n", response_token_count, total_response_tokens)
        return response_content
    except Exception as e:
        logger.error("Error in prompt_chatgpt: %s", e)
        return {"error": str(e)}

def generate_embedding(text, model="text-embedding-3-small"):
    text = text.replace("\n", " ")

    # Count tokens for the embedding
    global total_embedding_tokens
    embedding_token_count = count_tokens(text, model=model)
    total_embedding_tokens += embedding_token_count
    logger.info("Embedding tokens for this call: %d (Total so far: %d)\n\n", embedding_token_count, total_embedding_tokens)
    
    return client.embeddings.create(input = [text], model=model).data[0].embedding

def get_total_prompt_tokens():
    return total_prompt_tokens

def get_total_response_tokens():
    return total_response_tokens
# Example Usage
if __name__ == "__main__":
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Write a haiku about recursion in programming."}
    ]
    response = prompt_chatgpt(messages)
    print("Response from ChatGPT:")
    print(response)
    print("Total prompt tokens:", total_prompt_tokens)
    print("Total response tokens:", total_response_tokens)
    print("Total tokens:", total_prompt_tokens + total_response_tokens)