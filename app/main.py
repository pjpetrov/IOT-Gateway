from markupsafe import escape
import datetime
import redis
import flask_sock
from flask import Flask, render_template
import queue

app = Flask(__name__)
sock = flask_sock.Sock(app)

def event_handler(msg):
    sendRedisData()

cache = redis.Redis(host='redis', port=6379)
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

@app.route("/websocket_test")
def websocket_test():
    return render_template('websocket.html')

@app.route("/dump_redis")
def dump_redis():
    return render_template('dump_redis.html')

qs = []

@sock.route("/redis")
def redis_event(ws):
    q = queue.Queue()
    qs.append(q)
    #data = ws.receive()
    #if data == "disconnect":
    #    return
    while True:
        item = q.get();
        if item == None:
            break
        data = dumpRedis()
        try:
            ws.send(data)
            #if ws.receive() == "disconnect":
            #    break
        except:
            break

def sendRedisData():
    for q in qs:
        q.put('report')

def dumpRedis():
    redisData = ''
    for key in cache.scan_iter():
        redisData += key.decode("utf-8")  + '->' + cache.get(key).decode("utf-8")  + '<br>'
    return redisData
    

@sock.route('/test')
def test_event(ws):
    while True:
        data = ws.receive()
        ws.send(data)

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True, port=80)
