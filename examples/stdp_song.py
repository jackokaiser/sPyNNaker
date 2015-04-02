# Import modules
import math, numpy, pylab, random, sys
import pylab

# Import classes
from pyNN.random import NumpyRNG, RandomDistribution

# Import simulator
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

input_exc_rate = 15.0

mad = True
duration = 100 * 1000
a_plus = 0.01
a_minus_ratio = 1.05
w_max = 0.006

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
    'v_rest'    : -74.0,
    'v_thresh'  : -54.0,
}

# Create RNG and uniform weight distribution
rng = NumpyRNG()
exc_weight_distribution = RandomDistribution("uniform", (0.0, w_max))

# SpiNNaker setup
sim.setup(timestep=1.0, min_delay=1.0, max_delay=8.0)

# Populations
exc_pre_pop = sim.Population(num_exc_inputs, sim.SpikeSourcePoisson, {'rate': input_exc_rate, 'start':0, 'duration':duration})
post_pop = sim.Population(1, model, cell_params)

post_pop.record()

# Plastic Connection between pre_pop and post_pop
stdp_model = sim.STDPMechanism(
    timing_dependence = sim.SpikePairRule(tau_plus=20.0, tau_minus=20.0),
    weight_dependence = sim.AdditiveWeightDependence(w_min=0.0, w_max=w_max, A_plus=a_plus, A_minus=(a_plus * a_minus_ratio)),
    #mad=mad
)

projection = sim.Projection(exc_pre_pop, post_pop, 
                            sim.AllToAllConnector(weights=exc_weight_distribution),
                            target="excitatory",
                            synapse_dynamics=sim.SynapseDynamics(slow=stdp_model))

print("Simulating for %us" % (duration / 1000))

# Run simulation
sim.run(duration)

# Get spikes
post_spikes = post_pop.getSpikes(compatible_output=True)

# Get weight from projection
end_w = projection.getWeights(format="list")

print("Post-synaptic firing rate %fHz" % (float(len(post_spikes)) / (float(duration) / 1000.0)))

# End simulation
sim.end()

#-------------------------------------------------------------------
# Plot weight distribution
#-------------------------------------------------------------------
def plot_hist(weights, axis):
    axis.set_xlabel("w")
    axis.set_ylabel("Fraction in bin")
    axis.hist(weights, 20)

def plot_rates(spikes, axis, binsize=1000):
    bins = numpy.arange(0, duration + 1, binsize)
    histogram, bins = numpy.histogram(spikes[:,1], bins=bins)
    
    rates = histogram * (1000.0 / binsize)
    
    axis.plot(bins[0:-1], rates)

# Calculate deltas from end weights
ratio_w = [w / w_max for w in end_w]

# Plot weight histogram
figure, axes = pylab.subplots(2)
plot_hist(ratio_w, axes[0])
plot_rates(post_spikes, axes[1])
    
pylab.show()