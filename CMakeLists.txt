cmake_minimum_required(VERSION 3.8)
project(sam3_ros)

find_package(ament_cmake REQUIRED)
find_package(ament_cmake_python REQUIRED)
find_package(rosidl_default_generators REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(vision_msgs REQUIRED)

rosidl_generate_interfaces(${PROJECT_NAME}
  "msg/Detection2DWithCompressedMask.msg"
  "msg/Detection2DWithCompressedMaskArray.msg"
  DEPENDENCIES sensor_msgs std_msgs vision_msgs
)

# Keep the node separate from the generated sam3_ros.msg Python package.
ament_python_install_package(sam3_ros_node)
install(PROGRAMS scripts/sam3_node DESTINATION lib/${PROJECT_NAME})
install(DIRECTORY launch weights DESTINATION share/${PROJECT_NAME})

if(BUILD_TESTING)
  find_package(ament_cmake_pytest REQUIRED)
  ament_add_pytest_test(sam3_ros_tests test
    WORKING_DIRECTORY "${CMAKE_CURRENT_SOURCE_DIR}"
  )
endif()

ament_export_dependencies(rosidl_default_runtime)
ament_package()
