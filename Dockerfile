FROM ubuntu:focal

RUN apt update && apt install software-properties-common -y
RUN add-apt-repository ppa:alex-p/tesseract-ocr5 
RUN apt update && apt install mkvtoolnix tesseract-ocr python3-pip ffmpeg libsm6 libxext6 -y

COPY ./requirements.txt requirements.txt
RUN python3 -m pip install -r requirements.txt

WORKDIR /app
COPY . .

ENTRYPOINT ["python3","/app/main.py"]