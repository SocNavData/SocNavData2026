# sudo docker build -t surveyservice . && sudo docker run -it --net=host --rm -v $(pwd)/survey_storage:/storage surveyservice 

FROM python:3.12-slim

RUN apt-get update && apt-get install -y nginx certbot python3-certbot-nginx && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r /requirements.txt
RUN mkdir -p /app/static
COPY videos /app/static/videos

COPY app /app

WORKDIR /app
EXPOSE 5421
ENV FLASK_APP=/app/app.py
CMD ["gunicorn", "--bind", "0.0.0.0:5421", "--keyfile", "privkey.pem", "--certfile", "cert.pem", "app:app"]
#CMD ["gunicorn", "--bind", "0.0.0.0:5421", "app:app"]


