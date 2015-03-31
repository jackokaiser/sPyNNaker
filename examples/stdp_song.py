import math, numpy, pylab, random, sys
import pylab

spinnaker = False

if spinnaker:
    import spynnaker.pyNN as sim
else:
    import nest
    import pyNN.nest as sim

#-------------------------------------------------------------------
# This example uses the sPyNNaker implementation of pair-based STDP
# To reproduce the weight distributions found by Song, Miller and Abbott
#-------------------------------------------------------------------
num_exc_inputs = 1000
num_inh_inputs = 200

input_exc_rate = 10.0
input_inh_rate = 10.0

mad = True
duration = 10 * 1000
a_plus = 0.005
a_minus_ratio = 1.05
w_max = 0.00015
#w_max = 0.00016275
record_analogue = True

w_inh = w_max * 3.0

# Population parameters
model = sim.IF_curr_exp
cell_params = {
    'cm'        : 0.2, # nF
    'i_offset'  : 0.0,
    'tau_m'     : 20.0,
    'tau_refrac': 1.0,
    'tau_syn_E' : 5.0,
    'tau_syn_I' : 5.0,
    'v_reset'   : -60.0,
    'v_rest'    : -70.0,
    'v_thresh'  : -54.0,
    #'e_rev_E'   : 0.0,
    #'e_rev_I'   : -70.0,
}

# SpiNNaker setup
sim.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

# Populations
exc_pre_pop = sim.Population(num_exc_inputs, sim.SpikeSourcePoisson, {'rate': input_exc_rate, 'start':0, 'duration':duration})
inh_pre_pop = sim.Population(num_inh_inputs, sim.SpikeSourcePoisson, {'rate': input_inh_rate, 'start':0, 'duration':duration})
post_pop = sim.Population(1, model, cell_params)

post_pop.record()
if record_analogue:
    post_pop.record_v()
    post_pop.record_gsyn()

# Plastic Connection between pre_pop and post_pop
stdp_model = sim.STDPMechanism(
    timing_dependence = sim.SpikePairRule(tau_plus=20.0, tau_minus=20.0),
    weight_dependence = sim.AdditiveWeightDependence(w_min=0.0, w_max=w_max, A_plus=a_plus, A_minus=(a_plus * a_minus_ratio)),
    #mad=mad
)

sim.Projection(inh_pre_pop, post_pop, 
               sim.AllToAllConnector(weights=w_inh), 
               target="inhibitory")

projection = sim.Projection(exc_pre_pop, post_pop, 
                            sim.AllToAllConnector(weights=w_max),
                            target="excitatory",
                            synapse_dynamics=sim.SynapseDynamics(slow=stdp_model))

print("Simulating for %us" % (duration / 1000))

# Run simulation
sim.run(duration)

# Get spikes
post_spikes = post_pop.getSpikes(compatible_output=True)

# Get weight from projection
end_w = projection.getWeights(format="list")

if record_analogue:
    voltages = post_pop.get_v()

print("Post-synaptic firing rate %fHz" % (float(len(post_spikes)) / (float(duration) / 1000.0)))

# End simulation
sim.end()

#-------------------------------------------------------------------
# Plot weight distribution
#-------------------------------------------------------------------
def plot_trace(trace, axis, title, y_axis_label, colour):
    axis.plot([t[2] for t in trace], color=colour) 
    axis.set_xlabel('Time/ms')
    axis.set_ylabel(y_axis_label)
    axis.set_title(title)

def plot_hist(weights, axis):
    axis.set_xlabel("w")
    axis.set_ylabel("Fraction in bin")
    axis.hist(weights, 50, normed=1)

#if spinnaker:
#    numpy.save("spinnaker_voltages.npy", voltages)
#else:
#    numpy.save("nest_voltages.npy", voltages)

# Calculate deltas from end weights
ratio_w = [w / w_max for w in end_w]

# Plot weight histogram
if record_analogue:
    figure, axes = pylab.subplots(2)
    plot_hist(ratio_w, axes[0])
    plot_trace(voltages, axes[1], "v", "v", "red")
else:
    figure, axis = pylab.subplots()
    plot_hist(ratio_w, axis)
    
pylab.show()