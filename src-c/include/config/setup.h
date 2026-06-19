#include <coap3/coap.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>

// #define ENABLE_OSCORE

#ifdef ENABLE_OSCORE
#define OSCORE_CLIENT_SEQ_NUM_FILENAME "/tmp/client.seq"
#define OSCORE_SERVER_SEQ_NUM_FILENAME "/tmp/server.seq"
#endif

coap_session_t *setup_client_session(
#ifdef ENABLE_OSCORE
  coap_address_t *client, coap_address_t *server, const uint16_t port, const char oscore_conf_str[]
#else
  coap_address_t *client, coap_address_t *server, const uint16_t port
#endif
);
coap_context_t *setup_server_context(
#ifdef ENABLE_OSCORE
  coap_context_t *ctx, const char oscore_conf_str[]
#else
  coap_context_t *ctx
#endif
);
