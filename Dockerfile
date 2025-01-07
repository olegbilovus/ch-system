FROM python:3.12-slim AS install-dependencies

RUN apt-get update &&  \
    apt-get install -y --no-install-recommends build-essential gcc libpq-dev && \
    apt-get clean && \
    python -m venv /opt/venv

ENV PATH="/opt/venv/bin:$PATH"

COPY requirements.txt .
RUN pip install -r requirements.txt

FROM python:3.12-slim

RUN useradd -m app && \
    apt-get update &&  \
    apt-get install -y --no-install-recommends libpq-dev && \
    apt-get clean

USER app

COPY --from=install-dependencies /opt/venv /opt/venv

WORKDIR /app

COPY . .

ENV PATH="/opt/venv/bin:$PATH"

ENV PYTHONPATH="$PYTHONPATH:/app/chsystem/utility/"
ENV PYTHONPATH="$PYTHONPATH:/app/chsystem/database/"

ENTRYPOINT [ "python3"]
