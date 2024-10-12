cmake_minimum_required(VERSION 3.8)
project(bitbots_head_mover)

if(CMAKE_COMPILER_IS_GNUCXX OR CMAKE_CXX_COMPILER_ID MATCHES "Clang")
  add_compile_options(-Wall -Wextra -Wpedantic)
endif()

# find dependencies
find_package(ament_cmake REQUIRED)
find_package(backward_ros REQUIRED)
find_package(bio_ik REQUIRED)
find_package(bio_ik_msgs REQUIRED)
find_package(bitbots_msgs REQUIRED)
find_package(generate_parameter_library REQUIRED)
find_package(bitbots_msgs REQUIRED)
find_package(moveit_core REQUIRED)
find_package(moveit_msgs REQUIRED)
find_package(moveit_ros_planning REQUIRED)
find_package(moveit_ros_planning_interface REQUIRED)
find_package(rclcpp REQUIRED)
find_package(rclcpp_components REQUIRED)
find_package(sensor_msgs REQUIRED)
find_package(std_msgs REQUIRED)
find_package(tf2_geometry_msgs REQUIRED)
find_package(tf2_ros REQUIRED)

set(CMAKE_BUILD_TYPE Debug)

# uncomment the following section in order to fill in further dependencies
# manually. find_package(<dependency> REQUIRED)
generate_parameter_library(
  head_parameters # cmake target name for the parameter library
  config/head_config.yml)

# add_executable(move_head src/move_head.cpp)
add_library(move_head_component SHARED src/move_head.cpp)
target_link_libraries(move_head_component rclcpp::rclcpp head_parameters)

ament_target_dependencies(
  move_head_component
  backward_ros
  bio_ik
  bio_ik_msgs
  bitbots_msgs
  generate_parameter_library
  moveit_core
  moveit_msgs
  moveit_ros_planning
  moveit_ros_planning_interface
  rclcpp
  rclcpp_components
  sensor_msgs
  std_msgs
  tf2_geometry_msgs
  tf2_kdl
  tf2_ros)

rclcpp_components_register_node(move_head_component PLUGIN
                                "move_head::HeadMover" EXECUTABLE move_head)

# install(TARGETS move_head DESTINATION lib/${PROJECT_NAME})
ament_export_targets(export_all_targets)
install(
  TARGETS move_head_component head_parameters
  EXPORT export_all_targets
  ARCHIVE DESTINATION lib
  LIBRARY DESTINATION lib
  RUNTIME DESTINATION bin)
install(DIRECTORY config DESTINATION share/${PROJECT_NAME})

install(DIRECTORY launch DESTINATION share/${PROJECT_NAME})

ament_package()
