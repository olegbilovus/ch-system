FROM python:latest

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip3 install -r requirements.txt

COPY . .

CMD [ "bash", "init.sh" , "chsystem/discord/discordBot.py"]
