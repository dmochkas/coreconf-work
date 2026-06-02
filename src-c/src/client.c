/* Includes */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

#include <coap3/libcoap.h>
#include <coap3/coap.h>

#include "definitions.h"
#include "helpers/resolve.h"

/* Private variables */

static uint8_t received_response = 0;

// OSCORE sequence number file and address
static FILE *oscore_seq_num_fp = NULL;
static const char *oscore_seq_save_file = OSCORE_CLIENT_SEQ_NUM_FILENAME;

// OSCORE configurations
static uint8_t oscore_config_str[] = // TODO Get config from text file
  "master_secret,hex,\"0102030405060708090a0b0c0d0e0f10\"\n"
  "master_salt,hex,\"9e7ca92223786340\"\n"
  "sender_id,hex,\"02\"\n"
  "recipient_id,hex,\"01\"\n"
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
    "  Version: 0.1\n"
    "  Libraries:\n"
    "  - libcoap/%s\n"
    "\n",
    LIBCOAP_PACKAGE_VERSION
  );

  const char *resource_uri_str = "coap://[2001:660:7301:51:8b61:22c0:6d18:c74f]/hello";
  uint8_t dummy_buf[100];
  
  coap_startup();
  coap_set_log_level(COAP_LOG_OSCORE);

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

  // Create CoAP context
  coap_context_t *ctx = coap_new_context(NULL);
  if (!ctx) {
    coap_log_err("** Failed to get CoAP context.\n");
    exit(3);
  }
  coap_context_set_keepalive(ctx, 10);

  // Create CoAP session (with OSCORE)
  coap_session_t *session = NULL;
  if (coap_oscore_is_supported()) {
    coap_log_warn("** OSCORE is supported!\n");

    coap_str_const_t *config_str = coap_make_str_const(oscore_config_str);
    uint64_t start_seq_num = 0;
    coap_oscore_conf_t *oscore_config;

    if (oscore_seq_save_file) {
      // Try to open file
      oscore_seq_num_fp = fopen(oscore_seq_save_file, "r+");

      if (oscore_seq_num_fp == NULL) { // If it doesn't exist, try to create it
        oscore_seq_num_fp = fopen(oscore_seq_save_file, "w+");

        if (oscore_seq_num_fp == NULL) { // If failed to create, abort.
          coap_log_err("** OSCORE save restart info file error: %s\nAborting!\n", oscore_seq_save_file);
          exit(4);
        }

        fscanf(oscore_seq_num_fp, "%ju", &start_seq_num);
      }
      oscore_config = coap_new_oscore_conf(*config_str, oscore_save_seq_num, NULL, start_seq_num);

      if (!oscore_config) {
        coap_free_context(ctx);

        coap_log_err("** Failed to create OSCORE config.\n");

        exit(5);
      }
    }
    
    session = coap_new_client_session_oscore(ctx, &client, &server, COAP_PROTO_UDP, oscore_config);
  } else {
    coap_log_warn("** OSCORE is NOT supported! Aborting...\n");
    exit(4);
  }
  
  if (!session) {
    coap_log_err("** Failed to create CoAP session object.\n");
    coap_free_context(ctx);
    exit(4);
  }

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
  // if (coap_send(session, request) == COAP_INVALID_MID) {
  //   coap_log_err("** Failed to send CoAP request.\n");
  //   exit(8);
  // }

  // Send message and wait for response
  coap_pdu_t *response = NULL;
  unsigned wait_ms = (coap_session_get_default_leisure(session).integer_part + 1) * 1000;

  coap_log_info("Sending message...\n");
  int result = coap_send_recv(session, request, &response, wait_ms);
  
  if (result >= 0) {
    coap_log_info("Response received!\n");
    response_handler(session, request, response, coap_pdu_get_mid(request));

    if (result < (int)wait_ms) {
      wait_ms -= result;
    } else {
      wait_ms = 0;
    }
  } else {
    switch (result) {
    case -1:
      coap_log_err("coap_send_recv: Invalid timeout value %u\n", wait_ms);
      break;
    case -2:
      coap_log_err("coap_send_recv: Failed to transmit PDU\n");
      break;
    case -3:
      coap_log_err("coap_send_recv: Critical Nack / Event occurred\n");
      break;
    case -4:
      coap_log_err("coap_send_recv: Internal coap_io_process() failed\n");
      break;
    case -5:
      coap_log_err("coap_send_recv: No response received within the timeout\n");
      break;
    case -6:
      coap_log_err("coap_send_recv: Terminated by user\n");
      break;
    case -7:
      coap_log_err("coap_send_recv: Client Mode code not enabled\n");
      break;
    default:
      coap_log_err("coap_send_recv: Invalid return value %d\n", result);
      break;
    }
  }

  // int res;
  // while (!received_response) {
  //   res = coap_io_process(ctx, 1000);
  //   if (res >= 0 && wait_ms > 0) {
  //     if (res >= wait_ms) {
  //       coap_log_err("** Response timeout.\n");
  //       break;
  //     } else {
  //       wait_ms -= res;
  //     }
  //   }
  // }

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
  if (oscore_seq_num_fp) {
    rewind(oscore_seq_num_fp);
    fprintf(oscore_seq_num_fp, "%lu\n", sender_seq_num);
    fflush(oscore_seq_num_fp);
  }
  return 1;
}