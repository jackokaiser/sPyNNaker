#ifndef _IN_SPIKES_H_
#define _IN_SPIKES_H_

#include "neuron-typedefs.h"

// initialize_spike_buffer
//
// This function initializes the input spike buffer.
// It configures:
//    buffer:     the buffer to hold the spikes (initialized with size spaces)
//    input:      index for next spike inserted into buffer
//    output:     index for next spike extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.
bool in_ap_initialize_buffer(uint32_t size);

bool in_ap_add(ap_t ap);

bool in_ap_get_next(ap_t* ap);

bool in_ap_is_next_key_equal(ap_t ap);

counter_t in_ap_get_n_buffer_overflows();

counter_t in_ap_get_n_buffer_underflows();

void in_ap_print_buffer();

#endif // _IN_SPIKES_H_
