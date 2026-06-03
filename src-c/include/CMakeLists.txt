# CONFIG_LIB
add_library(${CONFIG_LIB} OBJECT "${SOURCE_CODE_DIR}/config/oscore.c")
target_include_directories(${CONFIG_LIB} PRIVATE "${INCLUDE_DIR}/config/")
target_link_libraries(${CONFIG_LIB} PUBLIC libcoap::coap-3)

# HELPERS_LIB
add_library(${HELPERS_LIB} OBJECT "${SOURCE_CODE_DIR}/helpers/resolve.c")
target_include_directories(${HELPERS_LIB} PRIVATE "${INCLUDE_DIR}/helpers/")
target_link_libraries(${HELPERS_LIB} PUBLIC libcoap::coap-3)

message("${CMAKE_CURRENT_SOURCE_DIR}: Subdirectory added!")