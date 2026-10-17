<h1 align="center">SAS - Semiconductor Agnostic Structure</h1>

<p align="center">
  <em>The universal data format for semiconductor components in power electronics</em>
</p>

<p align="center">
  <a href="https://opensource.org/licenses/MIT"><img src="https://img.shields.io/badge/License-MIT-yellow.svg" alt="License: MIT"></a>
  <a href="https://json-schema.org/"><img src="https://img.shields.io/badge/JSON%20Schema-2020--12-blue.svg" alt="JSON Schema"></a>
</p>

---

## What is SAS?

**SAS is a standardized way to describe semiconductor components** -- MOSFETs, diodes, IGBTs, BJTs, thyristors (SCR, triac, sidac, diac, thyristor surge protectors), JFETs, optocouplers and multi-die power modules -- used in power electronics. It captures everything from absolute maximum ratings and electrical characteristics to SPICE model parameters and characteristic curves, all in a single machine-readable JSON file.

SAS is part of the **OpenConverters** family of agnostic structures:

```
PEAS (Power Electronics Agnostic Structure) -- Universal container
 |
 +-- MAS (Magnetic Agnostic Structure) -- Inductors, transformers, chokes
 +-- CAS (Capacitor Agnostic Structure) -- Capacitors
 +-- SAS (Semiconductor Agnostic Structure) -- MOSFETs, diodes, IGBTs, BJTs, thyristors, JFETs, optocouplers, power modules
 +-- RAS (Resistor Agnostic Structure) -- Resistors
```

Every valid SAS document is also a valid PEAS document. SAS is a sibling to MAS (for magnetics) and CAS (for capacitors), all sharing the same three-section `inputs / component / outputs` architecture defined by PEAS.

### SAS/data/ vs TAS/data/

