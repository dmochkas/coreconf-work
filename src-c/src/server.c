/* Includes */
#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <signal.h>
#include <coap3/libcoap.h>
#include <coap3/coap.h>

#include "definitions.h"
#include "helpers/resolve.h"

/* Private variables */

static uint8_t running = 1;

// OSCORE sequence number file and address
static FILE *oscore_seq_num_fp = NULL;
static const char *oscore_seq_save_file = OSCORE_SERVER_SEQ_NUM_FILENAME;

// OSCORE configurations
static uint8_t oscore_config_str[] = // TODO Get config from text file
  "master_secret,hex,\"0102030405060708090a0b0c0d0e0f10\"\n"
  "master_salt,hex,\"9e7ca92223786340\"\n"
  "sender_id,hex,\"01\"\n"
  "recipient_id,hex,\"02\"\n"
  "replay_window,integer,30\n"
  "aead_alg,integer,10\n"
  "hkdf_alg,integer,-10\n";

/* Private functions */

static void handle_sigint(int signum COAP_UNUSED) {
  running = 0;
}

/* Resource handler prototypes */

static void datastore_pull_handler(coap_resource_t *resource,
                                    coap_session_t *session, 
                                    const coap_pdu_t *request, 
                                    const coap_string_t *query COAP_UNUSED,
                                    coap_pdu_t *response);

/* Private function prototypes */

static int oscore_save_seq_num(uint64_t sender_seq_num, void *param COAP_UNUSED);

/* Main function */
int main() {
  coap_str_const_t *server_address = coap_make_str_const(COAP_SERVER_IP);
  uint8_t found_endpoint = 0;

  printf(
    "OSCORECONF SERVER\n"
    "  Version: 0.1\n"
    "  Libraries:\n"
    "  - libcoap/%s\n"
    "\n",
    LIBCOAP_PACKAGE_VERSION
  );

  signal(SIGINT, handle_sigint);
  
  coap_startup();
  coap_set_log_level(COAP_LOG_OSCORE);

  // Create CoAP context
  coap_context_t *ctx = coap_new_context(NULL);
  if (!ctx) {
    perror("Failed to get CoAP context.\n");
    exit(1);
  }

  // Let libcoap handle multi-block payload
  coap_context_set_block_mode(ctx, COAP_BLOCK_USE_LIBCOAP | COAP_BLOCK_SINGLE_BODY);
  uint32_t scheme_hint_bits = coap_get_available_scheme_hint_bits(0, 0, COAP_PROTO_NONE);
  coap_log_info("Resolving address...\n");
  coap_addr_info_t *info_list = coap_resolve_address_info(server_address, 0, 0, 0, 0, AF_INET6, scheme_hint_bits, COAP_RESOLVE_TYPE_LOCAL);

  // Start OSCORE server
  coap_log_info("Building OSCORE context...");
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

    coap_context_oscore_server(ctx, oscore_config);
  } else {
    coap_log_warn("** OSCORE is NOT supported! Aborting...\n");
    exit(4);
  }

  // Create listening endpoint(s)
  coap_log_info("Getting endpoints...\n");
  for (coap_addr_info_t *info = info_list; info != NULL; info = info->next) {
    coap_endpoint_t *endpoint = coap_new_endpoint(ctx, &info->addr, info->proto);
    if (!endpoint) {
      coap_log_warn("** Cannot create endpoint for CoAP protocol %u\n", info->proto);
    } else {
      found_endpoint = 1;
      coap_log_info("** Created endpoint: %s\n", coap_endpoint_str(endpoint));
    }
  }
  coap_free_address_info(info_list);
  if (!found_endpoint) {
    coap_log_err("No context available for interface '%s'\n", (const char *)server_address->s);
    exit(2);
  }

  // Create resource
  const char *datastore_resource_uri = "hello";
  coap_resource_t *datastore_resource = coap_resource_init(coap_make_str_const(datastore_resource_uri), 0);
  coap_register_handler(datastore_resource, COAP_REQUEST_GET, datastore_pull_handler);
  coap_register_handler(datastore_resource, COAP_REQUEST_FETCH, datastore_pull_handler);
  coap_add_resource(ctx, datastore_resource);

  // Handle any libcoap I/O requirements
  coap_log_info("Starting server...\n");
  running = 1;
  while (running) {
    coap_io_process(ctx, COAP_IO_WAIT);
  }
  printf("\n");
  coap_log_info("Closing server...\n");

  // Cleanup
  coap_delete_resource(ctx, datastore_resource);
  coap_free_context(ctx);
  coap_cleanup();

  return 0;
}

/* Function declarations */

/**
 * @brief 
 * 
 * @param resource 
 * @param session 
 * @param request 
 * @param COAP_UNUSED 
 * @param response 
 */
static void datastore_pull_handler(coap_resource_t *resource, coap_session_t *session, const coap_pdu_t *request, const coap_string_t *query COAP_UNUSED, coap_pdu_t *response) {

  coap_opt_t *block_opt;
  coap_opt_iterator_t opt_iter;
  
  size_t buf_len;
  const uint8_t *buf_data;
  size_t buf_offset;
  size_t buf_total;

  coap_pdu_code_t rcv_code = coap_pdu_get_code(request);
  coap_pdu_type_t rcv_type = coap_pdu_get_type(request);
  coap_bin_const_t token = coap_pdu_get_token(request);

  coap_log_info("** process incoming request %d.%02d request:\n",
                  COAP_RESPONSE_CLASS(rcv_code), rcv_code & 0x1F);
  coap_show_pdu(COAP_LOG_INFO, request);

  coap_pdu_set_code(response, COAP_RESPONSE_CODE_VALID);
  coap_add_data(response, 5, (const uint8_t *)"world");
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