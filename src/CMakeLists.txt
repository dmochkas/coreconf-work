add_library(${HELPERS_LIB} OBJECT "${CMAKE_CURRENT_SOURCE_DIR}/helpers/resolve.c")
target_include_directories(${HELPERS_LIB} PRIVATE "${PROJECT_SOURCE_DIR}/include/helpers/")

add_executable(oscoreconf_client client.c
            $<TARGET_OBJECTS:${HELPERS_LIB}>)
add_executable(oscoreconf_server server.c)

target_include_directories(oscoreconf_server PRIVATE 
                            "${PROJECT_BINARY_DIR}"
                            "${PROJECT_SOURCE_DIR}/include")

target_include_directories(oscoreconf_client PRIVATE
                            "${PROJECT_BINARY_DIR}"
                            "${PROJECT_SOURCE_DIR}/include")

target_link_libraries(oscoreconf_client libcoap::coap-3)
target_link_libraries(oscoreconf_server libcoap::coap-3)