cmake_minimum_required(VERSION 3.23)

project(oscoreconf_setup)
list(APPEND CMAKE_MODULE_PATH ${PROJECT_SOURCE_DIR}/build/build/Release)

# Project options
option(
  PROJ_ENABLE_TESTS
  "Compile project with unit tests"
)
option(
  PROJ_CLIENT
  "Compile client"
)
option(
  PROJ_SERVER
  "Compile server"
)

# Use config.cmake to set library/project options
include(config.cmake)

# Dependencies
find_package(OpenSSL REQUIRED)
add_subdirectory(thirdparty/libcoap)

# Project code folder
add_subdirectory(src-c)

# Project summary
message(NOTICE)
message(NOTICE "Project Summary:")
message(NOTICE)
message(NOTICE "Project: ${PROJECT_NAME}")
message(NOTICE "Version: ${PROJECT_VERSION}")
message(NOTICE "Building tests:   ${PROJ_ENABLE_TESTS}")
message(NOTICE "Building client:  ${PROJ_CLIENT}")
message(NOTICE "Building server:  ${PROJ_SERVER}")
message(NOTICE)