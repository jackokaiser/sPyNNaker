from spinnman.messages.eieio.command_messages.flush_data_completed import \
    FlushDataCompleted
from spinnman.messages.eieio.command_messages.spinnaker_request_read_data \
    import SpinnakerRequestReadData
from spynnaker.pyNN.buffer_management.abstract_buffer_manager import \
    AbstractBufferManager
import logging
from spynnaker.pyNN.buffer_management.storage_objects.buffered_receiving_subvertex import \
    BufferedReceivingSubvertex

logger = logging.getLogger(__name__)

# The total number of sequence numbers
_N_SEQUENCES = 256


class BufferReceivingToHostManager(AbstractBufferManager):

    def __init__(self, placements, routing_info, tags, transceiver,
                 buffer_handler):
        AbstractBufferManager.__init__(
            self, placements, routing_info, tags, transceiver, buffer_handler)
        self._receiver_vertices = dict()
        self._sequence_number_for_vertices = dict()
        self._vertex_data = dict()

    def add_receiver_vertex(self, manageable_vertex):
        """ adds a partitioned vertex into the managed list for vertices
        which require buffers to be extracted from them during runtime

        :param manageable_vertex: the vertex to be managed
        :return:
        """
        tag = self._tags.get_ip_tags_for_vertex(manageable_vertex)[0]
        self._buffer_handler.register_listener(
            SpinnakerRequestReadData, self.packet_listener, tag)
        self._buffer_handler.register_listener(
            FlushDataCompleted, self.flush_command_listener, tag)
        subvertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for subvertex in subvertices:
            placement = \
                self._placements.get_placement_of_subvertex(subvertex)
            self._receiver_vertices[(placement.x, placement.y, placement.p)] = \
                subvertex
            self._sequence_number_for_vertices[(placement.x,
                                                placement.y,
                                                placement.p)] = \
                (_N_SEQUENCES - 1)
            self._vertex_data[(placement.x, placement.y, placement.p)] = \
                BufferedReceivingSubvertex()

    def packet_listener(self, packet):
        # a SpinnakerRequestReadData is received - read corresponding bit of
        # memory and confirm
        sequence_no = packet.sequence_no

        n_requests = packet.number_of_requests
        for n in xrange(n_requests):
            x = packet.x
            y = packet.y
            start_address = packet.start_address(n)
            length = packet.space_to_be_read(n)
            data = self._transceiver.read_memory(x, y, start_address, length)

    def flush_command_listener(self, packet):
        pass