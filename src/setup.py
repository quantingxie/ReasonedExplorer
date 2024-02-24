from setuptools import setup, Extension
from pybind11.setup_helpers import Pybind11Extension, build_ext

ext_modules = [
    Pybind11Extension(
        "robot_wrapper",
        ["robot_wrapper.cpp"],
        include_dirs=['path/to/unitree/include'],  # Include path for the Unitree SDK
        library_dirs=['path/to/unitree/lib'],      # Library path for the Unitree SDK
        libraries=['unitree_legged_sdk']           # Unitree SDK libraries to link against
    ),
]

setup(
    name="robot_wrapper",
    ext_modules=ext_modules,
    cmdclass={"build_ext": build_ext},
)