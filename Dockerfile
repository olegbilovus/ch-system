FROM python:3.12

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

ENV PYTHONPATH="${PYTHONPATH}:/app/chsystem/utility/"
ENV PYTHONPATH="${PYTHONPATH}:/app/chsystem/database/"

ENTRYPOINT [ "python3"]
