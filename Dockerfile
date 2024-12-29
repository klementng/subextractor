FROM python:3.12

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

RUN groupadd -g 1000 app && \
    useradd -m -u 1000 -g app -s /bin/bash app

USER 1000:1000