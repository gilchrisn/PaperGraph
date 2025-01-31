from transformers import AutoTokenizer, AutoModel
import torch
import torch.nn.functional as F

# Path to your local SciBERT model files
model_path = "models/scibert"

# Load tokenizer and model from local path
tokenizer = AutoTokenizer.from_pretrained(model_path)
model = AutoModel.from_pretrained(model_path)

print("Model and tokenizer loaded successfully!")

# # Function to generate embeddings for text
# def generate_embedding(text):
#     if not text:
#         return None
#     tokens = tokenizer(text, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
#     with torch.no_grad():
#         outputs = model(**tokens)
#     cls_embedding = outputs.last_hidden_state[:, 0, :]  # [CLS] token embedding
#     return F.normalize(cls_embedding, p=2, dim=1).numpy()  # Normalize and convert to numpy

# # Metrics for each paper
# def create_paper_metrics():
#     """
#     Create a dictionary to represent metrics for a paper.

#     :return: Dictionary with default None values for all metrics
#     """
#     return {
#         "problem": None,
#         "methods": None,
#         "applications": None,
#         "datasets": None,
#         "results": None,
#         "citations/references": None,
#         "key_contributions": None,
#         "assumptions": None,
#         "evaluation_metrics": None,
#         "theoretical_vs_practical": None,
#         "baselines": None,
#         "domain": None,
#     }

# # Function to generate embeddings for a paper's metrics
# def generate_paper_embeddings(paper):
#     """
#     Generate embeddings for each metric of a paper.

#     :param paper: Dictionary of paper metrics
#     :return: Dictionary of embeddings for each metric
#     """
#     embeddings = {}
#     for metric, value in paper.items():
#         if value:  # Generate embedding only if the metric has content
#             embeddings[metric] = generate_embedding(value)
#         else:
#             embeddings[metric] = None
#     return embeddings

# if __name__ == "__main__":
#     # Test single text embedding
#     text = "SciBERT is designed for scientific text processing."
#     embedding = generate_embedding(text)
#     print("Generated Embedding Shape:", embedding.shape)

# def generate_combined_embedding(paper_metrics):
#     """
#     Generate a combined embedding for a paper by concatenating all its metrics.

#     :param paper_metrics: Dictionary of paper metrics
#     :param tokenizer: Hugging Face tokenizer
#     :param model: Hugging Face model
#     :return: Normalized embedding tensor
#     """
#     combined_text = " ".join(f"{key}: {value}" for key, value in paper_metrics.items() if value)
#     tokens = tokenizer(combined_text, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
#     with torch.no_grad():
#         outputs = model(**tokens)
#     return F.normalize(outputs.last_hidden_state[:, 0, :], p=2, dim=1)  # Normalize embedding

def generate_embedding(paper_abstract):
    """
    Generate an embedding for a paper abstract using SciBERT.

    :param paper_abstract: Abstract text of the paper
    :return: Normalized embedding tensor
    """
    tokens = tokenizer(paper_abstract, return_tensors="pt", padding="max_length", truncation=True, max_length=512)
    with torch.no_grad():
        outputs = model(**tokens)
    return F.normalize(outputs.last_hidden_state[:, 0, :], p=2, dim=1)  # Normalize embedding

