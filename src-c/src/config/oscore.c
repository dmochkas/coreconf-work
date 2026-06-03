#include "oscore.h"

static FILE *oscore_seq_num_fp = NULL;

static int oscore_save_seq_num(uint64_t sender_seq_num, void *param COAP_UNUSED) {
  coap_log_debug("*** Saving OSCORE sequente number (%lu)", sender_seq_num);

  if (oscore_seq_num_fp) {
    rewind(oscore_seq_num_fp);
    fprintf(oscore_seq_num_fp, "%lu\n", sender_seq_num);
    fflush(oscore_seq_num_fp);
  }
  return 1;
}

/**
 * @brief Set the up client session object
 * 
 * @param client CoAP client address or NULL
 * @param server CoAP server address
 * @param port Server access port (CoAP default is 5683)
 * @param oscore_conf_str OSCORE configuration string (master key, master salt, etc)
 * @return coap_session_t* 
 */
coap_session_t *setup_client_session(coap_address_t *client, coap_address_t *server, const uint16_t port, const uint8_t *oscore_conf_str) {
  
#ifndef OSCORE_CLIENT_SEQ_NUM_FILENAME
  #error "OSCORE_CLIENT_SEQ_NUM_FILENAME is undefined!"
#endif
  
  coap_session_t *session = NULL;

  // Create context
  coap_context_t *ctx = coap_new_context(NULL);

  // Check for context
  if (!ctx) {
    coap_log_err("%s: line %d: Failed to create context.", __FILE__, __LINE__);
    return NULL;
  }
  coap_log_debug("%s: Context created.", __FILE__);
  coap_context_set_block_mode(ctx, COAP_BLOCK_USE_LIBCOAP); // Required for OSCORE Echo challenge!
  coap_context_set_keepalive(ctx, 10);

  // Check for OSCORE
  if (coap_oscore_is_supported()) {
    coap_log_debug("%s: OSCORE is supported!", __FILE__);

    // Get OSCORE config string as coap_str_const_t
    coap_str_const_t config = { sizeof(oscore_conf_str), oscore_conf_str };
    uint64_t start_seq_num = 0;
    coap_oscore_conf_t *oscore_config;

    // Try to open file
    oscore_seq_num_fp = fopen(OSCORE_CLIENT_SEQ_NUM_FILENAME, "r+");

    if (oscore_seq_num_fp == NULL) { // If it doesn't exist, try to create it
      oscore_seq_num_fp = fopen(OSCORE_CLIENT_SEQ_NUM_FILENAME, "w+");

      if (oscore_seq_num_fp == NULL) { // If failed to create, abort.
        coap_log_err("%s: line %d: OSCORE save restart info file error: %s\n", __FILE__, __LINE__, OSCORE_CLIENT_SEQ_NUM_FILENAME);
        goto ctx_cleanup;
      }

      // Read first number
      fscanf(oscore_seq_num_fp, "%ju", &start_seq_num);
    }
    oscore_config = coap_new_oscore_conf(config, oscore_save_seq_num, NULL, start_seq_num);

    if (!oscore_config) {
      coap_log_err("%s: line %d: Failed to create OSCORE config.\n", __FILE__, __LINE__);
      goto ctx_cleanup;
    }

    // Finally create client OSCORE session
    session = coap_new_client_session_oscore3(
      ctx, client, server, COAP_PROTO_UDP, oscore_config, NULL, NULL, NULL
    );

  } else {
    // If no OSCORE, free context and return NULL.
    coap_log_err("%s: line %d: OSCORE is not supported!\n", __FILE__, __LINE__);
    goto ctx_cleanup;
  }

  // If no session was created, free context and return NULL.
  if (!session) {
    coap_log_err("%s: line %d: Failed to create session.\n", __FILE__, __LINE__);
    goto ctx_cleanup;
  }

  return session;

ctx_cleanup:
  coap_free_context(ctx);
  return NULL;
}