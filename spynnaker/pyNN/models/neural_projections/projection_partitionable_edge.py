"""
ProjectionPartitionableEdge
"""
from pacman.model.partitionable_graph.multi_cast_partitionable_edge\
    import MultiCastPartitionableEdge
from pacman.utilities.progress_bar import ProgressBar

from spynnaker.pyNN.utilities import conf
from spynnaker.pyNN.models.neural_projections.projection_partitioned_edge \
    import ProjectionPartitionedEdge
from spynnaker.pyNN.models.neural_properties.synapse_dynamics.\
    fixed_synapse_row_io import FixedSynapseRowIO

from spinn_front_end_common.utilities.timer import Timer

import logging
import copy
logger = logging.getLogger(__name__)


class ProjectionPartitionableEdge(MultiCastPartitionableEdge):
    """
    the partitionable edge for a projection (high level edge)
    """

    def __init__(self, presynaptic_population, postsynaptic_population,
                 machine_time_step, connector=None, synapse_list=None,
                 synapse_dynamics=None, label=None):
        MultiCastPartitionableEdge.__init__(
            self, presynaptic_population._get_vertex,
            postsynaptic_population._get_vertex, label=label)

        self._connector = connector
        self._synapse_dynamics = synapse_dynamics
        self._synapse_list = synapse_list
        self._synapse_row_io = FixedSynapseRowIO()
        self._stored_synaptic_data_from_machine = None

        # If there are synapse dynamics for this connector, create a plastic
        # synapse list
        if synapse_dynamics is not None:
            self._synapse_row_io = synapse_dynamics.get_synapse_row_io()

    def create_subedge(self, presubvertex, postsubvertex, constraints=None,
                       label=None):
        """
        Creates a subedge from this edge
        """
        if constraints is None:
            constraints = list()
        constraints.extend(self.constraints)
        return ProjectionPartitionedEdge(presubvertex, postsubvertex,
                                         constraints)

    def get_max_n_words(self, vertex_slice=None):
        """
        Gets the maximum number of words for a subvertex at the end of the
        connection
        :param vertex_slice: the vertex slice for this vertex which contains \
        the lo and hi atoms for this slice
        """
        if vertex_slice is None:
            return max([self._synapse_row_io.get_n_words(
                synapse_row)
                for synapse_row in self._synapse_list.get_rows()])
        else:
            return max([self._synapse_row_io.get_n_words(
                synapse_row, vertex_slice)
                for synapse_row in self._synapse_list.get_rows()])

    def get_n_rows(self):
        """
        Gets the number of synaptic rows coming in to a subvertex at the end of
        the connection
        """
        return self._synapse_list.get_n_rows()

    def get_synapse_row_io(self):
        """
        Gets the row reader and writer
        """
        return self._synapse_row_io

    def get_synaptic_list_from_machine(self, graph_mapper, partitioned_graph,
                                       placements, transceiver, routing_infos):
        """
        Get synaptic data for all connections in this Projection from the
        machine.
        """
        if self._stored_synaptic_data_from_machine is None:
            timer = None
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer = Timer()
                timer.start_timing()

            logger.debug("Reading synapse data for edge between {} and {}"
                         .format(self._pre_vertex.label,
                                 self._post_vertex.label))
            subedges = \
                graph_mapper.get_partitioned_edges_from_partitionable_edge(
                    self)
            if subedges is None:
                subedges = list()

            synaptic_list = copy.copy(self._synapse_list)
            synaptic_list_rows = synaptic_list.get_rows()
            progress_bar = ProgressBar(
                len(subedges), "progress on reading back synaptic matrix")
            for subedge in subedges:
                n_rows = subedge.get_n_rows(graph_mapper)
                pre_vertex_slice = \
                    graph_mapper.get_subvertex_slice(subedge.pre_subvertex)
                post_vertex_slice = \
                    graph_mapper.get_subvertex_slice(subedge.post_subvertex)

                sub_edge_post_vertex = \
                    graph_mapper.get_vertex_from_subvertex(
                        subedge.post_subvertex)
                rows = sub_edge_post_vertex.get_synaptic_list_from_machine(
                    placements, transceiver, subedge.pre_subvertex, n_rows,
                    subedge.post_subvertex,
                    self._synapse_row_io, partitioned_graph,
                    routing_infos, subedge.weight_scales).get_rows()

                for i in range(len(rows)):
                    synaptic_list_rows[
                        i + pre_vertex_slice.lo_atom].set_slice_values(
                            rows[i], vertex_slice=post_vertex_slice)
                progress_bar.update()
            progress_bar.end()
            self._stored_synaptic_data_from_machine = synaptic_list
            if conf.config.getboolean("Reports", "outputTimesForSections"):
                timer.take_sample()

        return self._stored_synaptic_data_from_machine

    @property
    def synapse_dynamics(self):
        """

        :return: returns the synapse_dynamics for the edge
        """
        return self._synapse_dynamics

    @property
    def synapse_list(self):
        """

        :return: returns the synaptic list for the edge
        """
        return self._synapse_list

    def is_multi_cast_partitionable_edge(self):
        return True
