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
  "sender_id,hex,\"01\"\n"
  "recipient_id,hex,\"00\"\n"
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
static int send_request(coap_session_t *session, coap_context_t *ctx, coap_pdu_t *pdu, coap_pdu_t **response);

/* Main function */
int main() {
  uint8_t data[BUFFER_MAX] = { 0 };
  
  const uint8_t *payload;
  long unsigned int payload_len = 0;

  printf(
    "OSCORECONF CLIENT\n"
    "  Libraries:\n"
    "  - libcoap/%s\n"
    "  Features:\n"
    "  - Simple GET message with server response\n"
    "  - Protection with OSCORE and AES CCM\n"
    "\n",
    LIBCOAP_PACKAGE_VERSION
  );

  const char *resource_uri_str = "coap://[" COAP_SERVER_IP "]/c";
  
  coap_startup();
  coap_set_log_level(COAP_LOG_INFO);

  // Setup client address
  coap_address_t client;
  coap_address_init(&client);
  memset(&client.addr.sin6, 0, sizeof(client.addr.sin6)); // Setting IPv6 socket in client
  client.addr.sa.sa_family       = AF_INET6;
  client.addr.sin6.sin6_family   = AF_INET6;
  client.addr.sin6.sin6_addr     = in6addr_loopback;
  client.addr.sin6.sin6_flowinfo = 0;
  client.addr.sin6.sin6_scope_id = 0;

  // Setup server address
  coap_address_t server;
  coap_address_init(&server);
  coap_str_const_t *server_address = coap_make_str_const(COAP_SERVER_IP);
  uint32_t scheme_hint_bits = coap_get_available_scheme_hint_bits(0, 0, COAP_PROTO_NONE);

  if (resolve_address(server_address, COAP_PORT, &server, scheme_hint_bits) > 0) {
    coap_log_err(__FILE__ ": line %d: Failed to resolve server address.\n", __LINE__);
    exit(1);
  }
  server.addr.sin6.sin6_port = htons(COAP_PORT);

  coap_session_t *session = setup_oscore_client_session(&client, &server, COAP_PORT, oscore_config_str);
  coap_context_t *ctx = coap_session_get_context(session);

  // Register handlers
  coap_register_nack_handler(ctx, nack_handler);
  coap_register_response_handler(ctx, response_handler);

  // Create message (PDU)
  coap_optlist_t *optlist = NULL;
  coap_uri_t resource_uri;
  coap_pdu_t *response = NULL;

  coap_pdu_t *request = NULL;
  
  // Temperature request
  request = coap_pdu_init(COAP_MESSAGE_CON, COAP_REQUEST_CODE_GET, coap_new_message_id(session), coap_session_max_pdu_size(session));
  if (!request) {
    coap_log_err(__FILE__ ": line %d: Failed to create CoAP request.\n", __LINE__);
    exit(1);
  }

  // Create options list and add to message
  if (coap_split_uri((const unsigned char *)resource_uri_str, strlen(resource_uri_str), &resource_uri)) {
    coap_log_err(__FILE__ ": line %d: Failed to parse URI.\n", __LINE__);
    exit(1);
  }
  if (coap_uri_into_options(&resource_uri, &server, &optlist, 1, dummy_buf, sizeof(dummy_buf)) < 0) {
    coap_log_err(__FILE__ ": line %d: Failed to create options.\n", __LINE__);
    exit(1);
  }
  if (coap_add_optlist_pdu(request, &optlist) != 1) {
    coap_log_err(__FILE__ ": line %d: Failed to add options to request.\n", __LINE__);
    exit(1);
  }

  memset(data, 0, sizeof(data));
  if (coap_add_option(request, COAP_OPTION_ACCEPT, 1, data) == 0) {
    coap_log_err(__FILE__ ": line %d: Failed to add Accept option to request.\n", __LINE__);
    exit(1);
  }
  
  if (coap_add_data(request, strlen("temp"), "temp") != 1) {
    coap_log_err(__FILE__ ": line %d: Failed to add data to request.\n", __LINE__);
    exit(1);
  }

  coap_show_pdu(COAP_LOG_INFO, request);
  send_request(session, ctx, request, &response);
  coap_show_pdu(COAP_LOG_INFO, response);

  coap_get_data(response, &payload_len, &payload);
  memset(data, 0, sizeof(data));
  memcpy(data, payload, payload_len);
  coap_log_info("Temperature: %s\n", data);

  printf("\n");
  
  // Battery level request
  request = coap_pdu_init(COAP_MESSAGE_CON, COAP_REQUEST_CODE_GET, coap_new_message_id(session), coap_session_max_pdu_size(session));
  if (!request) {
    coap_log_err(__FILE__ ": line %d: Failed to create CoAP request.\n", __LINE__);
    exit(1);
  }

  // Create options list and add to message
  if (coap_add_optlist_pdu(request, &optlist) != 1) {
    coap_log_err(__FILE__ ": line %d: Failed to add options to request.\n", __LINE__);
    exit(1);
  }

  memset(data, 0, sizeof(data));
  if (coap_add_option(request, COAP_OPTION_ACCEPT, 1, data) == 0) {
    coap_log_err(__FILE__ ": line %d: Failed to add Accept option to request.\n", __LINE__);
    exit(1);
  }
  
  if (coap_add_data(request, strlen("bat"), "bat") != 1) {
    coap_log_err(__FILE__ ": line %d: Failed to add data to request.\n", __LINE__);
  }

  // Send message
  coap_show_pdu(COAP_LOG_INFO, request);
  send_request(session, ctx, request, &response);
  coap_show_pdu(COAP_LOG_INFO, response);

  coap_get_data(response, &payload_len, &payload);
  coap_log_info("Battery level: %d\n", payload[0]);

  printf("\n");

  // Position request
  request = coap_pdu_init(COAP_MESSAGE_CON, COAP_REQUEST_CODE_GET, coap_new_message_id(session), coap_session_max_pdu_size(session));
  if (!request) {
    coap_log_err(__FILE__ ": line %d: Failed to create CoAP request.\n", __LINE__);
    exit(1);
  }

  // Create options list and add to message
  if (coap_add_optlist_pdu(request, &optlist) != 1) {
    coap_log_err(__FILE__ ": line %d: Failed to add options to request.\n", __LINE__);
    exit(1);
  }

  memset(data, 0, sizeof(data));
  if (coap_add_option(request, COAP_OPTION_ACCEPT, 1, data) == 0) {
    coap_log_err(__FILE__ ": line %d: Failed to add Accept option to request.\n", __LINE__);
    exit(1);
  }
  
  if (coap_add_data(request, strlen("pos"), "pos") != 1) {
    coap_log_err(__FILE__ ": line %d: Failed to add data to request.\n", __LINE__);
  }

  coap_show_pdu(COAP_LOG_INFO, request);
  send_request(session, ctx, request, &response);
  coap_show_pdu(COAP_LOG_INFO, response);

  coap_get_data(response, &payload_len, &payload);
  coap_log_info("Position:  X=%d Y=%d\n", payload[0], payload[1]);

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
  coap_log_err("NACK event. Reason: %d", reason);
}

