add_executable(
  unittest
  ${CMAKE_CURRENT_LIST_DIR}/unittest.c
  ${CMAKE_CURRENT_LIST_DIR}/common/common.h
)

find_package(CUnit REQUIRED)
target_link_libraries(unittest PUBLIC 
                      cunit::cunit)