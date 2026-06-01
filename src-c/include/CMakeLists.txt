add_library(${HELPERS_LIB} OBJECT "${INCLUDE_DIR}/helpers/resolve.h" "${SOURCE_CODE_DIR}/helpers/resolve.c")
target_include_directories(${HELPERS_LIB} PRIVATE "${INCLUDE_DIR}/helpers/")

message("${PROJECT_SOURCE_DIR}/include/helpers/")

target_link_libraries(${HELPERS_LIB} PUBLIC helpers/resolve.h)
target_link_libraries(${HELPERS_LIB} PUBLIC libcoap::coap-3)

message("${CMAKE_CURRENT_SOURCE_DIR}: Subdirectory added!")