/**
 * @brief Response handler for `coap_send()` responses.
 */
static coap_response_t response_handler(coap_session_t *session COAP_UNUSED, const coap_pdu_t *sent, const coap_pdu_t *received, const coap_mid_t mid COAP_UNUSED) {
  
  // coap_opt_t *block_opt;
  // coap_opt_iterator_t opt_iter;
  
  // size_t buf_len;
  // const uint8_t *buf_data;
  // size_t buf_offset;
  // size_t buf_total;

  coap_pdu_code_t rcv_code = coap_pdu_get_code(received);
  coap_pdu_type_t rcv_type = coap_pdu_get_type(received);
  coap_bin_const_t token = coap_pdu_get_token(received);

  coap_log_info("** Incoming response %d.%02d: ",
                  COAP_RESPONSE_CLASS(rcv_code), rcv_code & 0x1F);
  coap_show_pdu(COAP_LOG_INFO, received);

  // received_response = 1;
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

/**
 * @brief Sends a request PDU using session and context.
 * 
 * @param session CoAP client session 
 * @param ctx CoAP context
 * @param pdu Request to send
 * @return 1 if success, 0 otherwise
 */
static int send_request(coap_session_t *session, coap_context_t *ctx, coap_pdu_t *pdu, coap_pdu_t **response) {

  // Send message and wait for response
  coap_log_info("Sending message...\n");
  unsigned wait_ms = (coap_session_get_default_leisure(session).integer_part + 1) * 1000;
  int result = coap_send_recv(session, pdu, response, wait_ms);
  switch (result) {
    case -1:
      coap_log_err(__FILE__ ": line %d: coap_send_recv: Invalid timeout value %u\n", __LINE__, wait_ms);
      break;
    case -2:
      coap_log_err(__FILE__ ": line %d: coap_send_recv: Failed to transmit PDU\n", __LINE__);
      break;
    case -3:
      /* Nack / Event handler already reported issue */
      break;
    case -4:
      coap_log_err(__FILE__ ": line %d: coap_send_recv: Internal coap_io_process() failed\n", __LINE__);
      break;
    case -5:
      coap_log_err(__FILE__ ": line %d: coap_send_recv: No response received within the timeout\n", __LINE__);
      break;
    case -6:
      coap_log_err(__FILE__ ": line %d: coap_send_recv: Terminated by user\n", __LINE__);
      break;
    case -7:
      coap_log_err(__FILE__ ": line %d: coap_send_recv: Client Mode code not enabled\n", __LINE__);
      break;
    default:
      coap_log_debug(__FILE__ ": line %d: coap_send_recv: Return value %d\n", __LINE__, result);
  }

  return result;
}