import threading
import collections
import logging
import socket

logger = logging.getLogger(__name__)


class BufferSendThread(threading.Thread):

    def __init__(self, sdp_connection):
        threading.Thread.__init__(self)
        self._queue = collections.deque()
        self._queue_condition = threading.Condition()
        self._sdp_connection = sdp_connection
        self._done = False
        self._exited = False
        self.setDaemon(True)

    def stop(self):
        """
        method to kill the thread
        """
        logger.info("[_buffer send thread] Stopping")
        self._queue_condition.acquire()
        self._done = True
        self._queue_condition.notify()
        self._queue_condition.release()

        self._queue_condition.acquire()
        while not self._exited:
            self._queue_condition.wait()
        self._queue_condition.release()

    def run(self):
        """
        runs by just pulling receive requests and executing them
        """
        logger.info("[buffer send thread] starting")
        while not self._done:
            self._queue_condition.acquire()
            while len(self._queue) == 0 and not self._done:
                self._queue_condition.wait()
            request = None
            if not self._done:
                request = self._queue.pop()
            self._queue_condition.release()
            if request is not None:
                self._handle_request(request)
        self._queue.append(None)
        self._queue_condition.acquire()
        self._exited = True
        self._queue_condition.notify()
        self._queue_condition.release()

    def add_request(self, request):
        """ adds a request to the tiger munching queue

        :param request:
        :return:
        """
        self._queue_condition.acquire()
        self._queue.append(request)
        self._queue_condition.notify()
        self._queue_condition.release()

    def _handle_request(self, request):
        """ handles a request from the munched queue by transmitting a chunk of
        memory to a buffer

        :param request:
        :return:
        """