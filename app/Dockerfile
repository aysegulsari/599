FROM python:3
ENV PYTHONUNBUFFERED=1
WORKDIR /analyzeMyMood
COPY requirements.txt /analyzeMyMood/
RUN pip install -r requirements.txt
COPY . /analyzeMyMood/