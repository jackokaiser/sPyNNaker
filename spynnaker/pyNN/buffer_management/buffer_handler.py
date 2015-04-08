from spinnman import exceptions as spinnman_exceptions
from spinnman import constants

import threading
import logging

logger = logging.getLogger(__name__)


class BufferHandler(object):

    def __init__(self, tags, transceiver):
        self._tags = tags
        self._transceiver = transceiver

        # Set of (ip_address, port) that are being listened to for the tags
        self._seen_tags = set()

        # Lock to avoid multiple messages being processed at the same time
        self._thread_locks = dict()

        # Set of function listening on particular packet types
        self._registered_listeners = dict()

    def register_listener(self, class_listened, function, tag):
        if (tag.ip_address, tag.port) not in self._seen_tags:
            self._seen_tags.add((tag.ip_address, tag.port))
            self._transceiver.register_listener(
                self.receive_buffer_command_message, tag.port,
                constants.CONNECTION_TYPE.UDP_IPTAG,
                constants.TRAFFIC_TYPE.EIEIO_COMMAND,
                hostname=tag.ip_address)

        if class_listened not in self._registered_listeners:
            self._registered_listeners[class_listened] = list([function])
            self._thread_locks[class_listened] = threading.Lock()
        else:
            # Do not register twice the same listener function
            if function not in self._registered_listeners[class_listened]:
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
