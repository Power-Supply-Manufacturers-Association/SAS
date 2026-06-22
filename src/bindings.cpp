// PySAS — pybind11 module exposing the SAS->CIAS converter.
#include <pybind11/pybind11.h>
#include <pybind11_json/pybind11_json.hpp>
#include "SasConverter.hpp"
#include "FidelityJson.hpp"

namespace py = pybind11;
using json = nlohmann::json;

PYBIND11_MODULE(PySAS, m) {
    m.doc() = "SAS (semiconductor) -> CIAS leaf converter";
    m.def("sas_to_cias",
          [](const json& peas, const json& fidelity, const std::string& name) {
              return SAS::sas_to_cias(peas, PEAS::fidelity_from_json(fidelity), name);
          },
          py::arg("peas"), py::arg("fidelity"), py::arg("name") = "semiconductor",
          "Convert a SAS semiconductor (mosfet/diode) PEAS document to a CIAS leaf.");
}
