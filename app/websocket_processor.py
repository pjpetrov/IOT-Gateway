import queue


class WebsocketProcessor(object):
    def __init__(self, redis):
        self._qs = []
        self._redis = redis

    def dumpRedis(self):
        redisData = ''
        for key in self._redis.scan_iter():
            value = self._redis.get(key)
            if value is not None:
                redisData += key.decode("utf-8")  + '->' + value.decode("utf-8")  + '<br>'
        return redisData

    def update(self):
        for q in self._qs:
            q.put('updatea')

    def processResult(self, id, result):
        if result == 'None':
            return
        cmd, value = result.split(',', 1)
        self._redis.set(id+cmd, value)

    def run(self, ws, id):
        q = queue.Queue()
        self._qs.append(q)
        while True:
            item = q.get();
            if item == None:
                break

            dataToSend = None

            if id is not None:
                if self._redis.exists(id):
                    value = self._redis.get(id)
                    if value is not None:
                        dataToSend = value.decode("utf-8")
                        self._redis.delete(id)
            else:
                dataToSend = self.dumpRedis()

            if dataToSend is not None:
                result = None
                try:
                    ws.send(dataToSend)
                    result = ws.receive()
                except:
                    break
                if result is not None:
                    self.processResult(id, result)


