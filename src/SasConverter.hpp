#pragma once

// SasConverter — "generate a CIAS element (leaf) from a SAS part".
//
// A PEAS semiconductor document is double-nested: {"semiconductor": {inputs, mosfet|diode|..,
// outputs}, "inputs": {...}}. sas_to_cias dispatches on the device discriminator:
//   mosfet -> a switch leaf (ports drain/gate/source). The atom carries onResistance +
//             gateThresholdVoltage; the CIAS emitter (P2) builds the `S` element + `.model SW`.
//   diode  -> a diode leaf (ports anode/cathode). The atom carries forwardVoltage; the emitter
//             builds the `D` element + `.model D`.
// Origins: REQUIREMENTS = ideal (idealized switch/diode defaults); DATASHEET = from
// datasheetInfo.electrical (modelParams.vto used for Vth only when allowStoredModelParams);
// MKF_MODEL throws. igbt/bjt are deferred (Phase 3).

#include <nlohmann/json.hpp>
#include <string>
#include "Fidelity.hpp"

namespace SAS {

nlohmann::json sas_to_cias(const nlohmann::json& peas,
                           const PEAS::Fidelity& fidelity,
                           const std::string& name = "semiconductor");

} // namespace SAS
