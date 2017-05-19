# -*- coding: utf-8 -*-
from utils import web_server_token, logger
import psutil
from threading import Thread
import Queue
import requests


class StatusWorker(Thread):
    def __init__(self, queue):
        self.queue = queue
        super(StatusWorker, self).__init__()

    def run(self):
        while True:
            address, sid, status = self.queue.get()
            url = 'http://{adr}/api/submission/update/'.format(adr=address)
            headers = {"Content-Type": "application/json"}
            data = {
                'token': web_server_token,
                'result': status,
                'submission_id': sid,
            }
            try:
                info = requests.post(url, headers=headers, json=data, timeout=2).json()
                logger.info(str(info))
            except Exception as e:
                logger.exception(e)
            finally:
                self.queue.task_done()

cpu_count = psutil.cpu_count()
que = Queue.Queue()
for cnt in range(cpu_count):
    worker = StatusWorker(que)
    worker.daemon = True
    worker.start()
logger.info('init update status env.')


def update_submission_status(address, sid, status):
    # print address, sid, status
    que.put([address, sid, status])
