FROM python:3.9.16-alpine3.16

WORKDIR /app

COPY requirements.txt /app
COPY rundeck_exporter.py /app

RUN pip install --no-cache-dir --disable-pip-version-check -r /app/requirements.txt

ENTRYPOINT ["python", "/app/rundeck_exporter.py"]
