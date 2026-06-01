cmake_minimum_required(VERSION 3.23)

project(oscoreconf_setup)
list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/build/build/Release)

message("Project: ${PROJECT_NAME}")
message("Libraries: ${CMAKE_MODULE_PATH}")

include(config.cmake)

find_package(OpenSSL REQUIRED)
#find_package(libcoap REQUIRED)

add_subdirectory(thirdparty/libcoap)

add_subdirectory(src-c)