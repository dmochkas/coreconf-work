/* Includes */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <coap3/libcoap.h>
#include <coap3/coap.h>

#include "common/definitions.h"
#include "config/oscore.h"
#include "helpers/resolve.h"

/* Private variables */

static uint8_t received_response = 0;
static uint8_t dummy_buf[BUFFER_MAX];

// OSCORE sequence number file and address
static FILE *oscore_seq_num_fp = NULL;
static const char *oscore_seq_save_file = OSCORE_CLIENT_SEQ_NUM_FILENAME;

// OSCORE configurations
const char oscore_config_str[] = // TODO Get config from text file
  "master_secret,hex,\"0102030405060708090a0b0c0d0e0f10\"\n"
  "master_salt,hex,\"9e7ca92223786340\"\n"
  "sender_id,ascii,\"user1\"\n"
  "recipient_id,ascii,\"server\"\n"
  "replay_window,integer,30\n"
  "aead_alg,integer,10\n"
  "hkdf_alg,integer,-10\n";

/* Message handler prototypes */

static void nack_handler(coap_session_t *session COAP_UNUSED, 
                          const coap_pdu_t *sent, 
                          const coap_nack_reason_t reason, 
                          const coap_mid_t mid COAP_UNUSED);
static coap_response_t response_handler(coap_session_t *session COAP_UNUSED, 
                                        const coap_pdu_t *sent, 
                                        const coap_pdu_t *received, 
                                        const coap_mid_t mid COAP_UNUSED);

/* Private function prototypes */

static int oscore_save_seq_num(uint64_t sender_seq_num, void *param COAP_UNUSED);

/* Main function */
int main() {
  printf(
    "OSCORECONF CLIENT\n"
    "  Version: 0.2\n"
    "  Libraries:\n"
    "  - libcoap/%s\n"
    "  Features:\n"
    "  - Simple GET message with server response\n"
    "  - Protection with OSCORE and AES CCM\n"
    "\n",
    LIBCOAP_PACKAGE_VERSION
  );

  const char *resource_uri_str = "coap://[2001:660:7301:51:8b61:22c0:6d18:c74f]/hello";
  
  coap_startup();
  coap_set_log_level(LOG_DEBUG);

  // Setup client address
  coap_address_t client;
  coap_address_init(&client);
  memset(&client.addr.sin6, 0, sizeof(client.addr.sin6)); // Setting IPv6 socket in client
  client.addr.sa.sa_family       = AF_INET6;
  client.addr.sin6.sin6_family   = AF_INET6;
  client.addr.sin6.sin6_port     = htons(COAP_PORT);
  client.addr.sin6.sin6_addr     = in6addr_any;
  client.addr.sin6.sin6_flowinfo = 0;
  client.addr.sin6.sin6_scope_id = 0;

  // Setup server address
  coap_address_t server;
  coap_address_init(&server);
  coap_str_const_t *server_address = coap_make_str_const(COAP_SERVER_IP);
  uint32_t scheme_hint_bits = coap_get_available_scheme_hint_bits(0, 0, COAP_PROTO_NONE);

  if (resolve_address(server_address, COAP_PORT, &server, scheme_hint_bits) > 0) {
    coap_log_err("** Failed to resolve server address.\n");
    exit(2);
  }
  server.addr.sin6.sin6_port = htons(COAP_PORT);

  coap_session_t *session = setup_client_session(&client, &server, COAP_PORT, oscore_config_str);
  coap_context_t *ctx = coap_session_get_context(session);

  // Register handlers
  coap_register_nack_handler(ctx, nack_handler);
  coap_register_response_handler(ctx, response_handler);

  // Create message (PDU)
  coap_pdu_t *request = coap_pdu_init(COAP_MESSAGE_CON, COAP_REQUEST_CODE_GET, coap_new_message_id(session), coap_session_max_pdu_size(session));
  if (!request) {
    coap_log_err("** Failed to create CoAP request.\n");
    exit(5);
  }

  // Create options list and add to message
  coap_optlist_t *optlist = NULL;
  coap_uri_t resource_uri;
  if (coap_split_uri((const unsigned char *)resource_uri_str, strlen(resource_uri_str), &resource_uri) != 0) {
    coap_log_err("** Failed to parse URI.");
    exit(5);
  }
  if (coap_uri_into_options(&resource_uri, &server, &optlist, 1, dummy_buf, sizeof(dummy_buf))) {
    coap_log_err("** Failed to create options.");
    exit(6);
  }
  if (coap_add_optlist_pdu(request, &optlist) != 1) {
    coap_log_err("** Failed to add options to request.");
    exit(7);
  }

  coap_show_pdu(COAP_LOG_WARN, request);

  // Finally send message
  coap_log_info("Sending message...\n");
  if (coap_send(session, request) == COAP_INVALID_MID) {
    coap_log_err("** Failed to send CoAP request.\n");
    exit(8);
  }

  // Send message and wait for response
  coap_pdu_t *response = NULL;
  unsigned wait_ms = (coap_session_get_default_leisure(session).integer_part + 1) * 1000;

  int res;
  while (!received_response) {
    res = coap_io_process(ctx, 1000);
    if (res >= 0 && wait_ms > 0) {
      if (res >= wait_ms) {
        coap_log_err("** Response timeout.\n");
        break;
      } else {
        wait_ms -= res;
      }
    }
  }

  // Cleanup
  coap_delete_optlist(optlist);
  coap_session_release(session);
  coap_free_context(ctx);
  coap_cleanup();

  return 0;
}


/* Function declarations */

static void nack_handler(coap_session_t *session COAP_UNUSED, const coap_pdu_t *sent, const coap_nack_reason_t reason, const coap_mid_t mid COAP_UNUSED) {
  // TODO Implement
  printf("NACK event. Reason: %d", reason);
}

/**
 * @brief Response handler for `coap_send()` responses.
 */
static coap_response_t response_handler(coap_session_t *session COAP_UNUSED, const coap_pdu_t *sent, const coap_pdu_t *received, const coap_mid_t mid COAP_UNUSED) {
  
  coap_opt_t *block_opt;
  coap_opt_iterator_t opt_iter;
  
  size_t buf_len;
  const uint8_t *buf_data;
  size_t buf_offset;
  size_t buf_total;

  coap_pdu_code_t rcv_code = coap_pdu_get_code(received);
  coap_pdu_type_t rcv_type = coap_pdu_get_type(received);
  coap_bin_const_t token = coap_pdu_get_token(received);

  coap_log_info("** Incoming response %d.%02d: ",
                  COAP_RESPONSE_CLASS(rcv_code), rcv_code & 0x1F);

  coap_show_pdu(COAP_LOG_INFO, received);

  received_response = 1;
  return COAP_RESPONSE_OK;
}

/**
 * @brief 
 * 
 * @param sender_seq_num 
 * @param COAP_UNUSED 
 * @return int 
 */
static int oscore_save_seq_num(uint64_t sender_seq_num, void *param COAP_UNUSED) {
  coap_log_info("** Saving sequence number: %lu\n", sender_seq_num);

  if (oscore_seq_num_fp) {
    rewind(oscore_seq_num_fp);
    fprintf(oscore_seq_num_fp, "%lu\n", sender_seq_num);
    fflush(oscore_seq_num_fp);
  }
  return 1;
}