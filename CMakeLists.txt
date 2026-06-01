cmake_minimum_required(VERSION 3.23)

project(oscoreconf_setup)
list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/build/build/Release)
list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/build)

message("Project: ${PROJECT_NAME}")
message("Libraries: ${CMAKE_MODULE_PATH}")

include(config.cmake)

find_package(OpenSSL REQUIRED)
#find_package(libcoap REQUIRED)

add_subdirectory(thirdparty/libcoap)

set(HELPERS_LIB "helpers")

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/src)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/include)