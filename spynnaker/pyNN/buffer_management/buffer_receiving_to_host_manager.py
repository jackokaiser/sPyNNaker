from spinnman.messages.eieio.command_messages.spinnaker_request_read_data import \
    SpinnakerRequestReadData
from spynnaker.pyNN.buffer_management.abstract_buffer_manager import \
    AbstractBufferManager


class BufferReceivingToHostManager(AbstractBufferManager):

    def __init__(self, placements, routing_info, tags, transceiver,
                 buffer_handler):
        AbstractBufferManager.__init__(
            self, placements, routing_info, tags, transceiver, buffer_handler)
        self._receiver_vertices = dict()

    def add_receiver_vertex(self, manageable_vertex):
        """ adds a partitioned vertex into the managed list for vertices
        which require buffers to be extracted from them during runtime

        :param manageable_vertex: the vertex to be managed
        :return:
        """
        tag = self._tags.get_ip_tags_for_vertex(manageable_vertex)[0]
        self._buffer_handler.register_listener(
            SpinnakerRequestReadData, self.packet_listener, tag)
        subvertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for subvertex in subvertices:
            placement = \
                self._placements.get_placement_of_subvertex(subvertex)
            self._receiver_vertices[(placement.x, placement.y, placement.p)] = \
                subvertex

    def packet_listener(self, packet):
        pass