#include "common-impl.h"
#include "buffered_eieio_defs.h"

// Standard includes
#include <string.h>

#define BUFFER_OPERATION_READ 0
#define BUFFER_OPERATION_WRITE 1

typedef uint16_t* eieio_msg_t;

//---------------------------------------
// Structures
//---------------------------------------
typedef struct recording_channel_t
{
  address_t counter;
  uint8_t *start;
  uint8_t *current_write;
  uint8_t *current_read;
  uint8_t *end;
  uint8_t region_id;
  bool last_buffer_operation;
} recording_channel_t;

typedef struct
{
  uint16_t eieio_header_command;
  uint16_t chip_id;
  uint8_t processor;
  uint8_t pad1;
  uint8_t channel_and_region;
  uint8_t sequence;
  uint32_t start_address;
  uint32_t space_to_be_read;
} read_req_packet_sdp_t;

//---------------------------------------
// Globals
//---------------------------------------
static recording_channel_t g_recording_channels[e_recording_channel_max];
static uint32_t pkt_fsm = 0xFF;
static sdp_msg_t read_request;
static read_req_packet_sdp_t *req_ptr;
//---------------------------------------
// Private API
//---------------------------------------
static inline bool recording_channel_in_use(recording_channel_e channel)
{
  return (g_recording_channels[channel].start != NULL &&  g_recording_channels[channel].end != NULL);
}

//---------------------------------------
// Public API
//---------------------------------------
bool recording_data_filled(address_t address, uint8_t region_id, uint32_t flags, recording_channel_e channel, uint32_t size_bytes)
{
  use(flags);
  if (size_bytes == 0)
  {

    // Channel is not enabled really
    return true;
  }

  if(recording_channel_in_use(channel))
  {
    log_info("Recording channel %u already configured", channel);

    // CHANNEL already initialized
    return false;
  }
  else
  {
    recording_channel_t *recording_channel = &g_recording_channels[channel];
    address_t output_region = region_start(region_id, address);

    // Cache pointer to output counter in recording channel and set it to 0
    recording_channel->counter = &output_region[0];
    *recording_channel->counter = 0;

    // Calculate pointers to the start, current_write position and end of this memory block
    recording_channel->start = recording_channel->current_write = recording_channel->current_read = (uint8_t*)&output_region[1];
    recording_channel->last_buffer_operation = BUFFER_OPERATION_READ;
    recording_channel->end = recording_channel->start + size_bytes;
    recording_channel->region_id = region_id;
    
    log_info("Recording channel %u configured to use %u byte memory block starting at %08x", channel, size_bytes, recording_channel->start);
    
    address_t config_region = region_start(0, address);
    uint8_t return_tag_id = config_region[7];
    
    read_request.length = 8 + sizeof(read_req_packet_sdp_t);
    read_request.flags = 0x7;
    read_request.tag = return_tag_id;
    read_request.dest_port = 0xFF;
    read_request.srce_port = (1 << 5) | spin1_get_core_id();
    read_request.dest_addr = 0;
    read_request.srce_addr = spin1_get_chip_id();
    req_ptr = (read_req_packet_sdp_t*) &(read_request.cmd_rc);
    req_ptr -> eieio_header_command = 1 << 14 | SPINNAKER_REQUEST_BUFFERS;
    req_ptr -> chip_id = spin1_get_chip_id();
    req_ptr -> processor = (spin1_get_core_id() << 3);
    req_ptr -> pad1 = 0;
    //req_ptr -> region = region_id & 0x0F;
    
    return true;
  }
}
//---------------------------------------
bool recording_record(recording_channel_e channel, void *data, uint32_t size_bytes)
{
  if(recording_channel_in_use(channel))
  {
    recording_channel_t *recording_channel = &g_recording_channels[channel];

    // If there's space to record
    if(recording_channel->current_write < (recording_channel->end - size_bytes))
    {
      // Copy data into recording channel
      memcpy(recording_channel->current_write, data, size_bytes);
      
      // Update current_write pointer
      recording_channel->current_write += size_bytes;
      return true;
    }
    else
    {
      log_info("ERROR: recording channel %u out of space", channel);
      return false;
    }
  }
  else
  {
    log_info("ERROR: recording channel %u not in use", channel);

    return false;
  }


}
//---------------------------------------
void recording_finalise()
{
  log_info("Finalising recording channels");

  // Loop through channels
  for(uint32_t channel = 0; channel < e_recording_channel_max; channel++)
  {
    // If this channel's in use
    if(recording_channel_in_use(channel))
    {
      recording_channel_t *recording_channel = &g_recording_channels[channel];

      // Calculate the number of bytes that have been written and write back to SDRAM counter
      uint32_t num_bytes_written = recording_channel->current_write - recording_channel->start;
      log_info("\tFinalising channel %u - %x bytes of data starting at %08x", channel, num_bytes_written + sizeof(uint32_t), recording_channel->counter);
      *recording_channel->counter = num_bytes_written;
    }
  }
}

//---------------------------------------
void send_read_request()
{
  for(uint32_t channel = 0; channel < e_recording_channel_max; channel++)
  {
    if(recording_channel_in_use(channel))
    {
      
    }
  }
}

void packet_handler(eieio_msg_t eieio_msg_ptr, uint32_t length)
{
  uint16_t eieio_cmd_hdr = eieio_msg_ptr[0];
  
  if (eieio_cmd_hdr == 0x4009) //host data read eieio command packet
  {
    uint32_t *ptr_2 = &eieio_msg_ptr[2];
    uint32_t space_read = ptr_2[0];
    uint8_t *ptr_1 = &eieio_msg_ptr[1];
    uint8_t channel = (ptr_1[0] >> 4) & 0x0F;
    uint8_t region_id = ptr_1[0] & 0x0F;
    uint8_t sequence_no = ptr_1[1];
    uint8_t next_fsm_state = ((pkt_fsm + 1) & 0xFF);
    
    if (sequence_no == next_fsm_state)
    {
      pkt_fsm = next_fsm_state;
      
      g_recording_channels[channel].current_read += space_read;
      if (g_recording_channels[channel].current_read >= g_recording_channels[channel].end)
	g_recording_channels[channel].current_read = g_recording_channels[channel].start;
      g_recording_channels[channel].last_buffer_operation = BUFFER_OPERATION_READ;
    }
    else
    {
      send_read_request();
    }
  }
}

void sdp_packet_callback(uint mailbox, uint port)
{
  use(port);
  sdp_msg_t *msg = (sdp_msg_t *) mailbox;
  uint16_t length = msg -> length;
  eieio_msg_t eieio_msg_ptr = (eieio_msg_t) &(msg -> cmd_rc);

  packet_handler(eieio_msg_ptr, length - 8);

  //free the message to stop overload
  spin1_msg_free(msg);
}