FROM python:3.10.8

WORKDIR /app

COPY requirements.txt .

RUN apt-get update && apt-get install -y cloc

RUN pip install --upgrade pip
RUN pip install -r requirements.txt

CMD ["python", "main.py"]