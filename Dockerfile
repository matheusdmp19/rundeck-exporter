FROM python:3.9.16-alpine3.16

WORKDIR /app

COPY requirements.txt /app
COPY /src/* /app

RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt && rm /app/requirements.txt

ENTRYPOINT ["python", "/app/rundeck_exporter.py"]
