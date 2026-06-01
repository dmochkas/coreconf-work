#include <arpa/inet.h>
#include <netdb.h>
#include <stdio.h>
#include <string.h>
#include <sys/socket.h>

#include "resolve.h"

/**
 * @brief Resolves host and port.
 * 
 * @param host 
 * @param port 
 * @param dst 
 * @param scheme_hint_bits 
 * @return int 
 */
int resolve_address(coap_str_const_t *host, uint16_t port, coap_address_t *dst, int scheme_hint_bits) {
  int ret = 1;
  coap_addr_info_t *addr_info;

  addr_info = coap_resolve_address_info(host, port, port, port, port, AF_INET6, scheme_hint_bits, COAP_RESOLVE_TYPE_REMOTE);

  if (addr_info) {
    *dst = addr_info->addr;
    ret = 0;
  }
  
  coap_free_address_info(addr_info);
  return ret;
}