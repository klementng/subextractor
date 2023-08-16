FROM python:3.10

RUN add-apt-repository ppa:alex-p/tesseract-ocr5 && apt update
RUN apt install mkvtoolnix tesseract-ocr

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

ENTRYPOINT ["python3","/app/main.py"]