cmake_minimum_required(VERSION 3.23)

project(oscoreconf_setup)

message("Project: ${PROJECT_NAME}")

include(config.cmake)

add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/include)
add_subdirectory(${CMAKE_CURRENT_SOURCE_DIR}/src)

target_include_directories(oscoreconf_server PRIVATE 
                            "${PROJECT_BINARY_DIR}"
                            "${PROJECT_SOURCE_DIR}/include")

target_include_directories(oscoreconf_client PRIVATE
                            "${PROJECT_BINARY_DIR}"
                            "${PROJECT_SOURCE_DIR}/include")