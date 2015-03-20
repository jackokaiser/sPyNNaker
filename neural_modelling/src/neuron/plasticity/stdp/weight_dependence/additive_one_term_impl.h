#ifndef ADDITIVE_ONE_TERM_IMPL_H
#define ADDITIVE_ONE_TERM_IMPL_H

// Standard includes
#include <stdbool.h>
#include <stdint.h>

// Include debug header for log_info etc
#include "../../../../common/common-impl.h"

// Include generic plasticity maths functions
#include "../../common/maths.h"
#include "../../common/runtime_log.h"

//---------------------------------------
// Structures
//---------------------------------------
typedef struct
{
  int32_t min_weight;
  int32_t max_weight;
  
  int32_t a2_plus;
  int32_t minus_a2_minus;
} plasticity_weight_region_data_t;

typedef struct
{
  int32_t initial_weight;
  
  int32_t a2_plus;
  int32_t a2_minus;
  
  const plasticity_weight_region_data_t *weight_region;
} weight_state_t;

//---------------------------------------
// Externals
//---------------------------------------
extern plasticity_weight_region_data_t plasticity_weight_region_data[SYNAPSE_TYPE_COUNT];

#define MAC
//---------------------------------------
// STDP weight dependance functions
//---------------------------------------
static inline weight_state_t weight_init(weight_t weight, index_t synapse_type)
{
  use(weight);

  return (weight_state_t){ 
    .initial_weight = (int32_t)weight, 
    .a2_plus = 0, .a2_minus = 0, 
    .weight_region = &plasticity_weight_region_data[synapse_type] };
}
//---------------------------------------
#ifdef MAC
static inline weight_state_t weight_mac_depression(weight_state_t state, int32_t a, int32_t b)
{
  state.a2_minus = __smlabb(a, b, state.a2_minus);
  return state;
}
//---------------------------------------
static inline weight_state_t weight_mac_potentiation(weight_state_t state, int32_t a, int32_t b)
{
  state.a2_plus = __smlabb(a, b, state.a2_plus);
  return state;
}
//---------------------------------------
#else
static inline weight_state_t weight_apply_depression(weight_state_t state, int32_t a2_minus)
{
  state.a2_minus += a2_minus;
  return state;
}
//---------------------------------------
static inline weight_state_t weight_apply_potentiation(weight_state_t state, int32_t a2_plus)
{
  state.a2_plus += a2_plus;
  return state;
}
#endif  // MAC
//---------------------------------------
static inline weight_t weight_get_final(weight_state_t new_state)
{
  // Scale potentiation and depression
  // **NOTE** A2+ and A2- are pre-scaled into weight format
#ifdef MAC
  int32_t delta_weight = __smulbb(new_state.a2_plus >> STDP_FIXED_POINT, new_state.weight_region->a2_plus);
  delta_weight = __smlabb(new_state.a2_minus >> STDP_FIXED_POINT, new_state.weight_region->minus_a2_minus, delta_weight);
#else
  int32_t delta_weight = __smulbb(new_state.a2_plus, new_state.weight_region->a2_plus);
  delta_weight = __smlabb(new_state.a2_minus, new_state.weight_region->minus_a2_minus, delta_weight);
#endif
  
  // Apply all terms to initial weight
  int32_t new_weight = new_state.initial_weight + (delta_weight >> STDP_FIXED_POINT);

  // Clamp new weight
  new_weight = MIN(new_state.weight_region->max_weight, MAX(new_weight, new_state.weight_region->min_weight));
  
  plastic_runtime_log_info("\told_weight:%u, a2+:%d, a2-:%d, delta_weight:%d, new_weight:%d",
    new_state.initial_weight, new_state.a2_plus, new_state.a2_minus, delta_weight, new_weight); 
  
  return (weight_t)new_weight;
}
#endif  // ADDITIVE_ONE_TERM_IMPL_H