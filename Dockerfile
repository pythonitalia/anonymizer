FROM python:3.10-bullseye

RUN apt update && \
    apt install -y lsb-release && \
    sh -c 'echo "deb http://apt.postgresql.org/pub/repos/apt $(lsb_release -cs)-pgdg main" > /etc/apt/sources.list.d/pgdg.list' && \
    wget --quiet -O - https://www.postgresql.org/media/keys/ACCC4CF8.asc | apt-key add - && \
    apt update && \
    apt -y install wget ca-certificates postgresql-client-14 postgresql-14 postgresql-contrib-14

RUN pip install poetry==1.2.0
RUN poetry config virtualenvs.in-project true

COPY pyproject.toml poetry.lock /app/

WORKDIR /app/

RUN poetry install

COPY . /app

RUN echo "local all all trust" > /etc/postgresql/14/main/pg_hba.conf
