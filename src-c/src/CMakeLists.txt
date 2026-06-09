if(${PROJ_CLIENT})
  add_subdirectory(client)
  message(STATUS "Compiling project with client")
endif()

if(${PROJ_SERVER})
  add_subdirectory(server)
  message(STATUS "Compiling project with server")
endif()