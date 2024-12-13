# Install necessary libraries
# pip install transformers datasets torch scikit-learn

# Import necessary libraries
from torch import Tensor
from transformers import AutoTokenizer, AutoModelForTokenClassification, TrainingArguments, Trainer, pipeline
from datasets import Dataset, DatasetDict, load_dataset
from sklearn.metrics import precision_recall_fscore_support

# Define labels and mappings
# We define the labels we want the model to predict, such as BASELINE, DATASET, etc.
label_list = ["O", "B-BASELINE", "I-BASELINE", "B-DATASET", "I-DATASET", "B-EXPERIMENT", "I-EXPERIMENT"]
label_to_id = {label: i for i, label in enumerate(label_list)}  # Map labels to IDs
id_to_label = {i: label for label, i in label_to_id.items()}    # Map IDs back to labels

# Load your annotated dataset
# The dataset should be in a format where each example has "tokens" (words) and "labels" (entity tags)
# Example JSON structure:
# [
#     {
#         "tokens": ["We", "compare", "our", "method", "to", "BERT", "on", "ImageNet", "dataset", "."],
#         "labels": ["O", "O", "O", "O", "O", "B-BASELINE", "O", "B-DATASET", "I-DATASET", "O"]
#     }
# ]
dataset = load_dataset("json", data_files={"train": "train.json", "test": "test.json"})

# Load SciBERT tokenizer and model
# SciBERT is pretrained on scientific text and is ideal for tasks involving research papers.
model_name = "allenai/scibert_scivocab_uncased"
tokenizer = AutoTokenizer.from_pretrained(model_name)  # Tokenizer converts text to tokens for the model
model = AutoModelForTokenClassification.from_pretrained(model_name, num_labels=len(label_to_id))  # The model is adapted for token classification

# Tokenization function to align labels with tokens
def tokenize_and_align_labels(examples):
    tokenized_inputs = tokenizer(examples["tokens"], truncation=True, padding=True, is_split_into_words=True)
    labels = []
    for i, label in enumerate(examples["labels"]):
        word_ids = tokenized_inputs.word_ids(batch_index=i)  # Map tokens back to original words
        label_ids = []
        for word_id in word_ids:
            if word_id is None:  # Ignore padding tokens
                label_ids.append(-100)
            else:
                label_ids.append(label_to_id[label[word_id]])  # Assign label IDs to tokens
        labels.append(label_ids)
    tokenized_inputs["labels"] = labels
    return tokenized_inputs

# Apply tokenization and label alignment to the dataset
tokenized_dataset = dataset.map(tokenize_and_align_labels, batched=True)

# Define training arguments for fine-tuning
training_args = TrainingArguments(
    output_dir="./results",            # Directory to save model checkpoints
    evaluation_strategy="epoch",      # Evaluate after every epoch
    learning_rate=2e-5,               # Learning rate for the optimizer
    per_device_train_batch_size=16,   # Batch size per device
    num_train_epochs=3,               # Number of training epochs
    weight_decay=0.01,                # Weight decay for regularization
    save_total_limit=2                # Keep only the last 2 checkpoints
)

# Function to compute evaluation metrics
def compute_metrics(pred):
    predictions, labels = pred
    predictions = predictions.argmax(axis=-1)  # Get the predicted label with the highest score
    true_labels = [
        [id_to_label[l] for l in label if l != -100]  # Convert label IDs back to readable labels
        for label in labels
    ]
    pred_labels = [
        [id_to_label[p] for p, l in zip(pred, label) if l != -100]
        for pred, label in zip(predictions, labels)
    ]
    precision, recall, f1, _ = precision_recall_fscore_support(true_labels, pred_labels, average="weighted")
    return {"precision": precision, "recall": recall, "f1": f1}

# Initialize the Trainer
trainer = Trainer(
    model=model,                         # The SciBERT model
    args=training_args,                  # Training arguments
    train_dataset=tokenized_dataset["train"],  # Training data
    eval_dataset=tokenized_dataset["test"],    # Evaluation data
    tokenizer=tokenizer,                 # Tokenizer
    compute_metrics=compute_metrics      # Evaluation metrics function
)

# Train the model
trainer.train()

# Evaluate the model on the test dataset
metrics = trainer.evaluate()
print("Evaluation Metrics:", metrics)

# Save the trained model for later use
model.save_pretrained("./fine_tuned_scibert")
tokenizer.save_pretrained("./fine_tuned_scibert")

# Inference: Use the fine-tuned model to predict on new text
ner_pipeline = pipeline("ner", model="./fine_tuned_scibert", tokenizer="./fine_tuned_scibert")

# Example text to test the model
text = "We compare our method to BERT and GPT-3 on the ImageNet dataset."

# Run the pipeline on the text
predictions = ner_pipeline(text)

# Print the predictions
for entity in predictions:
    print(f"Entity: {entity['word']}, Label: {entity['entity']}")
