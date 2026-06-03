add_executable(client client.c
              $<TARGET_OBJECTS:${HELPERS_LIB}>)

target_include_directories(client PRIVATE
                            ${PROJECT_BINARY_DIR}
                            ${INCLUDE_DIR})

target_link_libraries(client PUBLIC libcoap::coap-3)