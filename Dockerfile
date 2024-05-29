FROM alpine:latest

WORKDIR /app

COPY . .

ENV PORT=5000
ENV MODE=PROD
ENV DB_CONNECTION=mysql://root:root@172.0.0.3/tic_tac_toe_dev 
ENV REDIS_URL=172.0.0.4
ENV GAME_EXPIRE_TIME=60

RUN apk update \
    && apk add --virtual build-deps gcc python3-dev musl-dev \
    && apk add mariadb-dev \
    && apk add python3 py3-pip


# Set MySQL client flags
ENV MYSQLCLIENT_CFLAGS="-I/usr/include/mysql"
ENV MYSQLCLIENT_LDFLAGS="-L/usr/lib -lmysqlclient"


RUN python3 -m venv /venv/game-env
RUN . /venv/game-env/bin/activate && pip install -r requirements.txt

EXPOSE 5000

CMD ["/venv/game-env/bin//python3", "main.py"]