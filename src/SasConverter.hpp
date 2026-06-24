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
#include <cmath>
#include <algorithm>
#include "Fidelity.hpp"

namespace SAS {

// ── DIDEAL (MKF) ideal-rectifier reference — THE single source of truth for the ideal diode's forward
// characteristic. sas_to_cias stamps the ideal diode leaf with forwardVoltage = IDEAL_DIODE_VF_REF, and the
// CIAS emitter back-solves the ngspice model as IS = I_ref·exp(-Vf_ref/Vt). So the emitted diode's drop is
// EXACTLY Vf(I) = IDEAL_DIODE_VF_REF + Vt·ln(I/I_ref). Any consumer that must COMPENSATE for this drop at
// design time (a converter sizing its turns ratio, etc.) must use ideal_diode_drop(I) below — so the
// design-time compensation and the emitted model can never drift apart. ──
constexpr double IDEAL_DIODE_VF_REF = 0.8334;    // forward drop at the reference current (-> IS=1e-14 @ 1 A)
constexpr double IDEAL_DIODE_I_REF  = 1.0;       // reference current the drop is rated at [A]
constexpr double IDEAL_DIODE_VT     = 0.025852;  // thermal voltage kT/q (ngspice 27 °C default == CIAS Vt)

// Forward drop of the DIDEAL rectifier at a given current — Vf(I) = Vf_ref + Vt·ln(I/I_ref).
inline double ideal_diode_drop(double current) {
    return IDEAL_DIODE_VF_REF + IDEAL_DIODE_VT * std::log(std::max(current, 1e-9) / IDEAL_DIODE_I_REF);
}

nlohmann::json sas_to_cias(const nlohmann::json& peas,
                           const PEAS::Fidelity& fidelity,
                           const std::string& name = "semiconductor");

} // namespace SAS
