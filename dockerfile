FROM python:3.10

RUN apt update && apt install software-properties-common
RUN add-apt-repository ppa:alex-p/tesseract-ocr5 
RUN apt update && apt install mkvtoolnix tesseract-ocr

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT ["python3","/app/main.py"]