cmake_minimum_required(VERSION 3.15)
project(SAS LANGUAGES CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
if (NOT CMAKE_CXX_COMPILER_ID STREQUAL "MSVC")
    set(CMAKE_POSITION_INDEPENDENT_CODE ON)
endif()

include(FetchContent)
FetchContent_Declare(json
    GIT_REPOSITORY https://github.com/nlohmann/json.git
    GIT_TAG tags/v3.11.3)
FetchContent_MakeAvailable(json)

find_program(QUICKTYPE quicktype REQUIRED)
set(SAS_HPP "${CMAKE_CURRENT_BINARY_DIR}/SAS.hpp")
set(PEAS_SCHEMAS "${CMAKE_CURRENT_SOURCE_DIR}/../PEAS/schemas")
add_custom_command(
    OUTPUT "${SAS_HPP}"
    COMMAND "${QUICKTYPE}" -l c++ -s schema
            "${CMAKE_CURRENT_SOURCE_DIR}/schemas/SAS.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/mosfet.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/diode.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/igbt.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/bjt.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/inputs.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/inputs/designRequirements.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/outputs.json"
            -S "${CMAKE_CURRENT_SOURCE_DIR}/schemas/utils.json"
            -S "${PEAS_SCHEMAS}/utils.json"
            -S "${PEAS_SCHEMAS}/inputs/twoTerminalOperatingPoint.json"
            -S "${PEAS_SCHEMAS}/inputs/multiPortOperatingPoint.json"
            -S "${PEAS_SCHEMAS}/inputs/operatingConditions.json"
            -S "${PEAS_SCHEMAS}/inputs/operatingPointExcitation.json"
            -S "${PEAS_SCHEMAS}/outputs/outputBase.json"
            -S "${PEAS_SCHEMAS}/outputs/measurementCondition.json"
            -S "${PEAS_SCHEMAS}/outputs/insulationCoordination.json"
            -o "${SAS_HPP}"
            --namespace SAS --source-style single-source --type-style pascal-case
            --member-style underscore-case --enumerator-style upper-underscore-case --no-boost
    DEPENDS "${CMAKE_CURRENT_SOURCE_DIR}/schemas/SAS.json"
            "${CMAKE_CURRENT_SOURCE_DIR}/schemas/mosfet.json"
            "${CMAKE_CURRENT_SOURCE_DIR}/schemas/diode.json"
    COMMENT "Generating SAS.hpp via quicktype"
    VERBATIM)
add_custom_target(sas_generated_header DEPENDS "${SAS_HPP}")

add_library(SAS STATIC src/SasConverter.cpp)
add_dependencies(SAS sas_generated_header)
target_include_directories(SAS PUBLIC
    src
    "${CMAKE_CURRENT_BINARY_DIR}"
    "${CMAKE_CURRENT_SOURCE_DIR}/../PEAS/src")
target_link_libraries(SAS PUBLIC nlohmann_json::nlohmann_json)
target_include_directories(SAS PRIVATE "${json_SOURCE_DIR}/include/nlohmann")

if (NOT EMSCRIPTEN)
    option(SAS_BUILD_TESTS "Build SAS unit tests" ON)
    if (SAS_BUILD_TESTS)
        enable_testing()
        FetchContent_Declare(Catch2
            GIT_REPOSITORY https://github.com/catchorg/Catch2.git GIT_TAG v3.8.1)
        FetchContent_MakeAvailable(Catch2)
        add_executable(sas_tests tests/test_sas.cpp)
        target_link_libraries(sas_tests PRIVATE SAS Catch2::Catch2WithMain)
        add_test(NAME sas_tests COMMAND sas_tests)
    endif()

    option(SAS_BUILD_PYBIND "Build the PySAS pybind11 module" ON)
    if (SAS_BUILD_PYBIND)
        FetchContent_Declare(pybind11
            GIT_REPOSITORY https://github.com/pybind/pybind11.git GIT_TAG v2.13.6)
        FetchContent_Declare(pybind11_json
            GIT_REPOSITORY https://github.com/pybind/pybind11_json.git)
        FetchContent_MakeAvailable(pybind11 pybind11_json)
        pybind11_add_module(PySAS src/bindings.cpp)
        add_dependencies(PySAS sas_generated_header)
        target_include_directories(PySAS PRIVATE
            src "${CMAKE_CURRENT_SOURCE_DIR}/../PEAS/src"
            "${pybind11_json_SOURCE_DIR}/include")
        target_link_libraries(PySAS PRIVATE SAS)
    endif()
else()
    add_executable(libSAS src/libSAS.cpp)
    add_dependencies(libSAS sas_generated_header)
    target_include_directories(libSAS PRIVATE
        src "${CMAKE_CURRENT_SOURCE_DIR}/../PEAS/src")
    target_link_libraries(libSAS PRIVATE SAS)
    set_target_properties(libSAS PROPERTIES SUFFIX ".wasm.js")
    target_compile_options(libSAS PRIVATE -fwasm-exceptions)
    target_link_options(libSAS PRIVATE
        -fwasm-exceptions -sWASM=1 -sALLOW_MEMORY_GROWTH -sEXPORT_ES6=1
        -sMODULARIZE=1 -sENVIRONMENT=web,node --bind)
endif()
