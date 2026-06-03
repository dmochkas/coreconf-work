#include <coap3/coap.h>
#include <netinet/in.h>
#include <stdio.h>
#include <string.h>

#define OSCORE_CLIENT_SEQ_NUM_FILENAME "/tmp/client.seq"
#define OSCORE_SERVER_SEQ_NUM_FILENAME "/tmp/server.seq"

coap_session_t *setup_client_session(coap_address_t *client, coap_address_t *server, const uint16_t port, const char oscore_conf_str[]);
coap_session_t *setup_server_session(struct in6_addr ip_address);