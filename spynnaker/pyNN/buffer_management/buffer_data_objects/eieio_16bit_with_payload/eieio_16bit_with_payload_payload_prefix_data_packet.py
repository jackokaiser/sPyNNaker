from spinnman.messages.eieio.eieio_type_param import EIEIOTypeParam
from spynnaker.pyNN.buffer_management.abstract_eieio_packets.\
    abstract_eieio_data_packet import AbstractEIEIODataPacket


class EIEIO16BitWithPayloadPayloadPrefixDataPacket(AbstractEIEIODataPacket):

    def __init__(self, payload_prefix, data=None):
        if data is None:
            data = bytearray()

        AbstractEIEIODataPacket.__init__(
            self, EIEIOTypeParam.KEY_PAYLOAD_16_BIT,
            payload_base=payload_prefix, data=data)

    def insert_key_and_payload(self, key, payload):
        if self.get_available_count() > 0:  # there is space available
            AbstractEIEIODataPacket(self)._insert_key_and_payload(key, payload)
            self._length += self._element_size
            return True
        else:
            return False

    @property
    def payload_prefix(self):
        return AbstractEIEIODataPacket(self).payload_base

    @property
    def length(self):
        return self._length

    def is_data_packet(self):
        """
        handler for isinstance
        """
        return True