/*! \file
 *
 *
 * neuron-typedefs.h
 *
 *
 *  SUMMARY
 * \brief   Data type definitions for SpiNNaker Neuron-modelling
 *
 */

#ifndef __NEURON_TYPEDEFS_H__
#define __NEURON_TYPEDEFS_H__

#include <common-typedefs.h>
#include "maths-util.h"

// MC packets always have 32-bit keys and, optionally, 32-bit keyloads
// **TODO** these are about as common as stuff gets - move up!
typedef uint32_t key_t;
typedef uint32_t payload_t;

// Determine the type of an action potential
#ifndef __AP_T__

// Action potential always consist of a key
typedef key_t ap_t;

#define __AP_T__
#endif /*__AP_T__*/

// Determine the type of a gradient potential
#ifndef __GP_T__

// Unlike action potentials, gradient potentials (gp) also require a payload
typedef uint64_t gp_t;

//! \brief helper method to create a gradient potential from a key and a payload
//! \param[in] key: key of gradient potential
//! \param[in] payload: payload of gradient potential
//! \return gp_t: the complete gradient potential
static inline gp_t gp_create(key_t key, payload_t payload) {
    return (((gp_t)key) << 32) | (gp_t)(payload & UINT32_MAX);
}

//! \brief helper method to retrieve the key from a gradient potential
//! \param[in] gp: the gradient potential to get the key from
//! \return key_t: the key from the spike
static inline key_t gp_key(gp_t gp) {
    return ((key_t)(gp >> 32));
}

//! \brief helper method to retrieve the pay-load from a gradient potential
//! \param[in] gp: the gradient potential to get the pay-load from
//! \return payload_t: the pay-load from the gradient potential
static inline payload_t gp_payload (gp_t gp) {
    return ((payload_t)(gp & UINT32_MAX));
}

static inline payload_t gp_accum_to_payload(accum a) {
    union { payload_t p; accum a;} x; 
    x.a = a; 
    return (x.p); 
}
#define __GP_T__
#endif /*__GP_T__*/


// The type of a synaptic row
typedef address_t synaptic_row_t;

// The type of an input
typedef REAL input_t;

// The type of a state variable
typedef REAL state_t;


#endif /* __NEURON_TYPEDEFS_H__ */
