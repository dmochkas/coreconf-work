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
  coap_address_t *client, 
  coap_address_t *server, 
  const uint16_t port
#ifdef ENABLE_OSCORE
  , const char oscore_conf_str[]
#endif
);
coap_context_t *setup_server_context(
  coap_context_t *ctx
#ifdef ENABLE_OSCORE
  , const char oscore_conf_str[]
#endif
);
