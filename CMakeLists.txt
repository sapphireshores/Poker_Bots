cmake_minimum_required(VERSION 3.20)
project(pokerbots_lab CXX)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

# Release build flags for lab tools
set(CMAKE_CXX_FLAGS_RELEASE "-O3 -march=native -fno-plt -DNDEBUG")

add_executable(lab_tool src/main.cpp src/evaluator.cpp)