FROM alpine

RUN apk add python3 py3-pip supervisor py-redis py3-requests libuser shadow
# create non-root user

RUN adduser --disabled-password --gecos '' img
RUN gpasswd -a img www-data

# custom Supervisord config
COPY config/supervisord.conf /etc/supervisord.conf
COPY app/ /app/

CMD ["/usr/bin/supervisord"]
WORKDIR /app
