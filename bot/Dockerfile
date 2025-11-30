FROM python:3.13.7-slim-bookworm

ARG APP_HOME=/bot

RUN apt-get update && \
    apt-get install --no-install-recommends -y libpq-dev build-essential && \
    apt-get clean

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONBUFFERED=1

WORKDIR ${APP_HOME}

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . ${APP_HOME}

CMD ["python3", "__main__.py"]
