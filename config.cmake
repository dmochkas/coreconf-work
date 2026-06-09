  # Project configurations

set(PROJ_ENABLE_TESTS ON)
set(PROJ_CLIENT ON)
set(PROJ_SERVER ON)

  # libcoap configurations

# Disable IPv4, TCP
set(ENABLE_TCP OFF)
set(ENABLE_IPV4 OFF)

# Enable IPv6, CLIENT_MODE, SERVER_MODE, OSCORE (all on by default)
set(ENABLE_IPV6 ON)
set(ENABLE_CLIENT_MODE ON)
set(ENABLE_SERVER_MODE ON)
set(ENABLE_OSCORE ON)