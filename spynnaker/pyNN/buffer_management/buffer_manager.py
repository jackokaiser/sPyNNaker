from spinnman import exceptions as spinnman_exceptions

import threading
import logging

logger = logging.getLogger(__name__)


class BufferManager(object):

    def __init__(self):
        self._thread_locks = dict()
        self._registered_listeners = dict()
        pass

    def register_listener(self, class_listened, function):
        if class_listened not in self._registered_listeners:
            self._registered_listeners[class_listened] = list([function])
            self._thread_locks[class_listened] = threading.Lock()
        else:
            self._registered_listeners[class_listened].append(function)

    def receive_buffer_command_message(self, packet):
        """ received a eieio message from the port which this manager manages
        and locates what requests are required from it.

        :param packet: the class related to the message received
        :type packet:
        :return:
        """
        if type(packet) in self._registered_listeners.keys():
            with self._thread_locks[type(packet)]:
                for listener in self._registered_listeners[type(packet)]:
                    listener(packet)
        else:
            raise spinnman_exceptions.SpinnmanInvalidPacketException(
                    packet.__class__,
                    "The command packet is invalid for buffer management")

        # with self._thread_lock:
        #     if isinstance(packet, SpinnakerRequestBuffers):
        #
        #
        #     elif isinstance(packet, SpinnakerRequestReadData):
        #         pass
        #     else:
        #         raise spinnman_exceptions.SpinnmanInvalidPacketException(
        #             packet.__class__,
        #             "The command packet is invalid for buffer management")
