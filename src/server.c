#include <coap3/coap.h>

#include "definitions.h"

int main() {
  
  coap_startup();
  coap_set_log_level(LOG_NOTICE);

  coap_address_t server;
  coap_address_init(&server);
  

  return 0;
}