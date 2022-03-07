FROM alpine

RUN apk add python3-dev build-base linux-headers pcre-dev py3-pip \
            nginx shadow libuser supervisor ca-certificates gettext py-redis
# create non-root user
RUN pip install python-telegram-bot pymongo

RUN adduser --disabled-password --gecos '' bot
RUN gpasswd -a bot www-data

# custom Supervisord config
COPY config/supervisord.conf /etc/supervisord.conf
COPY app/ /app/

CMD ["/usr/bin/supervisord"]

WORKDIR /app
