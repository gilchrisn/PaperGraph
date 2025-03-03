import os
import logging
from dotenv import load_dotenv
from supabase import create_client, Client
from semantic_scholar import process_and_cite_paper, search_papers_by_title

load_dotenv()

# ----------------------------
# Logging Configuration
# ----------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(),
        # Uncomment to enable file logging:
        # logging.FileHandler("paper_downloader.log")
    ]
)
logger = logging.getLogger(__name__)

# ----------------------------
# Supabase Configuration
# ----------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://your-supabase-url.supabase.co")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "your-supabase-api-key")
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)


def main():
    # Example: search for papers by title (optional usage)
    # api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", None)
    # search_results = search_papers_by_title("Attention Is All You Need", limit=5, api_key=api_key)
    # logger.info(f"Search results: {search_results}")

    start_paper_id = input("Enter the Semantic Scholar paper id: ").strip()
    api_key = os.getenv("SEMANTIC_SCHOLAR_API_KEY", None)
    process_and_cite_paper(start_paper_id, supabase, api_key)
    logger.info("Processing complete.")


if __name__ == "__main__":
    main()


# Attention is All you Need: 204e3073870fae3d05bcbc2f6a8e263d9b72e776
# Chain-of-Thought Prompting Elicits Reasoning in Large Language Models: 1b6e810ce0afd0dd093f789d2b2742d047e316d5
# Large Language Models are Zero-Shot Reasoners: e7ad08848d5d7c5c47673ffe0da06af443643bda
# Distilling Step-by-Step! Outperforming Larger Language Models with Less Training Data and Smaller Model Sizes: aad167be3c902388ea625da4117fcae4325b8b7d
