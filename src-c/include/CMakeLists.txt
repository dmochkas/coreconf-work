# HELPERS_LIB
add_library(${HELPERS_LIB} OBJECT "${SOURCE_CODE_DIR}/helpers/resolve.c")
target_include_directories(${HELPERS_LIB} PRIVATE "${INCLUDE_DIR}/helpers/")
target_link_libraries(${HELPERS_LIB} PUBLIC libcoap::coap-3)

message("${CMAKE_CURRENT_SOURCE_DIR}: Subdirectory added!")