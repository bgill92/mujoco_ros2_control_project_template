cmake_minimum_required(VERSION 3.20)
project(my_robot_description)

find_package(ament_cmake REQUIRED)

# Add `meshes` here once the robot has mesh files.
install(DIRECTORY launch rviz urdf
  DESTINATION share/${PROJECT_NAME}
)

if(BUILD_TESTING)
  find_package(ament_lint_auto REQUIRED)
  set(ament_cmake_copyright_FOUND TRUE)
  set(ament_cmake_cpplint_FOUND TRUE)
  ament_lint_auto_find_test_dependencies()
endif()

ament_package()
