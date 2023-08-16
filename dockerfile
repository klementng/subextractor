FROM ubuntu:focal

RUN apt update && apt install software-properties-common -y
RUN add-apt-repository ppa:alex-p/tesseract-ocr5 
RUN apt update && apt install mkvtoolnix tesseract-ocr -y

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT ["python3","/app/main.py"]