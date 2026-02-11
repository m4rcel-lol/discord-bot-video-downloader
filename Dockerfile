FROM python:3.12-alpine

RUN apk add --no-cache ffmpeg

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY bot.py .
COPY .env.example .

RUN mkdir -p /app/downloads

CMD ["python", "bot.py"]
