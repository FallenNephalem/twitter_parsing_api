FROM python:3.10


WORKDIR /app
COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt
COPY . .

CMD exec uvicorn --host 0.0.0.0 --port 8080 main:app --reload