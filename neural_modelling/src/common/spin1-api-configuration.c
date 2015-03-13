/*
 * spin1-api-configuration.c
 *
 *
 *  SUMMARY
 *    Spin1-API dependent configuration routines
 *
 *  AUTHOR
 *    James Knight (knightk@man.ac.uk)
 *
 *  COPYRIGHT
 *    Copyright (c) James Knight and The University of Manchester, 2014.
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
 *    17 January, 2014
 *
 *  HISTORY
 * *  DETAILS
 *    Created on       : 17 January 2014
 *    Version          : $Revision$
 *    Last modified on : $Date$
 *    Last modified by : $Author$
 *    $Id$
 *
 *    $Log$
 *
 */

#include "common-impl.h"

// Globals
uint simulation_rtr_entry = 0;

address_t system_load_sram()
{
  uint core_id = spin1_get_core_id();

  // Get the address this core's DTCM data starts at from the user data member of the structure associated with this virtual processor
  address_t address = (address_t)sv_vcpu[core_id].user0;

  if(address != NULL)
  {
    log_info("Based on SRAM user field, SDRAM data for core %u begins at %08x", core_id, address);
  }
  else
  {
    uint app_id = sark_app_id();
    
    address = (address_t*)sv->alloc_tag[(app_id << 8) + core_id];
    log_info("Based on allocated tag, SDRAM for app_id %u running on core %u begins at %08x", app_id, core_id, address);
  }
  

  return address;
}

bool system_runs_to_completion()
{
  spin1_start(SYNC_WAIT);
  if (leadAp) {
//#ifndef DEBUG
      rtr_free_id(sark_app_id(), 1);
//#endif // n DEBUG
  }
  return (true);
}

bool system_data_extracted    () {                return (true); }
