python3 -m pip install -r requirements.txt

start docker

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