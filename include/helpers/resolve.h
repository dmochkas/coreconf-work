#ifndef HELPERS_RESOLVE_H
#define HELPERS_RESOLVE_H

#include <coap3/coap.h>

int resolve_address(coap_str_const_t *host, uint16_t port, coap_address_t *dst, int scheme_hint_bits);

#endif // HELPERS_RESOLVE_H