python3 -m pip install -r requirements.txt

start docker
docker pull grobid/grobid:0.8.1
if have gpu:
docker run --rm --gpus all --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.1

if no gpu: 
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.1

check localhost:8070 if grobid is running


install postgresql
install nodejs

npm version: 10.9.0
node version: 22.12.0

pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

average time to download paper 15.75 seconds
Average Extraction Time per Paper: 8.01 seconds
Keyword Counts in Filtered Sections:
  evaluation: 19
  methodology: 7
  related work: 40
  conclusion: 59
  baseline: 0
Papers with at least one keyword match: 64 out of 87

to start backend: uvicorn main:app --reload
to start frontend: npm start

You are an expert in analyzing scientific research papers. Your task is to compare two PDF files based on specific metrics and return a JSON object containing similarity scores.

to do: 
1. extract baselines and find hidden baselines (papers that should have been compared but are not present)
2. verify claims by author. (extract and verify claims)
3. visualization.
4. generate reason why 2 papers are comparable

### Input:
You will be provided with two PDF files:
1. **Reference Paper**: The paper we are comparing against.
2. **Comparison Paper**: The paper being compared.

### Metrics:
Evaluate the similarity of the two papers across the following metrics:
1. **Problem**
2. **Methods**
3. **Applications**
4. **Datasets**
5. **Results**
6. **Citations/References**
7. **Key Contributions**
8. **Assumptions**
9. **Evaluation Metrics**
10. **Theoretical vs. Practical**
11. **Baselines**
12. **Domain**

### Output:
Return the results as a **JSON object**, where the key is the metric and the value is the similarity score (a number between 0 and 1). Do not include any explanations or reasoning. The JSON should look like this:

```json
{
    "problem": 0.75,
    "methods": 0.60,
    "applications": 0.80,
    "datasets": 0.50,
    "results": 0.40,
    "citations/references": 0.70,
    "key_contributions": 0.85,
    "assumptions": 0.60,
    "evaluation_metrics": 0.65,
    "theoretical_vs_practical": 0.90,
    "baselines": 0.55,
    "domain": 0.95
}
