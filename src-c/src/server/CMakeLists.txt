add_executable(server server.c
              $<TARGET_OBJECTS:${CONFIG_LIB}>)

target_include_directories(server PRIVATE
                            ${PROJECT_BINARY_DIR}
                            ${INCLUDE_DIR})

# Setting parameters
set(ENABLE_SERVER_MODE ON)
set(ENABLE_CLIENT_MODE OFF)

target_link_libraries(server PUBLIC libcoap::coap-3)