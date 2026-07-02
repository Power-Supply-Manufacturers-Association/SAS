# SAS Schema Reference

Complete field-by-field documentation for the Semiconductor Agnostic Structure schema.

**Schema version**: JSON Schema 2020-12
**Base URI**: `https://psma.com/sas/`

SAS builds on PEAS: shared primitives (`dimensionWithTolerance`, `curve`, `manufacturerInfo`,
`distributorInfo`, `provenance`, the `datasheetInfo*` mixins, `outputBase`) are `$ref`ed from
`https://psma.com/peas/...`, so validating an SAS document requires the PEAS repo checked out
alongside SAS. The reference documents for this schema are
[`examples/01_mosfet_ipb017n10n5.json`](../examples/01_mosfet_ipb017n10n5.json) and
[`examples/02_diode_stps30l60ct.json`](../examples/02_diode_stps30l60ct.json).

---

## Table of Contents

- [Top-Level Structure (SAS.json)](#top-level-structure)
- [Device Documents (mosfet.json, diode.json, igbt.json, bjt.json)](#device-documents)
  - [manufacturerInfo](#manufacturerinfo)
  - [distributorsInfo](#distributorsinfo)
  - [datasheetInfo](#datasheetinfo)
- [Shared Sections (utils.json)](#shared-sections)
  - [part](#part)
  - [thermal](#thermal)
  - [mechanical](#mechanical)
  - [spiceModel (device-body)](#spicemodel-device-body)
- [MOSFET Sections](#mosfet-sections)
  - [mosfetElectrical](#mosfetelectrical)
  - [mosfetModelParams](#mosfetmodelparams)
  - [mosfetCurves](#mosfetcurves)
- [Diode Sections](#diode-sections)
  - [diodeElectrical](#diodeelectrical)
  - [Per-subType required fields](#per-subtype-required-fields)
  - [diodeModelParams](#diodemodelparams)
  - [diodeCurves](#diodecurves)
- [IGBT Sections](#igbt-sections)
  - [igbtElectrical](#igbtelectrical)
  - [igbtModelParams](#igbtmodelparams)
  - [igbtCurves](#igbtcurves)
- [BJT Sections](#bjt-sections)
  - [bjtElectrical](#bjtelectrical)
- [Inputs (inputs.json)](#inputs)
  - [designRequirements](#designrequirements)
- [Outputs (outputs.json)](#outputs)
- [PEAS Utility Types](#peas-utility-types)
  - [dimensionWithTolerance](#dimensionwithtolerance)
  - [curve](#curve)
- [Provenance (data-source trail)](#provenance-data-source-trail)
- [Enum Reference](#enum-reference)

---

## Top-Level Structure

**File**: `schemas/SAS.json`

An SAS document carries `inputs`, **exactly one** of `{mosfet, diode, igbt, bjt}`, and
`outputs`. **The field name is the discriminator** — there is no `deviceType` property
anywhere in the component data, and a `deviceType` key inside `part` is rejected
(`additionalProperties: false`).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inputs` | [inputs](#inputs) | See below | Design requirements and operating points for this semiconductor |
| `mosfet` | [mosfet.json](#device-documents) | oneOf | MOSFET (Si, SiC, GaN, GaAs) |
| `diode` | [diode.json](#device-documents) | oneOf | Diode (Schottky, ultrafast, SiC Schottky, Zener, TVS, ESD) |
| `igbt` | [igbt.json](#device-documents) | oneOf | IGBT |
| `bjt` | [bjt.json](#device-documents) | oneOf | BJT (npn or pnp) |
| `outputs` | array of [outputs](#outputs) | See below | Computed results; `outputs[i]` aligns positionally with `inputs.operatingPoints[i]` |

Structural rules:

- `oneOf`: exactly one of `mosfet` / `diode` / `igbt` / `bjt` must be present.
- `anyOf`: either **both** `inputs` and `outputs` are present (a full design document), or
  the document has **only** the device field (`maxProperties: 1` — a bare part record).
- `additionalProperties: false` — no extra fields allowed at the top level.

---

## Device Documents

**Files**: `schemas/mosfet.json`, `schemas/diode.json`, `schemas/igbt.json`, `schemas/bjt.json`

All four device files share the same outer shape:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturerInfo` | [manufacturerInfo](#manufacturerinfo) | anyOf | Manufacturer data, including the nested `datasheetInfo` |
| `distributorsInfo` | array of [distributorInfo](#distributorsinfo) | No | Where to buy this component |
| `spiceModel` | [spiceModel](#spicemodel-device-body) | anyOf | Device-body SPICE `.model` card for a simulation-sourced part (no datasheet) |

`anyOf`: the device body must contain `manufacturerInfo`, **or** `spiceModel`, **or** be an
empty object (`maxProperties: 0`). The device-body `spiceModel` is the canonical home for a
part whose only source is a simulation model — it does not require the
`manufacturerInfo`/`datasheetInfo` chain.

`additionalProperties: false` in every device file.

### manufacturerInfo

Each device file builds its own closed `manufacturerInfo` by `$ref`-ing the field definitions
of PEAS `utils.json#/$defs/manufacturerInfo`:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | Manufacturer name (e.g., "Infineon", "STMicroelectronics") |
| `reference` | string | No | Manufacturer part number |
| `status` | string (enum) | No | `"production"`, `"prototype"`, `"nrnd"`, `"obsolete"`, `"preview"` |
| `description` | string | No | Description of the part per its manufacturer |
| `orderCode` | string | No | Manufacturer order code |
| `datasheetUrl` | string (URI) | No | URL to the datasheet PDF |
| `spiceModel` | object | No | Free-form SPICE simulation model attached by the manufacturer (distinct from the structured device-body [spiceModel](#spicemodel-device-body)) |
| `family` | string | No | Manufacturer product family / product line (e.g. "CoolMOS C7") |
| `datasheetInfo` | [datasheetInfo](#datasheetinfo) | **Yes** | All information extracted from the datasheet |

`additionalProperties: false`

### distributorsInfo

Array of PEAS `utils.json#/$defs/distributorInfo` (closed object; only `name` required).
Key fields:

| Field | Type | Description |
|-------|------|-------------|
| `name` | string (**required**) | Distributor name (e.g., "Digi-Key", "Mouser") |
| `reference` | string or null | Distributor part number |
| `link` | string or null (URI) | Product page URL |
| `cost` | currencyAmount | Unit cost as `{value, currency}` — not a bare number |
| `stock` | integer or null | Available stock |
| `packaging` | string or null | Packaging format (e.g. "Tape and Reel", "Tube") |
| `vpe` | integer or null | Units per package / reel |
| `moq` | integer or null | Minimum order quantity |
| `leadTime` | number or null | Lead time in weeks |

Plus `country`, `distributedArea`, `phone`, `email`, `quantity`, `updatedAt`, `internal`,
`internalNote` — see PEAS `utils.json` for the full definition. Commercial data (cost, MOQ,
packaging) lives **here**, per distributor; there is no `business` section in `datasheetInfo`.

### datasheetInfo

Each device file defines its own closed `datasheetInfo` (there is no shared
device-discriminating `oneOf` — the file it lives in already fixes the device type):

| Field | Type | Required | mosfet | diode | igbt | bjt |
|-------|------|----------|--------|-------|------|-----|
| `part` | [part](#part) | **Yes** | yes | yes | yes | yes |
| `electrical` | per-device electrical | **Yes** | yes | yes | yes | yes |
| `thermal` | [thermal](#thermal) | No | yes | yes | yes | yes |
| `mechanical` | [mechanical](#mechanical) | No | yes | yes | yes | yes |
| `modelParams` | per-device modelParams | No | yes | yes | yes | -- |
| `curves` | per-device curves | No | yes | yes | yes | -- |
| `provenance` | [provenance](#provenance-data-source-trail) | No | yes | yes | yes | yes |

`additionalProperties: false`. The diode `datasheetInfo` additionally carries the
[per-subType conditional required rules](#per-subtype-required-fields).

---

## Shared Sections

**File**: `schemas/utils.json` (SAS-local `$defs`, built on PEAS mixins)

### part

`utils.json#/$defs/part` — extends PEAS `datasheetInfoPartBase` (which contributes
`partNumber`, `series`, `case`, `description`) with semiconductor-specific fields. The
extension layer is closed, so only the fields below are legal. **There is no `deviceType`
field** — the device type is the top-level field name.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `partNumber` | string | **Yes** | Manufacturer part number (e.g., "IPB017N10N5") |
| `series` | string or null | No | Product series (e.g., "OptiMOS 5"); null where the part has no distinct series |
| `case` | string | No | Package / case code (e.g., "TO-220", "SOT-23", "TO-263-3 (D2PAK)") |
| `description` | string | No | Free-text part description as on the datasheet |
| `technology` | string (enum) | **Yes** | `"Si"`, `"SiC"`, `"GaN"`, `"GaAs"`, `"Ge"` |
| `subType` | string (enum) | No | Per-device subtype — a **closed enum narrowed by each device file**, see [subType values](#subtype) |
| `package` | string | No | Manufacturer's exact package designation (e.g. "PG-TDSON-8"); complements the generic `case` code |
| `qualification` | string | No | Qualification grade (e.g. "Industrial", "Automotive (AEC-Q101)") |
| `matchcodeDescription` | string | No | Additional description or matchcode |

Each device file's `datasheetInfo.part` narrows `subType` to a closed enum via `allOf`:

| Device file | Legal `subType` values |
|-------------|------------------------|
| `mosfet.json` | `nChannel`, `pChannel`, `powerBlock` |
| `diode.json` | `rectifier`, `schottky`, `sicSchottky`, `fastRecovery`, `ultrafast`, `zener`, `tvs`, `esd` |
| `igbt.json` | `nChannel` |
| `bjt.json` | `npn`, `pnp` |

### thermal

`utils.json#/$defs/thermal` — a direct `$ref` to PEAS
`utils.json#/$defs/datasheetInfoThermalSemiconductor`. Closed; no required fields.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `thermalResistanceJunctionCase` | number | No | K/W | R_th(j-c) -- junction to case |
| `thermalResistanceJunctionAmbient` | number | No | K/W | R_th(j-a) -- junction to ambient |
| `thermalResistanceCaseSink` | number | No | K/W | R_th(c-s) -- case to heatsink |
| `junctionTemperatureMax` | number | No | Celsius | Maximum operating junction temperature |
| `junctionTemperatureMin` | number | No | Celsius | Minimum operating junction temperature |
| `fosterNetwork` | array (minItems 1) | No | -- | Foster RC ladder for transient thermal impedance, ordered from junction outward |

#### fosterNetwork items

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `resistance` | number | **Yes** | K/W | Thermal resistance of this RC cell |
| `timeConstant` | number | **Yes** | seconds | Time constant of this RC cell |

### mechanical

`utils.json#/$defs/mechanical` — extends PEAS `datasheetInfoMechanical` with a package
`case` field. The extension layer is closed. No required fields.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `length` | [dimensionWithTolerance](#dimensionwithtolerance) | No | metres | Body length |
| `width` | [dimensionWithTolerance](#dimensionwithtolerance) | No | metres | Body width |
| `height` | [dimensionWithTolerance](#dimensionwithtolerance) | No | metres | Body height |
| `diameter` | [dimensionWithTolerance](#dimensionwithtolerance) | No | metres | Body diameter (cylindrical parts) |
| `weight` | number | No | kg | Component weight |
| `shapeType` | string | No | -- | Package / body shape (e.g. "radial", "axial", "SMD") |
| `assemblyType` | string (enum) | No | -- | PCB mounting type — PEAS [connectionType](#connectiontype-assemblytype): `pin`, `screw`, `smt`, `flyingLead`, `tht`, `pcbPad`, `chassis` |
| `case` | string | No | -- | Package name (TO-220, SOT-23, etc.) — mirrors `part.case` for convenience |

Note the dimensions are `dimensionWithTolerance` objects (e.g. `{"nominal": 0.0103}`), not
bare numbers, and `assemblyType` uses the lowercase PEAS `connectionType` enum (there are no
`"SMT"`/`"THT"`/`"Chassis"` values).

### spiceModel (device-body)

`utils.json#/$defs/spiceModel` — the device's SPICE `.model` card as structured data, for
simulator-agnostic round-trip (ngspice and LTspice consume `.model` cards identically).
Referenced from each device file's top-level `spiceModel` property. Closed object.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `modelName` | string (minLength 1) | No | Model name exactly as in the `.model` card (e.g. "1N4148") |
| `modelType` | string (minLength 1) | **Yes** | SPICE model type keyword (e.g. `D`, `NPN`, `PNP`, `VDMOS`, `NMOS`, `PMOS`, `NIGBT`) |
| `parameters` | object | No | `.model` parameters as name → value (number, string, or boolean), SI-resolved. Empty object when the card carries only type defaults |

Nothing is fabricated: a bare card such as `.model Red D` yields `modelType: "D"` and an
empty `parameters` object.

---

## MOSFET Sections

**File**: `schemas/mosfet.json` (`$defs`)

### mosfetElectrical

Electrical characteristics specific to MOSFETs. Closed object.

**Required**: `drainSourceVoltage`, `onResistance`, `continuousDrainCurrent`,
`gateThresholdVoltage`, `totalGateCharge`.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `drainSourceVoltage` | number | **Yes** | V | V_DS max -- maximum drain-source voltage |
| `gateSourceVoltageMax` | number | No | V | V_GS max -- maximum gate-source voltage |
| `continuousDrainCurrent` | number | **Yes** | A | I_D at T_c=25C |
| `continuousDrainCurrentAt100C` | number | No | A | I_D at T_c=100C |
| `pulsedDrainCurrent` | number | No | A | I_DM -- pulsed drain current |
| `powerDissipation` | number | No | W | P_D max at T_c=25C |
| `avalancheEnergy` | number | No | J | E_AS -- single-pulse avalanche energy |
| `onResistance` | number | **Yes** | Ohm | R_DS(on) -- drain-source on-resistance |
| `onResistanceVgs` | number | No | V | V_GS at which R_DS(on) is specified |
| `onResistanceId` | number | No | A | I_D at which R_DS(on) is specified |
| `gateThresholdVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | **Yes** | V | V_GS(th) with min/nom/max |
| `inputCapacitance` | number | No | F | C_iss -- input capacitance |
| `outputCapacitance` | number | No | F | C_oss -- output capacitance |
| `reverseTransferCapacitance` | number | No | F | C_rss -- reverse transfer capacitance |
| `capacitanceMeasurementVds` | number | No | V | V_DS at which capacitances are measured |
| `totalGateCharge` | number | **Yes** | C | Q_g -- total gate charge |
| `gateSourceCharge` | number | No | C | Q_gs -- gate-source charge |
| `gateDrainCharge` | number | No | C | Q_gd -- gate-drain (Miller) charge |
| `outputCharge` | number | No | C | Q_oss -- output charge |
| `turnOnDelay` | number | No | s | t_d(on) -- turn-on delay time |
| `riseTime` | number | No | s | t_r -- rise time |
| `turnOffDelay` | number | No | s | t_d(off) -- turn-off delay time |
| `fallTime` | number | No | s | t_f -- fall time |
| `bodyDiodeForwardVoltage` | number | No | V | V_SD -- body diode forward voltage |
| `bodyDiodeContinuousCurrent` | number | No | A | I_S -- body diode continuous current |
| `reverseRecoveryTime` | number | No | s | t_rr -- body diode reverse recovery time |
| `reverseRecoveryCharge` | number | No | C | Q_rr -- body diode reverse recovery charge |
| `figureOfMerit` | number | No | Ohm*C | R_DS(on) x Q_g |

### mosfetModelParams

SPICE model parameters for MOSFET simulation. Closed; no required fields.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `level` | integer | No | -- | SPICE model level (e.g., 1, 3) |
| `vto` | number | No | V | Threshold voltage |
| `kp` | number | No | A/V^2 | Transconductance parameter |
| `lambda` | number | No | 1/V | Channel-length modulation |
| `rd` | number | No | Ohm | Drain resistance |
| `rs` | number | No | Ohm | Source resistance |
| `cgs` | number | No | F | Gate-source capacitance |
| `cgd` | number | No | F | Gate-drain capacitance |
| `cds` | number | No | F | Drain-source capacitance |
| `is` | number | No | A | Body diode saturation current |
| `n` | number | No | -- | Body diode ideality factor |

### mosfetCurves

Characteristic curves digitized from MOSFET datasheets. All fields are PEAS
[curve](#curve) objects, all optional.

| Field | X-axis | Y-axis | Description |
|-------|--------|--------|-------------|
| `rdsOnVsTj` | T_j (C) | R_DS(on) (Ohm) | On-resistance vs junction temperature |
| `rdsOnVsId` | I_D (A) | R_DS(on) (Ohm) | On-resistance vs drain current |
| `cissVsVds` | V_DS (V) | C_iss (F) | Input capacitance vs drain-source voltage |
| `cossVsVds` | V_DS (V) | C_oss (F) | Output capacitance vs drain-source voltage |
| `crssVsVds` | V_DS (V) | C_rss (F) | Reverse transfer capacitance vs V_DS |
| `gateCharge` | Q_g (C) | V_GS (V) | Gate voltage vs gate charge |
| `bodyDiodeVf` | V_SD (V) | I_SD (A) | Body diode forward voltage vs current |
| `soa` | V_DS (V) | I_D (A) | Safe Operating Area boundary |
| `thermalImpedance` | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |

---

## Diode Sections

**File**: `schemas/diode.json` (`$defs`)

### diodeElectrical

Diode electrical characteristics. Closed object. The `electrical` definition itself has
**no static required list** — which fields are required depends on `part.subType` and is
enforced by conditionals in the diode `datasheetInfo` (next section).

| Field | Type | Unit | Description |
|-------|------|------|-------------|
| `reverseVoltage` | number | V | V_RRM -- repetitive peak reverse voltage |
| `forwardCurrent` | number | A | I_F(AV) -- average forward current |
| `surgeCurrent` | number | A | I_FSM -- non-repetitive surge current |
| `forwardVoltage` | number | V | V_F -- forward voltage drop |
| `forwardVoltageAt` | number | A | I_F at which V_F is specified |
| `reverseLeakageCurrent` | number | A | I_R -- reverse leakage current |
| `reverseRecoveryTime` | number | s | t_rr -- reverse recovery time |
| `reverseRecoveryCharge` | number | C | Q_rr -- reverse recovery charge |
| `junctionCapacitance` | number | F | C_j -- junction capacitance |
| `junctionCapacitanceVr` | number | V | V_R at which C_j is measured |
| `powerDissipation` | number | W | P_D max |
| `clampingVoltage` | number | V | V_C at I_PP -- TVS clamping voltage |
| `breakdownVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | V | V_BR for Zener/TVS/ESD. For zeners this **is** the zener voltage V_Z (min/nom/max, specified at `zenerTestCurrent`) — there is deliberately no separate `zenerVoltage` field |
| `zenerTestCurrent` | number | A | I_ZT -- test current at which V_Z (breakdownVoltage) is specified |
| `zenerImpedance` | number | Ohm | Z_ZT -- dynamic impedance at I_ZT |
| `standoffVoltage` | number | V | V_RWM -- working voltage for TVS/ESD |
| `peakPulseCurrent` | number | A | I_PP for TVS/ESD (datasheet-stated waveform, typically 8/20 us or IEC 61000-4-5) |
| `peakPulsePower` | number | W | P_PP for TVS/ESD (datasheet-stated waveform, e.g. 10/1000 us) |
| `esdVoltageContact` | number | V | IEC 61000-4-2 contact discharge rating |
| `esdVoltageAir` | number | V | IEC 61000-4-2 air discharge rating |

### Per-subType required fields

Enforced by `if`/`then`/`else` conditionals on `part.subType` inside the diode
`datasheetInfo`:

| `part.subType` | Required in `electrical` |
|----------------|--------------------------|
| `zener` | `breakdownVoltage`, `powerDissipation` |
| `esd` | `standoffVoltage`, plus at least one of `peakPulseCurrent` / `peakPulsePower` / `esdVoltageContact` |
| `tvs` | `standoffVoltage`, `clampingVoltage`, plus at least one of `peakPulseCurrent` / `peakPulsePower` |
| rectifier family (`rectifier`, `schottky`, `sicSchottky`, `fastRecovery`, `ultrafast`) — or `subType` absent | `reverseVoltage`, `forwardVoltage`, `forwardCurrent` |

TVS and ESD parts do not have a `forwardCurrent` (I_F(AV)) rating — that is a rectifier
parameter; their forward-direction capability, when published, is the surge `surgeCurrent`
(I_FSM).

### diodeModelParams

SPICE model parameters for diode simulation. Closed; no required fields.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `is` | number | No | A | Saturation current |
| `n` | number | No | -- | Ideality factor (emission coefficient) |
| `rs` | number | No | Ohm | Series resistance |
| `cj0` | number | No | F | Zero-bias junction capacitance |
| `vj` | number | No | V | Junction potential (built-in voltage) |
| `m` | number | No | -- | Grading coefficient |
| `tt` | number | No | s | Transit time |
| `bv` | number | No | V | Reverse breakdown voltage |
| `ibv` | number | No | A | Current at breakdown voltage |

### diodeCurves

All fields are PEAS [curve](#curve) objects, all optional.

| Field | X-axis | Y-axis | Description |
|-------|--------|--------|-------------|
| `forwardVoltageVsCurrent` | I_F (A) | V_F (V) | Forward voltage vs forward current |
| `forwardVoltageVsTj` | T_j (C) | V_F (V) | Forward voltage vs junction temperature |
| `reverseCurrentVsVoltage` | V_R (V) | I_R (A) | Reverse leakage vs reverse voltage |
| `capacitanceVsVoltage` | V_R (V) | C_j (F) | Junction capacitance vs reverse voltage |
| `thermalImpedance` | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |
| `soa` | V_R (V) | I_F (A) | Safe Operating Area boundary |

---

## IGBT Sections

**File**: `schemas/igbt.json` (`$defs`)

### igbtElectrical

Closed object. **Required**: `collectorEmitterVoltage`, `collectorEmitterSaturation`,
`continuousCollectorCurrent`.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `collectorEmitterVoltage` | number | **Yes** | V | V_CE max -- maximum collector-emitter voltage |
| `gateEmitterVoltageMax` | number | No | V | V_GE max -- maximum gate-emitter voltage |
| `continuousCollectorCurrent` | number | **Yes** | A | I_C at T_c=25C |
| `collectorEmitterSaturation` | number | **Yes** | V | V_CE(sat) -- collector-emitter saturation voltage |
| `collectorEmitterSaturationIc` | number | No | A | I_C at which V_CE(sat) is specified |
| `turnOnEnergy` | number | No | J | E_on -- turn-on switching energy |
| `turnOffEnergy` | number | No | J | E_off -- turn-off switching energy |
| `totalGateCharge` | number | No | C | Q_g -- total gate charge |
| `gateThresholdVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V | V_GE(th) with min/nom/max |
| `inputCapacitance` | number | No | F | C_ies -- input capacitance |
| `powerDissipation` | number | No | W | P_D max |
| `shortCircuitTime` | number | No | s | t_SC -- short-circuit withstand time |

### igbtModelParams

Closed; no required fields.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `vto` | number | No | V | Threshold voltage |
| `kp` | number | No | A/V^2 | Transconductance parameter |
| `eon` | number | No | J | Turn-on energy |
| `eoff` | number | No | J | Turn-off energy |

### igbtCurves

All fields are PEAS [curve](#curve) objects, all optional.

| Field | X-axis | Y-axis | Description |
|-------|--------|--------|-------------|
| `vceVsIc` | I_C (A) | V_CE(sat) (V) | Saturation voltage vs collector current |
| `eonVsIc` | I_C (A) | E_on (J) | Turn-on energy vs collector current |
| `eoffVsIc` | I_C (A) | E_off (J) | Turn-off energy vs collector current |
| `thermalImpedance` | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |
| `soa` | V_CE (V) | I_C (A) | Safe Operating Area boundary |

---

## BJT Sections

**File**: `schemas/bjt.json` (`$defs`)

### bjtElectrical

Closed object. No `modelParams` or `curves` sections are defined for BJTs.
**Required**: `collectorEmitterVoltage`, `collectorCurrent`.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `collectorEmitterVoltage` | number | **Yes** | V | V_CEO -- collector-emitter voltage (base open) |
| `collectorBaseVoltage` | number | No | V | V_CBO -- collector-base voltage (emitter open) |
| `collectorCurrent` | number | **Yes** | A | I_C max -- maximum collector current |
| `dcCurrentGain` | [dimensionWithTolerance](#dimensionwithtolerance) | No | -- | h_FE -- DC current gain (min/nom/max) |
| `saturationVoltage` | number | No | V | V_CE(sat) -- collector-emitter saturation voltage |
| `transitionFrequency` | number | No | Hz | f_T -- gain-bandwidth product |
| `powerDissipation` | number | No | W | P_D max |

---

## Inputs

**File**: `schemas/inputs.json`

Mirrors the MAS / CAS / RAS inputs structure. Closed object; **both fields required**.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `operatingPoints` | array (minItems 1) of PEAS `multiPortOperatingPoint` | **Yes** | One entry per operating point. Each has optional `name`, required `conditions` and `excitationsPerPort` (semiconductors are three- or four-terminal devices — gate/drain/source, anode/cathode, base/collector/emitter — so each port carries its own voltage/current waveforms). Defined in `https://psma.com/peas/inputs/multiPortOperatingPoint.json` |
| `designRequirements` | [designRequirements](#designrequirements) | **Yes** | The requirements the semiconductor must comply with |

### designRequirements

**File**: `schemas/inputs/designRequirements.json`

Built as `allOf` [PEAS `designRequirementsBase`, semiconductor-specific layer] with
`unevaluatedProperties: false`. **Only `deviceType` is required** — every rated/limit field
is optional, so a seed record (e.g. converted from a bare SPICE model) validates with just
`{"deviceType": "mosfet"}`. Note: `deviceType` exists **only here**, in the requirements —
it states what kind of device is being asked for and drives the per-type `oneOf` below. The
component data itself carries no `deviceType`.

Common fields (semiconductor layer + PEAS base):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `deviceType` | string (enum) | **Yes** | `"mosfet"`, `"diode"`, `"igbt"`, `"bjt"` — selects the per-type branch below |
| `maximumJunctionTemperature` | number | No | Maximum allowed junction temperature, in Celsius |
| `maximumPowerDissipation` | number (>= 0) | No | Maximum allowed continuous power dissipation, in W |
| `role` | string (enum) | No | Semiconductor role in the converter: `mainSwitch`, `synchronousRectifier`, `freewheelingDiode`, `clampDiode`, `bootstrapDiode`, `lineRectifier`, `bridgeRectifier`, `bodyDiode`, `inrushLimiter`, `esdProtection`, `tvs`, `zenerReference`, `smallSignal` |
| `allowedTechnologies` | array (enum items, minItems 1, unique) | No | Acceptable process technologies: `Si`, `SiC`, `GaN`, `GaAs`, `Ge` |
| `application` | string (enum) | No | PEAS `semiconductorApplication`: `powerSwitching`, `powerRectification`, `protection`, `signalProcessing`, `referenceClamp` |
| `subApplication` | string (enum) | No | PEAS `semiconductorSubApplication` (e.g. `highSideSwitch`, `synchronousRectifier`, `freewheelingDiode`, `tvs`, `zenerReference`, ...) |
| `name` | string | No | Label for these requirements (PEAS base) |
| `market` | enum | No | PEAS base |
| `topology` | enum | No | PEAS base |
| `operatingTemperature` | [dimensionWithTolerance](#dimensionwithtolerance) | No | Operating temperature range, Celsius (PEAS base) |
| `terminalType` | array of connectionType | No | Required terminal type(s) (PEAS base) |
| `maximumWeight` | number (>= 0) | No | Maximum weight, kg (PEAS base) |
| `maximumDimensions` | object | No | Maximum width/height/depth, metres (PEAS base) |

Per-`deviceType` optional fields (`oneOf`, discriminated by `deviceType`; every branch has
`required: []` — the rated fields are deliberately optional to stay seed-friendly):

| deviceType | Optional fields |
|------------|-----------------|
| `mosfet` | `ratedDrainSourceVoltage` (V), `ratedContinuousDrainCurrent` (A), `maximumOnResistance` (Ohm), `maximumGateCharge` (C), `maximumOutputCapacitance` (F), `maximumSwitchingLossPerCycle` (J), `maximumReverseRecoveryCharge` (C) |
| `diode` | `ratedReverseVoltage` (V), `ratedForwardCurrent` (A), `maximumForwardVoltage` (V), `maximumReverseRecoveryCharge` (C), `maximumReverseRecoveryTime` (s), `maximumReverseLeakage` (A) |
| `igbt` | `ratedCollectorEmitterVoltage` (V), `ratedCollectorCurrent` (A), `maximumSaturationVoltage` (V), `maximumSwitchingLossPerCycle` (J) |
| `bjt` | `ratedCollectorEmitterVoltage` (V), `ratedCollectorCurrent` (A), `maximumSaturationVoltage` (V), `minimumDcCurrentGain` (--) |

---

## Outputs

**File**: `schemas/outputs.json`

Outputs computed for **one operating point**; the top-level SAS document holds an **array**
of these, aligned positionally with `inputs.operatingPoints`. Closed object; every named
block is independently optional (an empty `{}` per operating point is valid). Each block is
sealed (`unevaluatedProperties: false`) and wraps the PEAS `outputBase` provenance shell, so
when a block is present it must carry `origin` and `methodUsed` plus its own required
field(s):

| Block | Required fields (besides `origin`, `methodUsed`) | Key optional fields |
|-------|--------------------------------------------------|---------------------|
| `conductionLosses` | `totalConductionLosses` (W) | `rmsCurrent`, `averageCurrent`, `onStateResistance`, `onStateVoltageDrop`, `conditions` |
| `switchingLosses` | `energyPerCycle` (J) | `energyPerTurnOn`, `energyPerTurnOff`, `averagePower`, `switchingFrequency`, `conditions` |
| `reverseRecoveryLosses` | `averagePower` (W) | `qrr`, `trr`, `energyPerEvent`, `conditions` |
| `gateDriveEnergy` | `averagePower` (W) | `totalGateCharge`, `driveVoltageSwing`, `energyPerCycle` |
| `totalPowerDissipation` | `total` (W) | `conductionShare`, `switchingShare`, `reverseRecoveryShare`, `gateDriveShare` (each 0..1) |
| `junctionTemperature` | `junctionTemperature` (Celsius) | `caseTemperature`, `ambientTemperature`, `thermalResistanceJunctionToCase`, `thermalResistanceCaseToAmbient` |
| `soaCheck` | `passes` (boolean) | `worstMargin`, `appliedTrajectory.samples[]` (`{time, voltage, current}` all required per sample), `failurePoint` (`{voltage, current, time}` all required) |
| `lifetime` | `predictedHours` ([dimensionWithTolerance](#dimensionwithtolerance)) | `thermalCycles`, `endOfLifeMode` (enum: `bondWireFatigue`, `solderFatigue`, `gateOxideWear`, `electromigration`, `thermalRunaway`, `shortCircuit`, `openCircuit`), `conditions` |
| `isolationCheck` | per PEAS `outputs/insulationCoordination.json` | Insulation coordination figures, for isolated parts |

`conditions` blocks are PEAS `outputs/measurementCondition.json` (`frequency`, `voltageRms`,
`currentRms`, `dcBias`, `temperature` — all optional).

---

## PEAS Utility Types

These live in **PEAS** `utils.json` (`https://psma.com/peas/utils.json`), not in SAS. The
SAS-local `schemas/utils.json` holds only the semiconductor-specific defs documented in
[Shared Sections](#shared-sections).

### dimensionWithTolerance

A value with tolerance bounds. At least one of `minimum` / `nominal` / `maximum` must be
present (`anyOf`). Closed object.

```json
{
    "minimum": 2.2,
    "nominal": 3.0,
    "maximum": 3.8
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `minimum` | number | At least one of the three | Minimum value |
| `nominal` | number | At least one of the three | Nominal (typical) value |
| `maximum` | number | At least one of the three | Maximum value |
| `excludeMinimum` | boolean | No | True if the minimum is excluded from the range |
| `excludeMaximum` | boolean | No | True if the maximum is excluded from the range |
| `unit` | string | No | Optional SI unit string; when absent the unit is implied by the field name |

**Used in SAS for**: `gateThresholdVoltage` (MOSFET, IGBT), `breakdownVoltage` (diode),
`dcCurrentGain` (BJT), all `mechanical` body dimensions, `operatingTemperature`
(designRequirements), `predictedHours` (lifetime output).

### curve

X-Y data points representing a characteristic curve digitized from a datasheet. Closed
object; all fields optional.

```json
{
    "xData": [1, 5, 10, 25, 50, 80, 100],
    "yData": [40e-9, 10e-9, 5.5e-9, 2.8e-9, 1.5e-9, 0.9e-9, 0.7e-9]
}
```

| Field | Type | Description |
|-------|------|-------------|
| `xLabel` | string | Human-readable X-axis label including unit (e.g. "Frequency [Hz]") |
| `xData` | array of number | X-axis values |
| `yLabel` | string | Human-readable Y-axis label including unit |
| `yData` | array of number | Y-axis values (same length as `xData`; `(xData[i], yData[i])` is one point) |
| `conditions` | object (name → number or string) | Operating conditions under which the curve was measured |

---

## Provenance (data-source trail)

Every `datasheetInfo` carries an optional `provenance` array recording where its data
came from. Optional and closed, so records without it remain valid. Each entry:

| field | meaning |
|---|---|
| `source` | **required** — `manufacturerDatasheet` · `manufacturerParametric` · `manufacturerDatabase` · `distributor` · `librarianEnrichment` · `scrape` · `manual` |
| `sourceName` | human-readable source, e.g. `"TI parametric API"`, `"WE - Passive Components.mdb"`, `"DigiKey"` |
| `sourceUrl` | URL the value came from (optional) |
| `retrievedDate` | `YYYY-MM-DD` (optional) |
| `fields` | which `datasheetInfo` fields this source supplied — for mixed-source records (optional) |

It is a **list**: a record may combine sources (e.g. specs from the datasheet, a rated
voltage from a distributor, a missing field back-filled by librarian enrichment). The
canonical definition lives in `PEAS/schemas/utils.json#/$defs/provenance` (mirrored in
`MAS/schemas/utils.json`, which is self-contained).

---

## Enum Reference

### The device discriminator (no enum)

The device type of the component data is **not** an enum field — it is the name of the
top-level field: `mosfet`, `diode`, `igbt`, or `bjt`. The only `deviceType` enum in SAS is
in `inputs.designRequirements` (values `mosfet` / `diode` / `igbt` / `bjt`), where it states
the *required* device type. There is no `jfet` value anywhere.

### technology

Semiconductor material technology (`part.technology`, required).

| Value | Description |
|-------|-------------|
| `"Si"` | Silicon |
| `"SiC"` | Silicon Carbide |
| `"GaN"` | Gallium Nitride |
| `"GaAs"` | Gallium Arsenide |
| `"Ge"` | Germanium |

### subType

Optional per-device subtype. Each device file narrows the shared `part.subType` string to a
**closed enum** — a value from another device's list is rejected.

| Value | Device file | Description |
|-------|-------------|-------------|
| `"nChannel"` | mosfet, igbt | N-channel MOSFET or N-channel IGBT |
| `"pChannel"` | mosfet | P-channel MOSFET |
| `"powerBlock"` | mosfet | Half-bridge power block (two dies in one package) |
| `"rectifier"` | diode | Standard-recovery rectifier diode |
| `"schottky"` | diode | Silicon Schottky diode |
| `"sicSchottky"` | diode | Silicon Carbide Schottky diode |
| `"fastRecovery"` | diode | Fast recovery diode |
| `"ultrafast"` | diode | Ultrafast recovery diode |
| `"zener"` | diode | Zener voltage reference diode |
| `"tvs"` | diode | Transient Voltage Suppressor |
| `"esd"` | diode | ESD protection diode |
| `"npn"` | bjt | NPN bipolar transistor |
| `"pnp"` | bjt | PNP bipolar transistor |

When `subType` is omitted on a diode, the rectifier-family required set applies (see
[Per-subType required fields](#per-subtype-required-fields)).

### connectionType (assemblyType)

`mechanical.assemblyType` uses the PEAS `connectionType` enum (lowerCamelCase, aligned with
MAS):

| Value | Description |
|-------|-------------|
| `"pin"` | Pin terminals |
| `"screw"` | Screw terminals |
| `"smt"` | Surface mount |
| `"flyingLead"` | Flying leads |
| `"tht"` | Through-hole |
| `"pcbPad"` | PCB pad |
| `"chassis"` | Chassis / screw-mounted |

### status

Production lifecycle status (`manufacturerInfo.status`, from PEAS).

| Value | Description |
|-------|-------------|
| `"production"` | Currently in active production |
| `"prototype"` | Prototype / engineering samples |
| `"nrnd"` | Not Recommended for New Designs |
| `"obsolete"` | Discontinued |
| `"preview"` | Pre-release / sampling |
