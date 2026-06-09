set(INCLUDE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/include")
set(SOURCE_CODE_DIR "${CMAKE_CURRENT_SOURCE_DIR}/src")

set(CONFIG_LIB "config")
set(HELPERS_LIB "helpers")

add_subdirectory(${INCLUDE_DIR})
add_subdirectory(${SOURCE_CODE_DIR})

if(${PROJ_ENABLE_TESTS})
  add_subdirectory("./tests")
  message(STATUS "Compiling project with tests")
endif()