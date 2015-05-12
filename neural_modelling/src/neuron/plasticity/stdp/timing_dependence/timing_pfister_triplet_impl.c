#include "timing_pfister_triplet_impl.h"
#include "../../../../common/constants.h"

//---------------------------------------
// Globals
//---------------------------------------
// Exponential lookup-tables
int16_t tau_plus_lookup[TAU_PLUS_SIZE];
int16_t tau_minus_lookup[TAU_MINUS_SIZE];
int16_t tau_x_lookup[TAU_X_SIZE];
int16_t tau_y_lookup[TAU_Y_SIZE];

//---------------------------------------
// Functions
//---------------------------------------
address_t timing_initialise(
        address_t address, uint32_t time_dependency_magic_number) {

    log_info("timing_initialise: starting");
    log_info("\tSTDP triplet rule");
    // **TODO** assert number of neurons is less than max

    if (time_dependency_magic_number !=
        TIME_DEPENDENCY_PFISTER_SPIKE_TRIPLET_MAGIC_NUMBER){
        log_error("expected magic number 0x%x, got magic number 0x%x instead.",
                  TIME_DEPENDENCY_PFISTER_SPIKE_TRIPLET_MAGIC_NUMBER,
                  time_dependency_magic_number);
        return NULL;
    }

    // Copy LUTs from following memory
    address_t lut_address = maths_copy_int16_lut(&address[0], TAU_PLUS_SIZE,
                                                 &tau_plus_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_MINUS_SIZE,
                                       &tau_minus_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_X_SIZE,
                                       &tau_x_lookup[0]);
    lut_address = maths_copy_int16_lut(lut_address, TAU_Y_SIZE,
                                       &tau_y_lookup[0]);

    log_info("timing_initialise: completed successfully");

    return lut_address;
}
