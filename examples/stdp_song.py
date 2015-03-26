import math, numpy, pylab, random, sys
import pylab
import spynnaker.pyNN as sim

#-------------------------------------------------------------------
# This example uses the sPyNNaker implementation of pair-based STDP
# To reproduce the weight distributions found by Song, Miller and Abbott
#-------------------------------------------------------------------
#-------------------------------------------------------------------
# Common parameters
#-------------------------------------------------------------------
num_inputs = 1000
input_rate = 10.0
mad = True
duration = 100 * 1000
a_plus = 0.005
a_minus_ratio = 1.05
w_max = 0.025

# Population parameters
model = sim.IF_curr_exp
cell_params = {'cm'        : 0.25, # nF
                'i_offset'  : 0.0,
                'tau_m'     : 20.0,
                'tau_refrac': 1.0,
                'tau_syn_E' : 5.0,
                'tau_syn_I' : 5.0,
                'v_reset'   : -70.0,
                'v_rest'    : -70.0,
                'v_thresh'  : -54.0
                }

# SpiNNaker setup
sim.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

#-------------------------------------------------------------------
# Experiment loop
#-------------------------------------------------------------------
# Populations
pre_pop = sim.Population(num_inputs, sim.SpikeSourcePoisson, {'rate': input_rate, 'start':0, 'duration':duration})
post_pop = sim.Population(1, model, cell_params)

post_pop.record()
post_pop.record_gsyn()
post_pop.record_v()

# Plastic Connection between pre_pop and post_pop
stdp_model = sim.STDPMechanism(
    timing_dependence = sim.SpikePairRule(tau_plus=20.0, tau_minus=20.0, nearest=False),
    weight_dependence = sim.AdditiveWeightDependence(w_min=0.0, w_max=w_max, A_plus=a_plus, A_minus=(a_plus * a_minus_ratio)),
    mad=mad
)

projection = sim.Projection(pre_pop, post_pop, sim.AllToAllConnector(weights=w_max),
        synapse_dynamics=sim.SynapseDynamics(slow=stdp_model)
    )

print("Simulating for %us" % (duration / 1000))

# Run simulation
sim.run(duration)

# Get spikes
post_spikes = post_pop.getSpikes(compatible_output=True)

print("Post-synaptic firing rate %fHz" % (float(len(post_spikes)) / (float(duration) / 1000.0)))


# Get weight from projection
end_w = projection.getWeights(format="list")

voltages = post_pop.get_v()
currents = post_pop.get_gsyn()

# End simulation on SpiNNaker
sim.end(stop_on_board=True)

#-------------------------------------------------------------------
# Plot weight distribution
#-------------------------------------------------------------------
def plot_trace(trace, axis, title, y_axis_label, colour):
    axis.plot([t[2] for t in trace], color=colour) 
    axis.set_xlabel('Time/ms')
    axis.set_ylabel(y_axis_label)
    axis.set_title(title)
    
# Calculate deltas from end weights
ratio_w = [w / w_max for w in end_w]

# Plot STDP curve
figure, axis = pylab.subplots(3)
axis[0].set_xlabel("w")
axis[0].set_ylabel("Fraction in bin")
axis[0].hist(ratio_w, 50, normed=1)

plot_trace(voltages, axis[1], "v", "v", "red")
plot_trace(currents, axis[2], "i", "i", "blue")
pylab.show()