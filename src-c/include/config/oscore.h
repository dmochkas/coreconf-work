#include <coap3/coap.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>

#define OSCORE_CLIENT_SEQ_NUM_FILENAME "/tmp/client.seq"
#define OSCORE_SERVER_SEQ_NUM_FILENAME "/tmp/server.seq"

coap_session_t *setup_oscore_client_session(coap_address_t *client, coap_address_t *server, const uint16_t port, const uint8_t *oscore_conf_str);
coap_context_t *setup_oscore_server_context(coap_context_t *ctx, const uint8_t oscore_conf_str[]);
