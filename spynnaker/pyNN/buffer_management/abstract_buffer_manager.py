import threading
import struct
from spynnaker.pyNN.utilities import utility_calls

from spynnaker.pyNN.buffer_management.buffer_recieve_thread import \
    BufferReceiveThread

from abc import ABCMeta
from six import add_metaclass
from abc import abstractmethod


@add_metaclass(ABCMeta)
class AbstractBufferManager(object):

    def __init__(self, placements, routing_key_infos, graph_mapper,
                 port, local_host, transceiver):
        self._routing_infos = None
        self._partitioned_graph = None
        self._port = port
        self._local_host = local_host
        self._placements = placements
        self._routing_key_infos = routing_key_infos
        self._graph_mapper = graph_mapper
        self._transceiver = transceiver
        self._receive_thread = BufferReceiveThread()
        self._receive_thread.start()

    @property
    def port(self):
        return self._port

    @property
    def local_host(self):
        return self._local_host

    def kill_threads(self):
        """ turns off the threads as they are no longer needed

        :return:
        """
        self._receive_thread.stop()

    def _locate_region_address(self, region_id, sender_vertex):
        """ determines if the base address of the region has been set. if the
        address has not been set, it reads the address from the pointer table.
        ONLY PLACE WHERE THIS IS STORED!

        :param region_id: the region to locate the base address of
        :param sender_vertex: the partitionedVertex to which this region links
        :type region_id: int
        :type sender_vertex: instance of PartitionedVertex
        :return: None
        """
        base_address = sender_vertex.\
            sender_buffer_collection.get_region_base_address_for(region_id)
        if base_address is None:
            placement = \
                self._placements.get_placement_of_subvertex(sender_vertex)
            app_data_base_address = \
                self._transceiver.get_cpu_information_from_core(
                    placement.x, placement.y, placement.p).user[0]

            # Get the position of the region in the pointer table
            region_offset_in_pointer_table = utility_calls.\
                get_region_base_address_offset(app_data_base_address, region_id)
            region_offset_to_core_base = str(list(self._transceiver.read_memory(
                placement.x, placement.y,
                region_offset_in_pointer_table, 4))[0])
            base_address = struct.unpack("<I", region_offset_to_core_base)[0] \
                + app_data_base_address
            sender_vertex.sender_buffer_collection.\
                set_region_base_address_for(region_id, base_address)