# Dockerfile
FROM python:3.12-alpine

# set a working directory
WORKDIR /app
COPY app.py .
COPY requirements.txt .


# install only runtime dependencies
RUN pip install -r requirements.txt
RUN pip install gunicorn

ENV PORT 8000
EXPOSE 8000

ENTRYPOINT ["sh", "-c", "gunicorn app:app --bind 0.0.0.0:$PORT --workers 1"]
