cmake_minimum_required(VERSION 3.23)

project(oscoreconf_setup)
list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/build)

message("Project: ${PROJECT_NAME}")
message("Libraries: ${CMAKE_MODULE_PATH}")

# find_package(libcoap REQUIRED)

include(config.cmake)

find_package(OpenSSL REQUIRED)
# find_package(libcoap REQUIRED)
include(${PROJECT_SOURCE_DIR}/build/libcoap-config.cmake)

set(HELPERS_LIB "helpers")

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/include)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/src)