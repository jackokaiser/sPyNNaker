import logging

from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN import exceptions as spynnaker_exceptions
from spynnaker.pyNN.buffer_management.abstract_buffer_manager import \
    AbstractBufferManager

from spinnman.messages.eieio.command_objects.spinnaker_request_buffers import \
    SpinnakerRequestBuffers
from spinnman.messages.eieio.command_objects.padding_request import \
    PaddingRequest
from spinnman.messages.eieio.command_objects.event_stop_request \
    import EventStopRequest
from spinnman.messages.eieio.command_objects.host_send_sequenced_data\
    import HostSendSequencedData
from spinnman.messages.eieio.command_objects.start_requests \
    import StartRequests
from spinnman.messages.eieio.command_objects.stop_requests \
    import StopRequests
from spinnman.messages.sdp.sdp_header import SDPHeader
from spinnman.messages.sdp.sdp_message import SDPMessage
from spinnman.messages.sdp.sdp_flag import SDPFlag


logger = logging.getLogger(__name__)


class BufferSendingFromHostManager(AbstractBufferManager):

    def __init__(self, placements, routing_key_infos, graph_mapper,
                 port, local_host, transceiver, buffer_manager):
        self._sender_vertices = dict()
        self._buffer_manager = buffer_manager
        self._buffer_manager.register_listener(
            SpinnakerRequestBuffers, self.packet_listener)
        AbstractBufferManager.__init__(
            self, placements, routing_key_infos, graph_mapper, port,
            local_host, transceiver)

    def packet_listener(self, packet):
        key = (packet.x, packet.y, packet.p)
        if key in self._sender_vertices.keys():
            logger.debug("received packet sequence: {1:d}, "
                         "space available: {0:d}".format(
                             packet.space_available,
                             packet.sequence_no))
            data_requests = \
                self._sender_vertices[key].get_next_set_of_packets(
                    packet.space_available, packet.region_id,
                    packet.sequence_no, self._routing_infos,
                    self._partitioned_graph)
            # data_requests = list()
            space_used = 0
            for buffers in data_requests:
                logger.debug("packet to be sent length: {0:d}".format(
                    buffers.length))
                space_used += buffers.length
            logger.debug("received packet sequence: {3:d}, "
                         "space available: {0:d}, data requests: "
                         "{1:d}, total length: {2:d}".format(
                             packet.space_available,
                             len(data_requests),
                             space_used, packet.sequence_no))
            if len(data_requests) != 0:
                for buffers in data_requests:
                    self._send_request(
                        packet.x, packet.y, packet.p, buffers)
                    # data_request = {'data': buffers,
                    #                 'x': packet.x,
                    #                 'y': packet.y,
                    #                 'p': packet.p}
                    # self._add_request(data_request)

    def add_sender_vertex(self, manageable_vertex):
        """ adds a partitioned vertex into the managed list for vertices
        which require buffers to be sent to them during runtime

        :param manageable_vertex: the vertex to be managed
        :return:
        """
        vertices = \
            self._graph_mapper.get_subvertices_from_vertex(manageable_vertex)
        for vertex in vertices:
            placement = \
                self._placements.get_placement_of_subvertex(vertex)
            self._sender_vertices[(placement.x, placement.y, placement.p)] = \
                vertex

    def contains_sender_vertices(self):
        """ helper method which determines if the buffer manager is currently
        managing vertices which require buffers to be sent to them

        :return:
        """
        if len(self._sender_vertices) == 0:
            return False
        return True

    def load_initial_buffers(self, routing_infos, partitioned_graph):
        """ takes all the sender vertices and loads the initial buffers.
            In addition stores the routing infos and the partitioned graph
            objects, after they are generated, when loading the initial buffers

        :param routing_infos:
        :param partitioned_graph: A partitioned_graph of partitioned vertices \
        and edges from the partitionable_graph
        :type partitioned_graph: :py:class: \
            `pacman.model.subgraph.subgraph.Subgraph`
        :return: None
        """
        self._routing_infos = routing_infos
        self._partitioned_graph = partitioned_graph
        progress_bar = ProgressBar(len(self._sender_vertices),
                                   "on loading buffer dependant vertices")
        for send_vertex_key in self._sender_vertices.keys():
            sender_vertex = self._sender_vertices[send_vertex_key]
            for region_id in \
                    sender_vertex.sender_buffer_collection.regions_managed:
                self._handle_a_initial_buffer_for_region(
                    region_id, sender_vertex)
            progress_bar.update()
        progress_bar.end()

    def _handle_a_initial_buffer_for_region(self, region_id, sender_vertex):
        """ collects the initial regions buffered data and transmits it to the
        board based chip's memory

        :param region_id: the region id to load a buffer for
        :type region_id: int
        :param sender_vertex: the vertex to load a buffer for
        :type sender_vertex: a instance of partitionedVertex
        :return:
        """
        region_size = \
            sender_vertex.sender_buffer_collection.get_size_of_region(
                region_id)

        # create a buffer packet to emulate core asking for region data
        placement_of_partitioned_vertex = \
            self._placements.get_placement_of_subvertex(sender_vertex)

        # create a list of buffers to be loaded on the machine, given the region
        # the size and the sequence number
        data_requests = sender_vertex.get_next_set_of_packets(
            region_size, region_id, None, self._routing_infos,
            self._partitioned_graph)

        # fetch region base address
        self._locate_region_address(region_id, sender_vertex)

        # check if list is empty and if so raise exception
        if len(data_requests) == 0:
            raise spynnaker_exceptions.BufferableRegionTooSmall(
                "buffer region {0:d} in subvertex {1:s} is too small to "
                "contain any type of packet".format(region_id, sender_vertex))
        space_used = 0
        base_address = sender_vertex.sender_buffer_collection.\
            get_region_base_address_for(region_id)
        # send each data request
        for data_request in data_requests:
            # write memory to chip
            logger.debug("writing one packet with length {0:d}".format(
                data_request.length))
            data_to_be_written = data_request.get_eieio_message_as_byte_array()
            self._transceiver.write_memory(
                placement_of_partitioned_vertex.x,
                placement_of_partitioned_vertex.y,
                base_address + space_used, data_to_be_written)

            space_used += len(data_to_be_written)

        # add padding at the end of memory region during initial memory write
        length_to_be_padded = region_size - space_used
        padding_packet = PaddingRequest(length_to_be_padded)
        padding_packet_bytes = padding_packet.get_eieio_message_as_byte_array()
        logger.debug("writing padding with length {0:d}".format(
            len(padding_packet_bytes)))
        self._transceiver.write_memory(
            placement_of_partitioned_vertex.x,
            placement_of_partitioned_vertex.y,
            base_address + space_used, padding_packet_bytes)

    # # to be copied in the buffered in buffer manager
    #
    # @staticmethod
    # def create_eieio_messages_from(buffer_data):
    #     """this method takes a collection of buffers in the form of a single
    #     byte array and interprets them as eieio messages and returns a list of
    #     eieio messages
    #
    #     :param buffer_data: the byte array data
    #     :type buffer_data: LittleEndianByteArrayByteReader
    #     :rtype: list of EIEIOMessages
    #     :return: a list containing EIEIOMessages
    #     """
    #     messages = list()
    #     while not buffer_data.is_at_end():
    #         eieio_packet = create_class_from_reader(buffer_data)
    #         messages.append(eieio_packet)
    #     return messages

    def _send_request(self, x, y, p, buffers):
        """ handles a request from the munched queue by transmitting a chunk of
        memory to a buffer

        :param x:
        :param y:
        :param p:
        :param buffers: the content of this message
        :return:
        """
        if isinstance(buffers, (HostSendSequencedData, StopRequests,
                                StartRequests, EventStopRequest)):
            eieio_message_as_byte_array = \
                buffers.get_eieio_message_as_byte_array()
            sdp_header = SDPHeader(destination_chip_x=x,
                                   destination_chip_y=y,
                                   destination_cpu=p,
                                   flags=SDPFlag.REPLY_NOT_EXPECTED,
                                   destination_port=1)
            sdp_message = \
                SDPMessage(sdp_header, eieio_message_as_byte_array)
            self._transceiver.send_sdp_message(sdp_message)
        else:
            raise spynnaker_exceptions.ConfigurationException(
                "this type of request is not suitable for this thread. Please "
                "fix and try again")
