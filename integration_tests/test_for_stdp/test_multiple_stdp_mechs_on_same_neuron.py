import pylab


cell_params_lif = {'cm'        : 0.25, # nF
                     'i_offset'  : 0.0,
                     'tau_m'     : 20.0,
                     'tau_refrac': 2.0,
                     'tau_syn_E' : 5.0,
                     'tau_syn_I' : 5.0,
                     'v_reset'   : -70.0,
                     'v_rest'    : -65.0,
                     'v_thresh'  : -50.0
                     }

def test_combinations(p, dependences):
    # Build STDP mechanisms for all combinations
    stdp_mechanisms = [p.STDPMechanism(timing_dependence=t, weight_dependence=w, mad=True) for (t, w) in dependences]
    #print zip(*dependences)
    
    # Create neural population
    neurons = p.Population(1, p.IF_curr_exp, cell_params_lif)
    
    # Loop through STDP mechanisms
    for s in stdp_mechanisms:
        # Create spike source
        spike_source = p.Population(1, p.SpikeSourcePoisson, { "rate": 10.0 })
        
        # Connect to neurons using STDP mechanism
        p.Projection(spike_source, neurons, p.OneToOneConnector(), synapse_dynamics=p.SynapseDynamics(slow=s))
    
    p.run(500)
    p.end(stop_on_board=True)

def test_failing_combination(p, dependences):
    try:
        test_combinations(p, dependences)
    except p.exceptions.SynapticConfigurationException as e:
        print "Fails as expected"

# Test combatible combinations# Test incompatible combinations with different timing params
print("Different timing parameters - Should fail")
if True:
    # **YUCK** no way of resetting sPyNnAkEr
    import spynnaker.pyNN as p
    p.setup()

    test_combinations(p, 
        [
            (p.SpikePairRule(tau_plus=16.7, tau_minus=12.7, nearest=True), p.AdditiveWeightDependence(w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005)),
            (p.SpikePairRule(tau_plus=16.7, tau_minus=12.7, nearest=True), p.AdditiveWeightDependence(w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005))
        ]
    )

# Test incompatible combinations with different timing params
print("Different timing parameters - Should fail")
if True:
    # **YUCK** no way of resetting sPyNnAkEr
    import spynnaker.pyNN as p
    p.setup()
    test_failing_combination(p, 
        [
            (p.SpikePairRule(tau_plus=20.0, tau_minus=12.7, nearest=True), p.AdditiveWeightDependence(w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005)),
            (p.SpikePairRule(tau_plus=16.7, tau_minus=12.7, nearest=True), p.AdditiveWeightDependence(w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005))
        ]
    )

print("Different weight parameters - Should fail")
if True:
    # **YUCK** no way of resetting sPyNnAkEr
    import spynnaker.pyNN as p
    p.setup()
    test_failing_combination(p, 
    [
        (p.SpikePairRule(tau_plus=16.7, tau_minus=12.7, nearest=True), p.AdditiveWeightDependence(w_min=0.0, w_max=1.0, A_plus=0.6, A_minus=0.005)),
        (p.SpikePairRule(tau_plus=16.7, tau_minus=12.7, nearest=True), p.AdditiveWeightDependence(w_min=0.0, w_max=1.0, A_plus=0.005, A_minus=0.005))
    ]
)