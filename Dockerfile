FROM python:3.7.1
ENV PYTHONUNBUFFERED 1

ENV VERSION 1.0

RUN apt-get update && apt-get install -y curl
RUN mkdir /model

WORKDIR /model
COPY requirements.txt /model/
COPY info.txt /model/
RUN pip install -r requirements.txt
COPY app/. /model/

CMD bash -c "python app.py"
