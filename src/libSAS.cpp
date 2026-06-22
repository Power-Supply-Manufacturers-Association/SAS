// libSAS — emscripten/embind module for the SAS->CIAS converter (JSON-string ABI).
#include <emscripten/bind.h>
#include "SasConverter.hpp"
#include "FidelityJson.hpp"
#include <nlohmann/json.hpp>
#include <string>

using json = nlohmann::json;

static std::string sas_to_cias_json(std::string peasStr, std::string fidelityStr) {
    try {
        auto leaf = SAS::sas_to_cias(json::parse(peasStr),
                                     PEAS::fidelity_from_json(json::parse(fidelityStr)));
        return leaf.dump();
    } catch (const std::exception& e) {
        return std::string("Exception: ") + e.what();
    }
}

EMSCRIPTEN_BINDINGS(sas) {
    emscripten::function("sas_to_cias", &sas_to_cias_json);
}
