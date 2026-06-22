#include "SasConverter.hpp"
#include "SAS.hpp"        // quicktype-generated typed structs (build/SAS.hpp)
#include "Dimension.hpp"  // PEAS::resolve_dimensional_values

#include <stdexcept>
#include <optional>

namespace SAS {

using nlohmann::json;

namespace {

// Idealized switch/diode modeling constants (used for the REQUIREMENTS/ideal origin — these are
// the *definition* of an ideal device, not data fallbacks).
//
// These are pinned to MKF's ideal converter models so a Kirchhoff simulation reproduces MKF's
// design+simulation with ideal components (see Kirchhoff/tests/test_mkf_equivalence.cpp):
//   MKF switch  : `.model SW1 SW VT=2.5 VH=0.5 RON=0.01 ROFF=1e6`
//   MKF diode   : `.model DIDEAL D(IS=1e-14 RS=1e-6)`
// The diode is parameterized here by forward voltage; the CIAS converter maps it to the
// ngspice saturation current IS = exp(-Vf/Vt) with Vt = 0.025852 V (ngspice 27 °C default),
// so Vf = 0.8334 V yields IS = 1e-14 — identical to MKF's DIDEAL.
constexpr double IDEAL_SW_RON  = 0.01;     // ohm  (MKF SW1 RON)
constexpr double IDEAL_SW_VTH  = 2.5;      // V    (MKF SW1 VT; gate threshold of the modeled switch)
constexpr double IDEAL_D_VF    = 0.8334;   // V -> IS = exp(-Vf/0.025852) = 1e-14 (MKF DIDEAL)

json pin_port_net(const std::string& net, const std::string& comp,
                  const std::string& pin, const std::string& port) {
    json endpoints = json::array();
    endpoints.push_back(json{{"component", comp}, {"pin", pin}});
    endpoints.push_back(json{{"port", port}});
    return json{{"name", net}, {"endpoints", endpoints}};
}

json make_diode_atom(const json& electrical);  // defined in the diode section below

// --- MOSFET: switch leaf carrying onResistance + gateThresholdVoltage ---
json make_mosfet_atom(double ron, double vth) {
    json electrical;
    electrical["onResistance"] = ron;
    electrical["gateThresholdVoltage"]["nominal"] = vth;

    json atom;
    auto& mfg = atom["semiconductor"]["mosfet"]["manufacturerInfo"];
    mfg["name"] = "ideal";
    mfg["datasheetInfo"]["part"]["partNumber"] = "ideal";
    mfg["datasheetInfo"]["part"]["technology"] = "Si";
    mfg["datasheetInfo"]["electrical"] = electrical;
    return atom;
}

// A parasitic capacitor atom (CIAS reads capacitor...electrical.capacitance). Used for MOSFET Coss.
json make_cap_atom(double c) {
    json atom;
    auto& mfg = atom["capacitor"]["manufacturerInfo"];
    mfg["name"] = "parasitic";
    mfg["datasheetInfo"]["part"]["partNumber"] = "coss";
    mfg["datasheetInfo"]["electrical"]["capacitance"]["nominal"] = c;
    return atom;
}

json mosfet_leaf(const json& peas, const PEAS::Fidelity& fidelity, const std::string& name) {
    double ron = IDEAL_SW_RON, vth = IDEAL_SW_VTH;
    std::optional<double> coss, bodyVf;
    if (fidelity.is_real()) {
        auto mosfet = peas.at("semiconductor").at("mosfet").get<Mosfet>();
        // manufacturerInfo is optional in the schema (seed parts have none); a REAL part must carry it.
        const auto& mfg = mosfet.get_manufacturer_info();
        if (!mfg) throw std::runtime_error("SAS real mosfet: manufacturerInfo.datasheetInfo missing");
        const auto& elec = mfg->get_datasheet_info().get_electrical();
        ron = elec.get_on_resistance();
        if (fidelity.allowStoredModelParams) {
            auto mp = mfg->get_datasheet_info().get_model_params();
            if (mp && mp->get_vto()) vth = *mp->get_vto();
            else vth = PEAS::resolve_dimensional_values(elec.get_gate_threshold_voltage());
        } else {
            vth = PEAS::resolve_dimensional_values(elec.get_gate_threshold_voltage());
        }
        if (elec.get_output_capacitance()) coss = *elec.get_output_capacitance();
        if (elec.get_body_diode_forward_voltage()) bodyVf = *elec.get_body_diode_forward_voltage();
    }

    json ports = json::array();
    for (auto p : {"drain", "gate", "source"}) ports.push_back(json{{"name", p}});
    json components = json::array({json{{"name", "Q"}, {"data", make_mosfet_atom(ron, vth)}}});

    // The switch, plus (for a real part) its output capacitance Coss and body diode, all sit across
    // drain-source. The assembler inlines this multi-atom equivalent circuit into the stage subckt.
    json drainEps  = json::array({json{{"component", "Q"}, {"pin", "drain"}},  json{{"port", "drain"}}});
    json sourceEps = json::array({json{{"component", "Q"}, {"pin", "source"}}, json{{"port", "source"}}});
    if (coss) {
        components.push_back(json{{"name", "Coss"}, {"data", make_cap_atom(*coss)}});
        drainEps.push_back(json{{"component", "Coss"}, {"pin", "1"}});
        sourceEps.push_back(json{{"component", "Coss"}, {"pin", "2"}});
    }
    if (bodyVf) {
        json el; el["forwardVoltage"] = *bodyVf;
        components.push_back(json{{"name", "Dbody"}, {"data", make_diode_atom(el)}});
        drainEps.push_back(json{{"component", "Dbody"}, {"pin", "cathode"}});   // body diode S->D
        sourceEps.push_back(json{{"component", "Dbody"}, {"pin", "anode"}});
    }
    json connections = json::array({
        json{{"name", "drain"},  {"endpoints", drainEps}},
        json{{"name", "gate"},   {"endpoints", json::array({json{{"component", "Q"}, {"pin", "gate"}},
                                                            json{{"port", "gate"}}})}},
        json{{"name", "source"}, {"endpoints", sourceEps}}});

    json leaf;
    leaf["name"] = name;
    leaf["ports"] = ports;
    leaf["components"] = components;
    leaf["connections"] = connections;
    return leaf;
}

// --- DIODE: diode leaf carrying the (ideal or datasheet) electrical block. The CIAS converter builds
// the ngspice .model D() from it: IS from Vf@I, plus CJO/TT/BV for a real part. ---
json make_diode_atom(const json& electrical) {
    json atom;
    auto& mfg = atom["semiconductor"]["diode"]["manufacturerInfo"];
    mfg["name"] = "ideal";
    mfg["datasheetInfo"]["part"]["partNumber"] = "ideal";
    mfg["datasheetInfo"]["part"]["technology"] = "Si";
    mfg["datasheetInfo"]["electrical"] = electrical;
    return atom;
}

json diode_leaf(const json& peas, const PEAS::Fidelity& fidelity, const std::string& name) {
    json electrical;
    if (fidelity.is_real()) {
        auto diode = peas.at("semiconductor").at("diode").get<Diode>();   // validate structure
        const auto& mfg = diode.get_manufacturer_info();
        if (!mfg) throw std::runtime_error("SAS real diode: manufacturerInfo.datasheetInfo missing");
        if (!mfg->get_datasheet_info().get_electrical().get_forward_voltage())
            throw std::runtime_error("SAS real diode: electrical.forwardVoltage missing");
        // Carry the datasheet electrical block forward (Vf, Vf@I, junctionCapacitance, trr, BV, ...).
        electrical = peas.at("semiconductor").at("diode").at("manufacturerInfo")
                         .at("datasheetInfo").at("electrical");
    } else {
        electrical["forwardVoltage"] = IDEAL_D_VF;   // ideal: IS=1e-14 at 1 A (matches MKF DIDEAL)
    }

    json ports = json::array();
    for (auto p : {"anode", "cathode"}) ports.push_back(json{{"name", p}});
    json components = json::array();
    components.push_back(json{{"name", "D"}, {"data", make_diode_atom(electrical)}});
    json connections = json::array();
    connections.push_back(pin_port_net("anode",   "D", "anode",   "anode"));
    connections.push_back(pin_port_net("cathode", "D", "cathode", "cathode"));

    json leaf;
    leaf["name"] = name;
    leaf["ports"] = ports;
    leaf["components"] = components;
    leaf["connections"] = connections;
    return leaf;
}

} // namespace

json sas_to_cias(const json& peas, const PEAS::Fidelity& fidelity, const std::string& name) {
    PEAS::reject_mkf_model(fidelity, "SAS");
    if (!peas.contains("semiconductor"))
        throw std::runtime_error("SAS: not a semiconductor PEAS document");
    const auto& semi = peas.at("semiconductor");
    if (semi.contains("mosfet")) return mosfet_leaf(peas, fidelity, name);
    if (semi.contains("diode"))  return diode_leaf(peas, fidelity, name);
    throw std::runtime_error("SAS: only mosfet/diode supported in the slice (igbt/bjt = Phase 3)");
}

} // namespace SAS
