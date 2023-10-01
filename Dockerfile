FROM python:3.9-slim-buster

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

expose 5000

CMD python ./main.py