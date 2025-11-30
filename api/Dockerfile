FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y libpq-dev gcc && rm -rf /var/lib/apt/lists/*


RUN pip install fastapi uvicorn sqlalchemy psycopg2-binary

COPY ./app.py /app/app.py

EXPOSE 80
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "80"]
