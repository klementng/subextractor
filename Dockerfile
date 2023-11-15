FROM lscr.io/linuxserver/ffmpeg:latest

RUN apt update && \ 
    apt install -y \ 
        python3 \
        python3-pip \ 
        mkvtoolnix \ 
        tesseract-ocr \ 
        libgl1

COPY ./requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

RUN rm -rf /var/lib/apt/lists/* /var/tmp/*

WORKDIR /app
COPY . .

ENV \
  PUID=1000 \
  PGID=1000

ENTRYPOINT [ "/init" , "python3", "/app/main.py" ]