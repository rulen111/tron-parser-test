FROM python:3.10-alpine
WORKDIR /

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir --upgrade -r requirements.txt

COPY app/*.py .

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8080"]
