add_executable(oscoreconf_client client.c
            $<TARGET_OBJECTS:${HELPERS_LIB}>)
add_executable(oscoreconf_server server.c)

target_include_directories(oscoreconf_server PRIVATE 
                            "${PROJECT_BINARY_DIR}"
                            "${PROJECT_SOURCE_DIR}/src-c/include")

target_include_directories(oscoreconf_client PRIVATE
                            "${PROJECT_BINARY_DIR}"
                            "${PROJECT_SOURCE_DIR}/src-c/include")

target_link_libraries(oscoreconf_client libcoap::coap-3)
target_link_libraries(oscoreconf_server libcoap::coap-3)