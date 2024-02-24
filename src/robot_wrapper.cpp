#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include "custom_control.hpp"  // Assuming this is the header file for your Custom class

namespace py = pybind11;

PYBIND11_MODULE(robot_wrapper, m) {
    py::class_<Custom>(m, "Custom")
        .def(py::init<>())
        .def("control", &Custom::control)
        .def_readwrite("dt", &Custom::dt);
    // You can also wrap other members and methods as needed.
}

class Custom
{
public:
  Custom() {}
  void control(const std::vector<unitree::robot::go2::PathPoint>& goalPoints);

  unitree::robot::go2::SportClient tc;

  int c = 0;
  float dt = 0.002; // 0.001~0.01
};

void Custom::control(const std::vector<unitree::robot::go2::PathPoint>& goalPoints)
{
    c++;
    int32_t ret;
    std::vector<unitree::robot::go2::PathPoint> path = goalPoints;

    ret = tc.TrajectoryFollow(path);
    if(ret != 0){
      std::cout << "Call TrajectoryFollow: " << ret << std::endl;
    }

    std::cout << c << std::endl;
}
