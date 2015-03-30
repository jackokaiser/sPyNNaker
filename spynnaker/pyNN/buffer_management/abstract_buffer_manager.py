from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractBufferManager(object):
    """Abstract manager to handle buffer of spikes from host to the
    SpiNNaker machine, and/or to the host form the SpiNNaker machine"""

    def __init__(self, placements, routing_info, tags, transceiver):
        self._placements = placements
        self._routing_info = routing_info
        self._tags = tags
        self._transceiver = transceiver