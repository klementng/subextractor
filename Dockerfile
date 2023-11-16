FROM python:3.11

RUN apt update && \ 
    apt install -y \ 
        ffmpeg \
        mkvtoolnix \ 
        tesseract-ocr \ 
        libgl1

COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN rm -rf /var/lib/apt/lists/* /var/tmp/*

WORKDIR /app
COPY . .
ENTRYPOINT [ "python3", "/app/main.py" ]