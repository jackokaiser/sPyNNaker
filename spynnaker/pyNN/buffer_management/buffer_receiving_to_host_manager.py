from spinnman.messages.eieio.command_objects.spinnaker_request_read_data import \
    SpinnakerRequestReadData
from spynnaker.pyNN.buffer_management.abstract_buffer_manager import \
    AbstractBufferManager


class BufferReceivingToHostManager(AbstractBufferManager):

    def __init__(self, placements, routing_key_infos, graph_mapper,
                 port, local_host, transceiver, buffer_manager):
        self._receive_vertices = dict()
        self._buffer_manager = buffer_manager
        self._buffer_manager.register_listener(
            SpinnakerRequestReadData, self.packet_listener)
        AbstractBufferManager.__init__(
            self, placements, routing_key_infos, graph_mapper, port,
            local_host, transceiver)

    def add_receiver_vertex(self, manageable_vertex):
        """ adds a partitioned vertex into the managed list for vertices
        which require buffers to be extracted from them during runtime

        :param manageable_vertex: the vertex to be managed
        :return:
        """
        vertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for vertex in vertices:
            placement = \
                self._placements.get_placement_of_subvertex(vertex)
            self._receive_vertices[(placement.x, placement.y, placement.p)] = \
                vertex

    def packet_listener(self, packet):
        pass