An important distinction: **SAS/data/** is reserved for manufacturing building blocks -- semiconductor dies and packages -- and is **currently empty** (the former seed records were finished orderable parts and were moved out; those parts live in **TAS/data/** alongside the ~29k other catalogued semiconductors). **Finished semiconductor components** (the parts you actually order and solder) always go in **TAS/data/**: think of SAS/data/ as the bill of materials for the semiconductor fab, and TAS/data/ as the distributor catalog.

### The Problem SAS Solves

| Without SAS | With SAS |
|-------------|----------|
| MOSFET specs scattered across datasheets and spreadsheets | **One file** with all electrical, thermal, and mechanical data |
| Manual extraction of SPICE parameters from datasheets | **modelParams** section ready for simulation |
| No machine-readable format for characteristic curves | **curves** section with digitized datasheet graphs |
| Different formats for MOSFETs vs diodes vs IGBTs | **One schema family** with a per-device file selected by field name (`oneOf` over `mosfet`/`diode`/`igbt`/`bjt`/`module`) |
| Ambiguous parameter conditions (R_DS(on) at which V_GS?) | **Explicit test conditions** stored alongside every spec |

---

## How It Works

### The Three Sections

Every SAS document has three parts, matching the PEAS pattern:

```
+----------------+     +------------------+     +----------------+
|     INPUTS     |     |  SEMICONDUCTOR   |     |    OUTPUTS     |
+----------------+     +------------------+     +----------------+
| What you NEED  |  +  | What it IS       |  =  | What you GET   |
|                |     |                  |     |                |
| Design         |     | Part info        |     | Conduction     |
| requirements   |     | Electrical specs |     | losses         |
| Operating      |     | SPICE params     |     | Switching      |
| points         |     | Curves           |     | losses         |
|                |     | Thermal data     |     | Junction       |
|                |     | Mechanical dims  |     | temperature    |
+----------------+     +------------------+     +----------------+
```

### The field-name discriminator

`SAS.json` carries `inputs`, `outputs`, and **exactly one** of
`{mosfet, diode, igbt, bjt, thyristor, jfet, optocoupler, module}` — enforced by a top-level `oneOf`. **The field name
*is* the discriminator; there is no `deviceType` property.** Each device field
`$ref`s its own schema file, so a MOSFET document simply has no `diode` key and
vice versa:

```
SAS.json
  +-- inputs           ./inputs.json
  +-- oneOf (exactly one of):
  |     +-- mosfet     ./mosfet.json
  |     +-- diode      ./diode.json
  |     +-- igbt       ./igbt.json
  |     +-- bjt        ./bjt.json
  |     +-- thyristor  ./thyristor.json   (SCR, triac, sidac, diac, surge protector)
  |     +-- jfet       ./jfet.json
  |     +-- optocoupler ./optocoupler.json
  |     +-- module     ./module.json   (multi-die power module)
  +-- outputs[]        ./outputs.json  (aligned positionally with inputs.operatingPoints)
```

Each device file has the same outer shape — `manufacturerInfo` (+ nested
`datasheetInfo`) and `distributorsInfo` — and its `datasheetInfo` carries the
**device-specific** sections directly (no `mosfetElectrical`/`diodeElectrical`
prefixes — the file it lives in already fixes the device type):

```
<device>.json                       (mosfet | diode | igbt | bjt | thyristor | jfet | optocoupler | module)
  +-- manufacturerInfo
  |     +-- name, reference, status, family, datasheetUrl, spiceModel, ...
  |     +-- datasheetInfo
  |           +-- part         (required)  partNumber, technology, subType, case
  |           +-- electrical   (required)  device-specific ratings
  |           +-- dies                     mosfet + bjt: one entry per die in a
  |           |                            multi-die package, INSTEAD OF electrical
  |           +-- matching                 bjt only: matching specs between die
  |           +-- packagePowerDissipation  bjt only, beside dies: package P_tot
  |           +-- thermal                  R_th, T_j range, Foster network
  |           +-- mechanical               package dims, assembly type
  |           +-- modelParams              SPICE parameters   (not bjt)
  |           +-- curves                   digitized graphs   (not bjt)
  |           +-- provenance               data-source trail
  +-- distributorsInfo                cost/stock/MOQ/packaging per distributor
  +-- substitutesInfo                 successors + second sources (PEAS substituteInfo)
  +-- spiceModel                      structured .model card, for parts whose
                                      only source is a simulation model
```

A device body must carry `manufacturerInfo` **or** the device-body `spiceModel`
(or be empty). `part.subType` is narrowed by each device file to a **closed
per-device enum**: mosfet `nChannel`/`pChannel`/`powerBlock`, diode
`rectifier`/`schottky`/`sicSchottky`/`fastRecovery`/`ultrafast`/`switching`/`pin`/
`zener`/`tvs`/`esd`,
igbt `nChannel`, bjt `npn`/`pnp`, module (mirrors its `electrical.topology` enum:
`halfBridge`, `fullBridge`, `sixpack`, ...).

This means a MOSFET file never has empty diode fields, and a diode file never has
empty MOSFET fields — each device type only carries the fields relevant to it.

```mermaid
classDiagram
    class SAS {
        +inputs
        +oneOf~mosfet|diode|igbt|bjt|module~
        +outputs
    }
    class device {
        +manufacturerInfo
        +distributorsInfo
        +substitutesInfo
    }
    class datasheetInfo {
        +part
        +electrical
        +thermal
        +mechanical
        +modelParams
        +curves
    }
    class MOSFET {
        drainSourceVoltage
        onResistance
        gateCharge
    }
    class Diode {
        reverseVoltage
        forwardVoltage
    }
    class IGBT {
        collectorEmitterVoltage
        turnOnEnergy
    }
    class BJT {
        collectorEmitterVoltage
        dcCurrentGain
    }
    SAS --> device : field name = mosfet|diode|igbt|bjt|module
    device --> datasheetInfo
    datasheetInfo --> MOSFET : in mosfet.json
    datasheetInfo --> Diode : in diode.json
    datasheetInfo --> IGBT : in igbt.json
    datasheetInfo --> BJT : in bjt.json
```

```mermaid
flowchart LR
    DS["Manufacturer<br/>Datasheet PDF"] --> Extract["Parameter<br/>Extraction"]
    Extract --> Validate["Validate against<br/>SAS schema"]
    Validate --> NDJSON["TAS/data/<br/>mosfets.ndjson<br/>diodes.ndjson<br/>igbts.ndjson<br/>bjts.ndjson"]
    NDJSON --> Select["Component<br/>Selection"]
    Select --> TAS["TAS Converter<br/>Design Document"]
```

Note the TAS catalog records are **PEAS-wrapped**: each NDJSON line is
`{"semiconductor": {"mosfet": {...}}}` (or `diode`/`igbt`/`bjt`), i.e. the SAS
device body nested under PEAS's `semiconductor` discriminator — not a bare SAS
document.

---

## Device Type Coverage

### MOSFET (Si, SiC, GaN, GaAs)

- **electrical** -- V_DS, R_DS(on), I_D, V_GS(th), gate charge (Q_g, Q_gs, Q_gd), capacitances (C_iss, C_oss, C_rss), switching times, body diode specs, avalanche energy, figure of merit
- **dies** -- multi-die packages (duals, complementary pairs, two-FET power blocks): one entry per die, each `{name, role, pins, subType, electrical, thermal}` with the full electrical block above. Mutually exclusive with the package-level `electrical`, and **required** once `part.dieConfiguration` is `dual` or `complementary` -- so one die's R_DS(on) cannot be stored as the part's
- **modelParams** -- SPICE Level 3 parameters: VTO, KP, LAMBDA, RD, RS, CGS, CGD, CDS, IS, N
- **curves** -- R_DS(on) vs T_j, R_DS(on) vs I_D, C_iss/C_oss/C_rss vs V_DS, gate charge curve, body diode V_F, SOA, thermal impedance

### Diode (Rectifier, Schottky, SiC Schottky, Fast/Ultrafast, Zener, TVS, ESD)

- **electrical** -- V_RRM, I_F(AV), V_F, I_FSM, t_rr, Q_rr, C_j, plus Zener fields (V_BR = V_Z, I_ZT, Z_ZT) and TVS/ESD fields (V_RWM, V_C, I_PP, P_PP, IEC 61000-4-2 contact/air ratings)
- **modelParams** -- SPICE parameters: IS, N, RS, CJ0, VJ, M, TT, BV, IBV
- **curves** -- V_F vs I_F, V_F vs T_j, I_R vs V_R, C_j vs V_R, thermal impedance, SOA

### IGBT

- **electrical** -- V_CE, V_CE(sat), I_C, E_on, E_off, Q_g, V_GE(th), C_ies, short-circuit time
- **modelParams** -- SPICE parameters: VTO, KP, EON, EOFF
- **curves** -- V_CE(sat) vs I_C, E_on vs I_C, E_off vs I_C, thermal impedance, SOA

### BJT

- **electrical** -- V_CEO, V_CBO, I_C, h_FE, V_CE(sat), f_T, P_D, voltage noise density e_n (+ the frequency and collector current it is specified at; the AAS field names)
- **biasResistors** (inside `electrical`) -- resistor-equipped ("pre-biased", "digital", BRT/RET) transistors: R1, R2 and their ratio as printed with its direction (`R2/R1` | `R1/R2`). Its presence is the only pre-biased marker; beside it, V_I(on)/V_I(off) as a distribution with their test V_CE/I_C, the input voltage limits and I_O (only where printed below I_C). Per die on a multi-die part, never in a dual's package block
- **dies** -- duals, complementary pairs, matched pairs/quads and current mirrors: one entry per die, each `{name, role, pins, subType, electrical, thermal}` with the full BJT electrical block (I_C stays required per die: BJT duals print it per transistor). Mutually exclusive with the package-level `electrical`, and required (as on the MOSFET) when `part.dieConfiguration` is `dual`/`complementary`/`array`
- **matching** -- only beside `dies`: |ΔV_BE| (V_OS), its drift, Δh_FE/h_FE, I_OS, mirror-ratio error, each as a `dimensionWithTolerance` (typical + guaranteed) with its test I_C / V_CB / T_A
- **packagePowerDissipation** -- only beside `dies`: the package total P_tot; each die keeps its per-transistor P_D
- No modelParams or curves sections defined (BJTs are rarely used in new power designs)

### Thyristor (SCR, triac, sidac, diac, thyristor surge protector)

- **part.subType** -- `scr` / `triac` / `sidac` / `diac` / `surgeProtector` (a part sold as a protector is a `surgeProtector` even when its silicon is a sidac). Thyristor modules and press-pack discs are not this file
- **electrical** -- V_DRM, V_RRM, conduction direction, I_T(RMS) / I_T(AV) + the case/ambient/lead temperature they are rated at, I_TSM as an array `{current, duration, shape: halfSine|fullSine}`, I^2t + duration, di/dt, dV/dt (gate open) + T_j, I_GT, V_GT, I_L, I_H, gate ratings, V_T + current, off-state leakage per condition, t_gt, t_q, isolated-tab V_isol / C_isol; triac only: per-quadrant gate figures (Q1..Q4), dI_com/dt, dV_com/dt; breakover devices: V_(BO) + ramp, impulse V_(BO) + dv/dt and di/dt, I_(BO), breakback; protectors: `peakPulseCurrents[]` `{current, waveform}` (one per printed impulse, waveform required, PEAS `surgeWaveform`), C_off per bias. A/us is stored as A/s
- **headline ratings per member** -- scr: V_DRM + an on-state current; triac: V_DRM + I_T(RMS); sidac/diac: V_(BO); surgeProtector: V_DRM + V_(BO) + peakPulseCurrents
- **dies** -- multi-line protectors: required once `part.dieConfiguration` is `dual`/`array`, mutually exclusive with the package `electrical`
- Pinout: triac MT1/MT2 use the PEAS pin functions `mainTerminal1` / `mainTerminal2`

### JFET (n- or p-channel; Si, SiC)

- **electrical** -- V_DS and/or V_GD (one is required), V_GS max, I_GF max, I_D max, I_DSS + V_DS, V_GS(off) signed as printed + its I_D and V_DS, transconductance per bias (`{transconductance, drainCurrent, gateSourceVoltage, drainSourceVoltage}`), r_DS(on), I_GSS + voltage, C_iss/C_rss/C_oss, Q_g (power JFETs), P_D, e_n and i_n with their conditions (mosfet and AAS/bjt field names)
- **dies + matching** -- duals (LSK389, U401-U406): per-die blocks plus V_GS / I_DSS / g_fs / I_G matching, the BJT pattern
- SiC cascodes (UJ3C/UJ4C/UF3C) are normally-off and stay `mosfet`; normally-on SiC JFETs (UJ3N) are `jfet` with technology `SiC`

### Optocoupler

- **part.subType** -- the output stage: `phototransistor`, `photodarlington`, `logicOutput`, `gateDriver` (optical gate-drive couplers such as TLP250 / HCPL-3120), `photoThyristor`, `photovoltaic`, `linear`. PhotoMOS / photorelays / SSRs are EMAS relays; optical isolation amplifiers are CTAS
- **electrical** (per channel; `numberOfChannels` for multi-channel parts) -- LED input (I_F, V_R, I_FSM + duration, P_diss, V_F + current, threshold current), transistor output (V_CEO, V_ECO, I_C, I_CM, I_CEO, V_CE(sat), **CTR as a fraction**, 100 % = 1.0), thyristor output (V_DRM, zero crossing), gate-driver / logic output (I_OPK, V_CC max, t_PHL, t_PLH, data rate), switching times + test load, cut-off frequency
- **isolation** (required, with V_ISO required) -- the shared PEAS `isolationRating` (the CTAS key names: withstandVoltageRms + duration, workingVoltage, transientVoltage, barrierCapacitance, cmti, creepage, clearance, ...)

### Power Module (Si IGBT, Si/SiC MOSFET, GaN HEMT dies)

- **electrical** -- `topology` (halfBridge, fullBridge, sixpack, boost, buck, chopper, singleSwitch, dualCommonSource, dualIndependent, asymmetricBridge, sixpackWithBrake, pim, threeLevel — derived from the Digi-Key IGBT-module Configuration filter + the Vincotech topology catalog), `switchTechnology` (siliconIgbt / siliconMosfet / sicMosfet / ganHemt), `numberOfSwitches`, per-switch ratings **reusing the discrete shapes by `$ref`** (`switch` is `mosfet.json`'s or `igbt.json`'s electrical block, pinned by switchTechnology), separate co-pack `diode` ratings (`diode.json`'s electrical block), loop-measured `switchingEnergy` (E_on/E_off + test conditions), baseplate `isolationVoltage`, integrated NTC (`ntcIntegrated`, R25, B-value)
- **mechanical** -- adds `terminalStyle` (screw / pressFit / solderPin / spring / busbar)
- **curves** -- R_DS(on) vs T_j, V_CE(sat) vs I_C, E_on/E_off vs I, diode V_F, thermal impedance, SOA
- No modelParams section (a single .model card cannot describe a multi-die module)

---

## SPICE Model Parameters

MOSFETs, diodes, and IGBTs have a dedicated `modelParams` section containing the parameters needed to build a SPICE simulation model:

```json
"modelParams": {
    "level": 3,
    "vto": 3.0,
    "kp": 350,
    "lambda": 0.01,
    "rd": 0.0008,
    "rs": 0.0008,
    "cgs": 8.5e-9,
    "cgd": 0.098e-9,
    "cds": 2.7e-9,
    "is": 1e-12,
    "n": 1.5
}
```

These values can be used directly in ngspice `.MODEL` statements or other SPICE simulators.

Separately, every device body (all four types) accepts a top-level `spiceModel` — a structured `.model` card (`modelName`, `modelType`, `parameters`) that serves as the canonical home for parts whose only source is a simulation model rather than a datasheet.

---

## Characteristic Curves

Curves are stored as paired arrays of X and Y data points, digitized from datasheet graphs:

```json
"curves": {
    "rdsOnVsTj": {
        "xData": [-40, 25, 75, 125, 150, 175],
        "yData": [0.0012, 0.0017, 0.0024, 0.0032, 0.0037, 0.0043]
    },
    "cossVsVds": {
        "xData": [1, 5, 10, 25, 50, 80, 100],
        "yData": [40e-9, 10e-9, 5.5e-9, 2.8e-9, 1.5e-9, 0.9e-9, 0.7e-9]
    }
}
```

This format enables loss calculations at arbitrary operating points via interpolation, without requiring access to the original datasheet PDF.

---

## Thermal Model

The `thermal` section is shared across all device types and includes:

- **Static thermal resistances**: R_th(j-c), R_th(j-a), R_th(c-s) in K/W
- **Junction temperature limits**: T_j min and max in Celsius
- **Foster RC network**: An array of {resistance, timeConstant} pairs for transient thermal impedance modeling

```json
"thermal": {
    "thermalResistanceJunctionCase": 0.7,
    "thermalResistanceJunctionAmbient": 62,
    "junctionTemperatureMax": 175,
    "junctionTemperatureMin": -55,
    "fosterNetwork": [
        { "resistance": 0.1, "timeConstant": 0.001 },
        { "resistance": 0.3, "timeConstant": 0.01 },
        { "resistance": 0.3, "timeConstant": 0.1 }
    ]
}
```

The Foster network allows accurate transient thermal simulation -- essential for pulsed load applications and SOA analysis.

---

## Schema Structure

```
SAS/
+-- schemas/
|   +-- SAS.json              Top-level: inputs + (one of mosfet/diode/igbt/bjt/thyristor/jfet/optocoupler/module) + outputs
|   +-- mosfet.json           MOSFET device data
|   +-- diode.json            Diode device data (per-subType required-field rules)
|   +-- igbt.json             IGBT device data
|   +-- bjt.json              BJT device data
|   +-- thyristor.json        Thyristor device data (SCR, triac, sidac, diac, surge protector)
|   +-- jfet.json             JFET device data
|   +-- optocoupler.json      Optocoupler device data (isolation = PEAS isolationRating)
|   +-- module.json           Multi-die power module data (topology + per-switch $refs)
|   +-- inputs.json           Operating points + design requirements
|   +-- inputs/
|   |   +-- designRequirements.json
|   +-- outputs.json          Per-operating-point computed results
|   +-- utils.json            Shared SAS defs: part, thermal, mechanical, spiceModel
|                             (dimensionWithTolerance, curve, etc. come from PEAS utils)
|
+-- examples/
|   +-- 01_mosfet_ipb017n10n5.json   100V Si n-channel MOSFET (reference document)
|   +-- 02_diode_stps30l60ct.json    60V Si Schottky diode    (reference document)
|   +-- 03_module_ff2mr12w3m1h.json  1200V SiC half-bridge module (reference document)
|   +-- 04_mosfet_dual_iaucn04s7l025ah.json  two-die MOSFET package
|   +-- 05_tvs_ptvs1_022c_h.json     22V TVS diode, 1 kA 8/20 us, with pulse waveforms
|   +-- 06_bjt_dual_matched_ssm2212.json  dual matched NPN pair (dies[] + matching[])
|   +-- 07_bjt_prebiased_dual_pumh11.json  pre-biased NPN/NPN pair (per-die biasResistors)
|   +-- 08_thyristor_scr_bt151_500r.json   500 V / 12 A SCR
|   +-- 09_thyristor_triac_bta16_600b.json 600 V / 16 A isolated-tab 4Q triac (MT1/MT2 pinout)
|   +-- 10_thyristor_protector_tisp4350h3bj.json  bidirectional telecom surge protector, 8 impulse ratings
|   +-- 11_optocoupler_vo617a_3.json      phototransistor optocoupler, CTR 100..200 % bin, 5300 V RMS
|   +-- 12_jfet_jfe150.json                low-noise n-channel JFET
|
+-- src/                      C++ converter layer (semiconductor PEAS -> CIAS)
+-- tests/                    pytest schema tests + C++ converter tests
|
+-- docs/
    +-- schema.md             Detailed field-by-field schema reference
```

There is no populated `data/` directory in SAS (see
[SAS/data/ vs TAS/data/](#sasdata-vs-tasdata) above): finished parts live in
`TAS/data/`.

---

## Examples Walkthrough

### Example 1: MOSFET -- Infineon IPB017N10N5

File: `examples/01_mosfet_ipb017n10n5.json`

A 100V / 1.7 mOhm Si n-channel MOSFET in the OptiMOS 5 family, packaged in TO-263-3 (D2PAK).

Key features demonstrated:
- Complete electrical section with all MOSFET-specific fields: V_DS=100V, R_DS(on)=1.7mOhm at V_GS=10V/I_D=100A, V_GS(th) as min/nom/max, gate charge breakdown (Q_g, Q_gs, Q_gd), capacitances at specified V_DS, body diode specs, figure of merit
- SPICE Level 3 model parameters ready for simulation
- Two characteristic curves: R_DS(on) vs T_j and C_oss vs V_DS
- Thermal data: R_th(j-c)=0.7 K/W, T_j range -55 to 175C
- Mechanical dimensions as `dimensionWithTolerance` objects in metres, `assemblyType: "smt"`
- Distributor info with Digi-Key stock, `{value, currency}` pricing, MOQ, and packaging (commercial data lives per-distributor -- there is no `business` section)
- A full `inputs` block: one operating point (drain port, rectangular waveforms) plus seed-friendly `designRequirements` (`deviceType: "mosfet"`, optional rated fields)

### Example 2: Diode -- ST STPS30L60CT

File: `examples/02_diode_stps30l60ct.json`

A 60V / 30A Si Schottky diode in TO-220AB package.

Key features demonstrated:
- Diode-specific electrical section: V_RRM=60V, I_F(AV)=30A, V_F=0.42V at I_F=15A, surge current, junction capacitance (`subType: "schottky"` puts it in the rectifier family, so V_RRM/V_F/I_F are the required trio)
- SPICE diode model parameters: IS, N, RS, CJ0, VJ, M, BV
- Two characteristic curves: V_F vs I_F and C_j vs V_R
- Through-hole assembly type (`assemblyType: "tht"`)

### Example 3: Power Module -- Infineon FF2MR12W3M1H_B11

File: `examples/03_module_ff2mr12w3m1h.json`

A 1200V / 1.44 mOhm CoolSiC MOSFET half-bridge in the EasyDUAL 3B (EasyPACK) housing with
PressFIT terminals and an integrated NTC.

Key features demonstrated:
- `topology: "halfBridge"`, `switchTechnology: "sicMosfet"`, `numberOfSwitches: 2`
- The `switch` block reuses the **mosfet electrical shape by $ref**: V_DS=1200V,
  R_DS(on)=1.44mOhm at V_GS=18V/I_D=400A, V_GS(th) as min/nom/max, capacitances at 800V,
  switching times, body diode specs
- Module-level data a discrete part does not have: `switchingEnergy` (E_on=17.7mJ,
  E_off=2.83mJ at 600V/400A, measured in the module's own commutation loop),
  `isolationVoltage: 3000` (V RMS), `ntcIntegrated: true` with R25=5kOhm and B25/100=3433K
- Baseplate-less module thermal: the datasheet's R_th(j-s)=0.128 K/W per switch stored in
  `thermalResistanceJunctionCase`
- `terminalStyle: "pressFit"` in the module-specific mechanical section
- A `module` designRequirements branch: `moduleTopology`, `allowedSwitchTechnologies`,
  `ratedBlockingVoltage`, `minimumIsolationVoltage`, `requireIntegratedNtc`

### Example 4: Multi-die MOSFET -- Infineon IAUCN04S7L025AH

File: `examples/04_mosfet_dual_iaucn04s7l025ah.json`

An asymmetric 40 V half-bridge: two N-channel OptiMOS 7 die, M1 and M2, in one
PG-TDSON-8 package. The datasheet gives every static, dynamic and thermal row in
separate M1 and M2 columns.

Key features demonstrated:
- `part.dieConfiguration: "dual"` and `part.internalConnection: "halfBridge"`
- **No package-level `electrical`**: the two die differ (2.56 mOhm / 100 A versus
  5.04 mOhm / 65 A), so there is no single R_DS(on) to record as the part's -- and
  the schema gives it nowhere to go
- `dies[]` entries named `M1` / `M2` exactly as the datasheet names them, each with its
  own complete electrical block and its own `thermal` (R_th(j-c) 2 versus 3.7 K/W)
- `dies[].pins` binding each die to `mechanical.pinout`; pins 2 and 3 appear in BOTH
  die because the datasheet bonds Source M1 to Drain M2 -- that shared pair is the
  switching node
- A bare part record (device field only, no `inputs`/`outputs`), which the top-level
  `anyOf` allows

### Example 6: Dual matched NPN pair -- Analog Devices SSM2212

File: `examples/06_bjt_dual_matched_ssm2212.json`

An audio dual matched NPN transistor in SOIC-8, sold for its matching spec.

Key features demonstrated:
- `part.dieConfiguration: "dual"` and **no package-level `electrical`**: two `dies[]`
  named `Channel 1` / `Channel 2`, the datasheet's own words for C1/B1/E1 and C2/B2/E2
- Each die states its own V_CEO = 40 V, I_C = 20 mA, h_FE {min 300, typ 605} and
  e_n = 0.85 nV/sqrt(Hz) at 1 kHz and I_C = 1 mA (`voltageNoiseDensity*`)
- `matching[]`: V_OS {typ 10 uV, max 200 uV}, its drift, Delta h_FE {0.5 %, 5 %} and
  I_OS max 6.2 nA, each with the test conditions the datasheet prints

### Example 7: Resistor-equipped (pre-biased) NPN/NPN pair -- Nexperia PUMH11

File: `examples/07_bjt_prebiased_dual_pumh11.json`

A 50 V, 100 mA double resistor-equipped transistor (R1 = R2 = 10 kOhm) in TSSOP6, every
value from the 15 July 2026 product data sheet.

Key features demonstrated:
- `electrical.biasResistors` in each die: R1 {7, 10, 13} kOhm, R2 nominal 10 kOhm (the
  title), and the ratio stored as printed, `R2/R1` {0.8, 1, 1.2}
- V_I(off) printed "typ 1.1, Max 0.8" -> `inputOffVoltage {minimum 0.8, nominal 1.1}`;
  V_I(on) printed "Min 2.5, typ 1.8" -> `inputOnVoltage {nominal 1.8, maximum 2.5}`: the
  guarantee column is moved to the end of the distribution, no arithmetic
- I_O 100 mA is the part's only current rating, so it is `collectorCurrent` and there is
  no `outputCurrentMax`; V_I +40 / -10 V -> `inputVoltageMax` 40, `inputReverseVoltageMax` 10
- P_tot 200 mW per transistor on each die, 300 mW per device in `packagePowerDissipation`

### Examples 8-12: Thyristors, an optocoupler and a JFET

Files: `examples/08_thyristor_scr_bt151_500r.json` (WeEn BT151-500R, data sheet 22 Feb 2018),
`examples/09_thyristor_triac_bta16_600b.json` (WeEn BTA16-600B, Rev.02 30 May 2023),
`examples/10_thyristor_protector_tisp4350h3bj.json` (Bourns TISP4350H3BJ, rev. Mar 2021),
`examples/11_optocoupler_vo617a_3.json` (Vishay VO617A-3, doc 83430 Rev 2.8) and
`examples/12_jfet_jfe150.json` (TI JFE150, SLPS732B). Every value is read from the cited
datasheet; each record carries its `provenance`.

Key features demonstrated:
- BT151: I_TSM printed twice (120 A / 10 ms, 132 A / 8.3 ms half sine) as two
  `surgeOnStateCurrent` entries; dV/dt with the gate open only (the R_GK = 100 Ohm figure is left out);
  leakage at 125 C as an `offStateCurrent` entry
- BTA16: per-quadrant I_GT / I_L in `quadrantRatings` (Q1..Q4), dI_com/dt, the isolated tab
  (V_isol 2500 V RMS, C_isol 10 pF) and an MT1/MT2/G pinout; R_th(j-h) is not recorded (it is
  junction-to-heatsink, not junction-to-case)
- TISP4350H3BJ: eight impulse ratings in `peakPulseCurrents[]`, including 5/310, 5/200 and 0.2/310,
  and C_off at -2 V and -50 V
- VO617A-3: the 100..200 % CTR bin stored as `{minimum 1.0, maximum 2.0}`; the isolation block maps
  V_ISO 5300 V RMS / 60 s, V_IORM 890 V and V_IOTM 8000 V with no new key
- JFE150: V_GS(off) signed as printed (-1.5..-0.9 V), g_fs at V_GS = 0 and g_m at 2 mA as two
  `transconductance` entries, e_n with its frequency and drain current

---

## Quick Reference: Fields by Device Type

### Shared Sections (all device types)

| Section | Key Fields |
|---------|------------|
| **part** | partNumber, technology, subType (per-device closed enum), case, package, qualification, dieConfiguration (`single`/`dual`/`complementary`/`array`), internalConnection (mosfet/igbt `independent`/`commonDrain`/`commonSource`/`halfBridge`; diode `commonCathode`/`commonAnode`/`series`; bjt `commonEmitter`/`commonBase`/`commonCollector`/`currentMirror`) |
| **thermal** | R_th(j-c), R_th(j-a), R_th(c-s), T_j min/max, fosterNetwork |
| **mechanical** | assemblyType (PEAS connectionType: smt/tht/chassis/...), case, length, width, height, weight |
| **provenance** | data-source trail: source, sourceName, sourceUrl, retrievedDate, fields |
| **distributorsInfo** | per-distributor commercial data: cost {value, currency}, stock, packaging, vpe, moq, leadTime |
| **substitutesInfo** | replacement parts (PEAS `substituteInfo`): partNumber, manufacturer, type (`successor` = this part is superseded by that one, one hop, manufacturer-stated), notes, source; evidence in `provenance` with `fields: ["substitutesInfo"]` |

### Device-Specific Sections

| Field | MOSFET | Diode | IGBT | BJT |
|-------|--------|-------|------|-----|
| **Voltage rating** | drainSourceVoltage | reverseVoltage | collectorEmitterVoltage | collectorEmitterVoltage |
| **Current rating** | continuousDrainCurrent | forwardCurrent | continuousCollectorCurrent | collectorCurrent |
| **On-state loss param** | onResistance | forwardVoltage | collectorEmitterSaturation | saturationVoltage |
| **Gate/base threshold** | gateThresholdVoltage | -- | gateThresholdVoltage | -- |
| **Switching energy** | (from Q_g, times) | -- | turnOnEnergy, turnOffEnergy | -- |
| **Capacitances** | C_iss, C_oss, C_rss | C_j | C_ies | -- |
| **Gate charge** | Q_g, Q_gs, Q_gd | -- | Q_g | -- |
| **Reverse recovery** | t_rr, Q_rr (body diode) | t_rr, Q_rr | -- | -- |
| **Current gain** | -- | -- | -- | h_FE (dcCurrentGain) |
| **SPICE params** | modelParams | modelParams | modelParams | -- |
| **Curves** | curves | curves | curves | -- |

### Required Fields by Device Type

| Device Type | Required Electrical Fields |
|-------------|--------------------------|
| **mosfet** | drainSourceVoltage, onResistance, continuousDrainCurrent, gateThresholdVoltage, totalGateCharge -- in `electrical` for a single-die part. A `dies[]` entry requires the same set **minus continuousDrainCurrent** (a package rating many vendors publish only per package), plus `name` and `subType` |
| **diode** | depends on `part.subType`: rectifier family (`rectifier`/`schottky`/`sicSchottky`/`fastRecovery`/`ultrafast`/`switching`/`pin`, or no subType) -> reverseVoltage, forwardVoltage, forwardCurrent; zener -> breakdownVoltage, powerDissipation; tvs -> standoffVoltage, clampingVoltage + a pulse rating; esd -> standoffVoltage + a pulse rating. Each pulse rating may state its waveform (`peakPulseCurrentWaveform`, `peakPulsePowerWaveform`, `clampingWaveform` + `clampingCurrent`; PEAS `surgeWaveform` enum), and a waveform requires its value |
| **igbt** | collectorEmitterVoltage, collectorEmitterSaturation, continuousCollectorCurrent |
| **bjt** | collectorEmitterVoltage, collectorCurrent -- in `electrical` for a single-die part, and in every `dies[]` entry (plus `name` and `subType`) for a multi-die one |
| **thyristor** | depends on `part.subType`: scr -> repetitivePeakOffStateVoltage + rmsOnStateCurrent or averageOnStateCurrent; triac -> repetitivePeakOffStateVoltage, rmsOnStateCurrent; sidac/diac -> breakoverVoltage; surgeProtector -> repetitivePeakOffStateVoltage, breakoverVoltage, peakPulseCurrents (each with its waveform) |
| **jfet** | drainSourceVoltage or gateDrainVoltageMax |
| **optocoupler** | `electrical` itself, with isolation.withstandVoltageRms (V_ISO); phototransistor/photodarlington also collectorEmitterVoltage, currentTransferRatio |
| **module** | topology, switchTechnology, numberOfSwitches, switch (whose own required set is the mosfet or igbt one above, per switchTechnology) |

---

## Data Files

SAS ships **no part data**: the `data/` directory is empty by design. It is reserved for
manufacturing building blocks (semiconductor dies and packages), none of which have been
catalogued yet. All finished, orderable semiconductors live in `TAS/data/`
(`mosfets.ndjson`, `diodes.ndjson`, `igbts.ndjson`, `bjts.ndjson`, `thyristors.ndjson`,
`jfets.ndjson`, `optocouplers.ndjson`) as PEAS-wrapped
`{"semiconductor": {...}}` records validated against these SAS schemas.

---

## Detailed Documentation

See [docs/schema.md](docs/schema.md) for the complete field-by-field schema reference with types, units, enum values, and required/optional status.

---

## License

This project is licensed under the MIT License -- see [LICENSE](LICENSE).

---

<p align="center">
  Part of the <a href="https://github.com/OpenConverters">OpenConverters</a> project
</p>
