CXX ?= c++
CXXFLAGS ?= -std=c++17 -Wall -Wextra -Wpedantic -Werror -O2
CPPFLAGS ?= -Iinclude
PYTHON ?= python3

TARGET := build/os-shell
PARSER_TEST := build/parser-tests
SOURCES := src/main.cpp src/parser.cpp src/shell.cpp src/scheduler.cpp
OBJECTS := $(SOURCES:src/%.cpp=build/%.o)

.PHONY: all clean test

all: $(TARGET)

$(TARGET): $(OBJECTS)
	$(CXX) $(CXXFLAGS) $(OBJECTS) -o $@

build/%.o: src/%.cpp | build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) -MMD -MP -c $< -o $@

-include $(OBJECTS:.o=.d)

$(PARSER_TEST): tests/test_parser.cpp src/parser.cpp include/parser.hpp | build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) tests/test_parser.cpp src/parser.cpp -o $@

build:
	mkdir -p build

build/scheduler-tests: tests/test_scheduler.cpp src/scheduler.cpp include/scheduler.hpp | build
	$(CXX) $(CPPFLAGS) $(CXXFLAGS) tests/test_scheduler.cpp src/scheduler.cpp -o $@

test: $(TARGET) $(PARSER_TEST) build/scheduler-tests
	./$(PARSER_TEST)
	./build/scheduler-tests
	$(PYTHON) tests/integration_test.py
	$(PYTHON) tests/scheduler_integration_test.py

clean:
	rm -rf build

