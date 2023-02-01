FROM python:3.9.10

WORKDIR /opt
COPY requirements.txt requirements.txt
RUN apt update && apt install -y build-essential
RUN python -m pip install -r requirements.txt --no-cache-dir --no-deps
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
