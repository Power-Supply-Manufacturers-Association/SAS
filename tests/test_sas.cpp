// Minimal dependency-free unit tests for sas_to_cias.
#include "SasConverter.hpp"
#include "Fidelity.hpp"
#include <nlohmann/json.hpp>
#include <iostream>

using nlohmann::json;
using PEAS::Fidelity;

#include <catch2/catch_test_macros.hpp>
#define CHECK_MSG(cond, ...) do { INFO(__VA_ARGS__); CHECK(cond); } while (0)

static double mosfet_ron(const json& leaf) {
    return leaf.at("components").at(0).at("data").at("semiconductor").at("mosfet")
               .at("manufacturerInfo").at("datasheetInfo").at("electrical").at("onResistance").get<double>();
}
static double mosfet_vth(const json& leaf) {
    return leaf.at("components").at(0).at("data").at("semiconductor").at("mosfet")
               .at("manufacturerInfo").at("datasheetInfo").at("electrical")
               .at("gateThresholdVoltage").at("nominal").get<double>();
}
static double diode_vf(const json& leaf) {
    return leaf.at("components").at(0).at("data").at("semiconductor").at("diode")
               .at("manufacturerInfo").at("datasheetInfo").at("electrical").at("forwardVoltage").get<double>();
}

TEST_CASE("SAS sas_to_cias", "[sas]") {
    // --- mosfet, real (DATASHEET): Ron + Vth from electrical ---
    json mosfetDoc = json::parse(R"({
        "semiconductor": { "mosfet": { "manufacturerInfo": { "name": "Infineon", "datasheetInfo": {
            "part": { "partNumber": "IPW60R070", "technology": "Si" },
            "electrical": { "drainSourceVoltage": 650, "onResistance": 0.07,
                "continuousDrainCurrent": 30, "gateThresholdVoltage": { "nominal": 3.0 },
                "totalGateCharge": 1.5e-7 },
            "modelParams": { "vto": 3.5 } } } } }
    })");
    json mleaf = SAS::sas_to_cias(mosfetDoc, Fidelity(Fidelity::Origin::DATASHEET));
    CHECK_MSG(mleaf.at("ports").size() == 3, "mosfet: 3 ports (drain/gate/source)");
    CHECK_MSG(mleaf.at("ports").at(0).at("name") == "drain", "mosfet: port[0]=drain");
    CHECK_MSG(mosfet_ron(mleaf) == 0.07, "mosfet real: Ron from electrical (0.07)");
    CHECK_MSG(mosfet_vth(mleaf) == 3.0, "mosfet real: Vth from electrical (3.0)");

    // allowStored -> Vth from modelParams.vto (3.5)
    json mleafStored = SAS::sas_to_cias(mosfetDoc, Fidelity(Fidelity::Origin::DATASHEET, true));
    CHECK_MSG(mosfet_vth(mleafStored) == 3.5, "mosfet real+allowStored: Vth from modelParams.vto (3.5)");

    // ideal mosfet -> default ideal switch
    json mleafIdeal = SAS::sas_to_cias(mosfetDoc, Fidelity(Fidelity::Origin::REQUIREMENTS));
    CHECK_MSG(mosfet_ron(mleafIdeal) == 0.01, "mosfet ideal: Ron = ideal default (10m, = MKF SW1 RON)");

    // --- diode, real ---
    json diodeDoc = json::parse(R"({
        "semiconductor": { "diode": { "manufacturerInfo": { "name": "Wolfspeed", "datasheetInfo": {
            "part": { "partNumber": "C3D10065A", "technology": "SiC" },
            "electrical": { "reverseVoltage": 650, "forwardVoltage": 1.5, "forwardCurrent": 10 } } } } }
    })");
    json dleaf = SAS::sas_to_cias(diodeDoc, Fidelity(Fidelity::Origin::DATASHEET));
    CHECK_MSG(dleaf.at("ports").size() == 2, "diode: 2 ports (anode/cathode)");
    CHECK_MSG(diode_vf(dleaf) == 1.5, "diode real: Vf from electrical (1.5)");

    json dleafIdeal = SAS::sas_to_cias(diodeDoc, Fidelity(Fidelity::Origin::REQUIREMENTS));
    CHECK_MSG(diode_vf(dleafIdeal) == 0.8334, "diode ideal: Vf = ideal default (0.8334 -> IS=1e-14, = MKF DIDEAL)");

    // --- MKF_MODEL throws ---
    bool threw = false;
    try { SAS::sas_to_cias(mosfetDoc, Fidelity(Fidelity::Origin::MKF_MODEL)); }
    catch (const std::exception&) { threw = true; }
    CHECK_MSG(threw, "MKF_MODEL origin throws for SAS");
}

TEST_CASE("SAS real MOSFET -> multi-atom (switch + Coss + body diode)", "[sas][real][mosfet]") {
    json doc = json::parse(R"({
        "semiconductor": { "mosfet": { "manufacturerInfo": { "name": "Infineon", "datasheetInfo": {
            "part": { "partNumber": "IPP60R099", "technology": "Si" },
            "electrical": { "drainSourceVoltage": 600, "onResistance": 0.099,
                "continuousDrainCurrent": 30, "gateThresholdVoltage": { "nominal": 3.5 },
                "totalGateCharge": 1.5e-7,
                "outputCapacitance": 1.9e-10, "bodyDiodeForwardVoltage": 0.9 } } } } }
    })");
    json leaf = SAS::sas_to_cias(doc, Fidelity(Fidelity::Origin::DATASHEET));
    REQUIRE(leaf.at("components").size() == 3);
    bool hasQ = false, hasCoss = false, hasDbody = false;
    for (const auto& c : leaf.at("components")) {
        const std::string n = c.at("name");
        if (n == "Q") hasQ = true;
        if (n == "Coss") hasCoss = true;
        if (n == "Dbody") hasDbody = true;
    }
    CHECK_MSG(hasQ, "switch atom Q present");
    CHECK_MSG(hasCoss, "output-capacitance atom Coss present");
    CHECK_MSG(hasDbody, "body-diode atom Dbody present");
    CHECK_MSG(SAS::sas_to_cias(doc, Fidelity(Fidelity::Origin::REQUIREMENTS)).at("components").size() == 1,
              "ideal MOSFET = single switch atom");
}
