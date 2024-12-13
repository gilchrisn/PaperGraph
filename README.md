python3 -m pip install -r requirements.txt

start docker

if have gpu:
docker run --rm --gpus all --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.1

if no gpu: 
docker run --rm --init --ulimit core=0 -p 8070:8070 grobid/grobid:0.8.1

check localhost:8070 if grobid is running


pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
