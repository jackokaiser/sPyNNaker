#include "../../spin-neuron-impl.h"
#include "post_events_impl.h"

//---------------------------------------
// Globals
//---------------------------------------
post_event_history_t *post_event_history = NULL;

//---------------------------------------
// Functions
//---------------------------------------
void post_init_buffers()
{
  post_event_history = (post_event_history_t*)spin1_malloc(num_neurons * sizeof(post_event_history_t));

  // Check allocations succeeded
  if(post_event_history == NULL)
  {
    sentinel("Unable to allocate %u bytes global STDP structures for %u neurons - Out of DTCM", num_neurons * sizeof(post_event_history_t), num_neurons);
  }
  
  // Loop through neurons
  for(uint32_t n = 0; n < num_neurons; n++)
  {
    // Add initial placeholder entry to buffer
    post_event_history[n].times[0] = 0;
    post_event_history[n].traces[0] = timing_get_initial_post_trace();
    post_event_history[n].count_minus_one = 0;
  }
}