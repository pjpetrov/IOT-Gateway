from markupsafe import escape
import datetime
import redis
import flask_sock
from flask import Flask, render_template
import websocket_processor
import logging

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                            level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config['SOCK_SERVER_OPTIONS'] = {'ping_interval': 25}
sock = flask_sock.Sock(app)

cache = redis.Redis(host='redis', port=6379)
wsProcessor = websocket_processor.WebsocketProcessor(cache)

def event_handler(msg):
    wsProcessor.update()

pubsub = cache.pubsub()
# Set Config redis key expire listener
cache.config_set('notify-keyspace-events', 'Exsg')
pubsub.psubscribe(**{"__key*__:*": event_handler})
pubsub.run_in_thread(sleep_time=0.01)


@app.route("/add/<target>/<message>")
def add(target, message):
    cache.setex(target, datetime.timedelta(seconds=10), value=message)
    return f'Done'

@app.route("/get/<target>")
def get(target):
    val = cache.get(target)
    return f' {escape(val)}'

@app.route("/pop/<target>")
def pop(target):
    val = cache.get(target)
    cache.delete(target)
    return f' {escape(val)}'

@app.route("/dump_redis")
def dump_redis():
    return render_template('dump_redis.html')

@app.route("/client/<id>")
def client(id):
    return render_template('client.html', id=id)

@sock.route("/redis/<id>")
def redis_id(ws, id):
    logging.info("Websocket client connected: {}".format(id))
    wsProcessor.run(ws, id)

@sock.route("/redis")
def redis_event(ws):
    wsProcessor.run(ws, None)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
