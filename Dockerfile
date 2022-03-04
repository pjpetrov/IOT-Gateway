FROM alpine

# disabled apks:
# uwsgi uwsgi-gevent3 uwsgi-python3 uwsgi-http py3-zope-component py3-gevent

RUN apk add python3-dev build-base linux-headers pcre-dev py3-pip \
            nginx shadow libuser supervisor ca-certificates gettext py-redis py3-gunicorn
# create non-root user
RUN pip install flask flask-sock

#RUN wget http://nginx.org/keys/nginx_signing.key \
#	&& apt-key add nginx_signing.key \
#	&& rm nginx_signing.key \
#	&& echo "deb http://nginx.org/packages/mainline/debian/ stretch nginx" >> /etc/apt/sources.list \
#	&& apt-get update \
#	&& apt-get install -y ca-certificates nginx gettext-base supervisor \x
#	&& rm -rf /var/lib/apt/lists/*

RUN adduser --disabled-password --gecos '' wsgi
RUN gpasswd -a wsgi www-data
RUN gpasswd -a nginx www-data
#RUN mkdir -p /var/cache/nginx

RUN chown -R nginx /var/log/nginx /var/lib/nginx  \
	&& touch /var/run/nginx.pid \
	&& chown -R nginx /var/run/nginx.pid 

EXPOSE 8080
EXPOSE 5000

# make NGINX run in foreground
RUN echo "daemon off;" >> /etc/nginx/nginx.conf
RUN cat > /etc/nginx/http.d/default
# update NGINX config
COPY docker-config/nginx.conf /etc/nginx/http.d/
# copy uWSGI ini file to enable default dynamic uwsgi process number
COPY docker-config/uwsgi.ini /etc/uwsgi/

# custom Supervisord config
COPY docker-config/supervisord.conf /etc/supervisord.conf
COPY docker-config/supervisord-kill.py /usr/bin/
COPY app/ /app/

CMD ["/usr/bin/supervisord"]

WORKDIR /app
