#ifndef _IN_GP_H_
#define _IN_GP_H_

#include "neuron-typedefs.h"

// initialize_gp_buffer
//
// This function initializes the input gradient potential buffer.
// It configures:
//    buffer:     the buffer to hold the spikes (initialized with size spaces)
//    input:      index for next spike inserted into buffer
//    output:     index for next spike extracted from buffer
//    overflows:  a counter for the number of times the buffer overflows
//    underflows: a counter for the number of times the buffer underflows
//
// If underflows is ever non-zero, then there is a problem with this code.
bool in_gp_initialize_buffer(uint32_t size);

bool in_gp_add(gp_t gp);

bool in_gp_get_next(gp_t *gp);

bool in_gp_is_next_key_equal(key_t key);

counter_t in_gp_get_n_buffer_overflows();

counter_t in_gp_get_n_buffer_underflows();

void in_gp_print_buffer();

#endif // _IN_GP_H_
