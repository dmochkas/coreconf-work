add_executable(server server.c)

target_include_directories(server PRIVATE
                            ${PROJECT_BINARY_DIR}
                            ${INCLUDE_DIR})

target_link_libraries(server PUBLIC libcoap::coap-3)