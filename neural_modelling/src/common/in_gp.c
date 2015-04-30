/*
 * in_gp.c
 *
 *
 *  SUMMARY
 *    Incoming gradient potential handling for SpiNNaker neural modelling
 *
 *    The essential feature of the buffer used in this impementation is that it
 *    requires no critical-section interlocking --- PROVIDED THERE ARE ONLY TWO
 *    PROCESSES: a producer/consumer pair. If this is changed, then a more
 *    intricate implementation will probably be required, involving the use
 *    of enable/disable interrupts.
 *
 *  AUTHOR
 *    Dave Lester (david.r.lester@manchester.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) Dave Lester and The University of Manchester, 2013.
 *    All rights reserved.
 *    SpiNNaker Project
 *    Advanced Processor Technologies Group
 *    School of Computer Science
 *    The University of Manchester
 *    Manchester M13 9PL, UK
 *
 *  DESCRIPTION
 *
 *
 *  CREATION DATE
 *    10 December, 2013
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 10 December 2013
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "in_gp.h"

#include <debug.h>

static gp_t* buffer;
static uint32_t buffer_size;

static index_t output;
static index_t input;
static counter_t overflows;
static counter_t underflows;

// unallocated
//
// Returns the number of buffer slots currently unallocated
static inline counter_t unallocated() {
    return ((input - output) % buffer_size);
}

// allocated
//
// Returns the number of buffer slots currently allocated
static inline counter_t allocated() {
    return ((output - input - 1) % buffer_size);
}

// The following two functions are used to determine whether a
// buffer can have an element extracted/inserted respectively.
static inline bool non_empty() {
    return (allocated() > 0);
}

static inline bool non_full() {
    return (unallocated() > 0);
}

bool in_gp_initialize_buffer(uint32_t size) {
    buffer = (gp_t*) sark_alloc(1, size * sizeof(gp_t));
    if (buffer == NULL) {
        log_error("Cannot allocate in gradient potential buffer");
        return false;
    }
    buffer_size = size;
    input = size - 1;
    output = 0;
    overflows = 0;
    underflows = 0;
    return true;
}

uint32_t in_gp_n_in_buffer() {
    return allocated();
}

#define peek_next(a) ((a - 1) % buffer_size)

#define next(a) do {(a) = peek_next(a);} while (false)

bool in_gp_add(gp_t gp) {
    bool success = non_full();

    if (success) {
        buffer[input] = gp;
        next(input);
    } else
        overflows++;

    return (success);
}

bool in_gp_get_next(gp_t* gp) {
    bool success = non_empty();

    if (success) {
        next(output);
        *gp = buffer[output];
    } else
        underflows++;

    return (success);
}

bool in_gp_is_next_key_equal(key_t key) {
    if (non_empty()) {
        uint32_t peek_output = peek_next(output);
        if (gp_key(buffer[peek_output]) == key) {
            output = peek_output;
            return true;
        }
    }
    return false;
}

// The following two functions are used to access the locally declared
// variables.
counter_t in_gp_get_n_buffer_overflows() {
    return (overflows);
}

counter_t in_gp_get_n_buffer_underflows() {
    return (underflows);
}

#if LOG_LEVEL >= LOG_DEBUG
void in_gp_print_buffer() {
    counter_t n = allocated();
    index_t a;

    log_debug("buffer: input = %3u, output = %3u elements = %3u\n", input,
              output, n);
    printf("------------------------------------------------\n");

    for (; n > 0; n--) {
        a = (input + n) % buffer_size;
        log_debug("  %3u: key:%08x, payload:%08x\n", 
                  a, gp_key(buffer[a]), gp_payload(buffer[a]));
    }

    log_debug("------------------------------------------------\n");
}
#else // DEBUG
void in_gp_print_buffer() {
    skip();
}
#endif // DEBUG
