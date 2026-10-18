# SAS Schema Reference

Complete field-by-field documentation for the Semiconductor Agnostic Structure schema.

**Schema version**: JSON Schema 2020-12
**Base URI**: `https://psma.com/sas/`

SAS builds on PEAS: shared primitives (`dimensionWithTolerance`, `curve`, `manufacturerInfo`,
`distributorInfo`, `provenance`, the `datasheetInfo*` mixins, `outputBase`) are `$ref`ed from
`https://psma.com/peas/...`, so validating an SAS document requires the PEAS repo checked out
alongside SAS. The reference documents for this schema are
[`examples/01_mosfet_ipb017n10n5.json`](../examples/01_mosfet_ipb017n10n5.json),
[`examples/02_diode_stps30l60ct.json`](../examples/02_diode_stps30l60ct.json),
[`examples/03_module_ff2mr12w3m1h.json`](../examples/03_module_ff2mr12w3m1h.json),
[`examples/04_mosfet_dual_iaucn04s7l025ah.json`](../examples/04_mosfet_dual_iaucn04s7l025ah.json)
(a two-die MOSFET package),
[`examples/05_tvs_ptvs1_022c_h.json`](../examples/05_tvs_ptvs1_022c_h.json)
(a TVS diode rated at 8/20 us, with its pulse waveforms stated), and the thyristor / JFET /
optocoupler records
[`examples/08_thyristor_scr_bt151_500r.json`](../examples/08_thyristor_scr_bt151_500r.json),
[`examples/09_thyristor_triac_bta16_600b.json`](../examples/09_thyristor_triac_bta16_600b.json),
[`examples/10_thyristor_protector_tisp4350h3bj.json`](../examples/10_thyristor_protector_tisp4350h3bj.json),
[`examples/11_optocoupler_vo617a_3.json`](../examples/11_optocoupler_vo617a_3.json) and
[`examples/12_jfet_jfe150.json`](../examples/12_jfet_jfe150.json).

---

## Table of Contents

- [Top-Level Structure (SAS.json)](#top-level-structure)
- [Device Documents (mosfet.json, diode.json, igbt.json, bjt.json, thyristor.json, jfet.json, optocoupler.json, module.json)](#device-documents)
  - [manufacturerInfo](#manufacturerinfo)
  - [distributorsInfo](#distributorsinfo)
  - [substitutesInfo](#substitutesinfo)
  - [datasheetInfo](#datasheetinfo)
- [Shared Sections (utils.json)](#shared-sections)
  - [part](#part)
  - [thermal](#thermal)
  - [mechanical](#mechanical)
  - [spiceModel (device-body)](#spicemodel-device-body)
- [MOSFET Sections](#mosfet-sections)
  - [mosfetElectrical](#mosfetelectrical)
  - [mosfetAmbientRating (T_A ratings)](#mosfetambientrating)
  - [mosfetAmbientRatingPoint](#mosfetambientratingpoint)
  - [mosfetDie (multi-die packages)](#mosfetdie)
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
  - [bjtBiasResistors (pre-biased transistors)](#bjtbiasresistors)
- [bjtDie (multi-die packages)](#bjtdie)
  - [bjtMatching](#bjtmatching)
- [Thyristor Sections](#thyristor-sections)
  - [thyristorElectrical](#thyristorelectrical)
  - [triacQuadrantRating](#triacquadrantrating)
  - [thyristorSurgeOnStateCurrent](#thyristorsurgeonstatecurrent)
  - [thyristorPeakPulseCurrent](#thyristorpeakpulsecurrent)
  - [thyristorOffStateCurrent](#thyristoroffstatecurrent)
  - [thyristorOffStateCapacitance](#thyristoroffstatecapacitance)
  - [thyristorDie](#thyristordie)
- [JFET Sections](#jfet-sections)
  - [jfetElectrical](#jfetelectrical)
  - [jfetTransconductance](#jfettransconductance)
  - [jfetDie](#jfetdie)
  - [jfetMatching](#jfetmatching)
- [Optocoupler Sections](#optocoupler-sections)
  - [optocouplerElectrical](#optocouplerelectrical)
  - [Optocoupler isolation](#optocoupler-isolation)
- [Power Module Sections](#power-module-sections)
  - [moduleElectrical](#moduleelectrical)
  - [moduleSwitchingEnergy](#moduleswitchingenergy)
  - [moduleMechanical](#modulemechanical)
  - [moduleCurves](#modulecurves)
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

An SAS document carries `inputs`, **exactly one** of `{mosfet, diode, igbt, bjt, thyristor, jfet, optocoupler, module}`, and
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
| `thyristor` | [thyristor.json](#thyristor-sections) | oneOf | Thyristor: SCR, triac, sidac, diac, thyristor surge protector |
| `jfet` | [jfet.json](#jfet-sections) | oneOf | Junction FET (n- or p-channel; Si, SiC) |
| `optocoupler` | [optocoupler.json](#optocoupler-sections) | oneOf | Optocoupler (LED input, photo-detector output, isolation barrier) |
| `module` | [module.json](#power-module-sections) | oneOf | Multi-die power module (half-bridge, full-bridge, sixpack, chopper, ...) |
| `outputs` | array of [outputs](#outputs) | See below | Computed results; `outputs[i]` aligns positionally with `inputs.operatingPoints[i]` |

Structural rules:

- `oneOf`: exactly one of `mosfet` / `diode` / `igbt` / `bjt` / `thyristor` / `jfet` / `optocoupler` /
  `module` must be present.
- `anyOf`: either **both** `inputs` and `outputs` are present (a full design document), or
  the document has **only** the device field (`maxProperties: 1` — a bare part record).
- `additionalProperties: false` — no extra fields allowed at the top level.

---

## Device Documents

**Files**: `schemas/mosfet.json`, `schemas/diode.json`, `schemas/igbt.json`, `schemas/bjt.json`,
`schemas/thyristor.json`, `schemas/jfet.json`, `schemas/optocoupler.json`, `schemas/module.json`

All eight device files share the same outer shape:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturerInfo` | [manufacturerInfo](#manufacturerinfo) | anyOf | Manufacturer data, including the nested `datasheetInfo` |
| `distributorsInfo` | array of [distributorInfo](#distributorsinfo) | No | Where to buy this component |
| `substitutesInfo` | array of [substituteInfo](#substitutesinfo) | No | Replacement parts: manufacturer-named successors and second sources |
| `spiceModel` | [spiceModel](#spicemodel-device-body) | anyOf | Device-body SPICE `.model` card for a simulation-sourced part (no datasheet) |

`anyOf`: the device body must contain `manufacturerInfo`, **or** `spiceModel`, **or** be an
empty object (`maxProperties: 0`). A body carrying only `substitutesInfo` satisfies none of
the three and is rejected. The device-body `spiceModel` is the canonical home for a
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

### substitutesInfo

Array of PEAS `utils.json#/$defs/substituteInfo` (closed object; only `partNumber` required),
the same type CTAS `controller.json` and COAS `converter.json` use (PEAS-RFC 0002).

| Field | Type | Description |
|-------|------|-------------|
| `partNumber` | string (**required**) | Part number of the replacement part |
| `manufacturer` | string or null | Its manufacturer. Omitted on a `successor` entry it means the same manufacturer as this part; it must be written when it differs |
| `type` | string (enum) | `drop-in`, `near-equivalent`, `functional`, `upgrade`, `downgrade`, `successor` |
| `notes` | string or null | Differences or caveats |
| `source` | string (enum) or null | `manufacturer`, `distributor`, `cross-reference`, `engineering` |

`type: "successor"` is directional: THIS part is superseded by the named one, one hop, as the
manufacturer states it — never inferred from `status: "obsolete"` or from a part-number
pattern. A successor that is itself superseded names its own successor on its own record, so a
chain resolves by traversal. The named part need not exist in any catalogue; whether it
resolves, and resolves once, is the referential pass's job — JSON Schema cannot check it. The
evidence for the claim is an ordinary [provenance](#provenance-data-source-trail) entry with
`fields: ["substitutesInfo"]`, carrying the same `sourceUrl`, `retrievedDate` and
`verification` stamp as any datasheet field.

Plus `country`, `distributedArea`, `phone`, `email`, `quantity`, `updatedAt`, `internal`,
`internalNote` — see PEAS `utils.json` for the full definition. Commercial data (cost, MOQ,
packaging) lives **here**, per distributor; there is no `business` section in `datasheetInfo`.

### datasheetInfo

Each device file defines its own closed `datasheetInfo` (there is no shared
device-discriminating `oneOf` — the file it lives in already fixes the device type):

| Field | Type | Required | mosfet | diode | igbt | bjt |
|-------|------|----------|--------|-------|------|-----|
| `part` | [part](#part) | **Yes** | yes | yes | yes | yes |
| `electrical` | per-device electrical | **Yes**, except on a multi-die MOSFET or BJT | yes | yes | yes | yes |
| `dies` | array of [mosfetDie](#mosfetdie) / [bjtDie](#bjtdie) | No | yes | -- | -- | yes |
| `matching` | array of [bjtMatching](#bjtmatching) | No (bjt only; requires `dies`) | -- | -- | -- | yes |
| `packagePowerDissipation` | number (W) | No (bjt only; requires `dies`) | -- | -- | -- | yes |
| `thermal` | [thermal](#thermal) | No | yes | yes | yes | yes |
| `mechanical` | [mechanical](#mechanical) | No | yes | yes | yes | yes |
| `modelParams` | per-device modelParams | No | yes | yes | yes | -- |
| `curves` | per-device curves | No | yes | yes | yes | -- |
| `provenance` | [provenance](#provenance-data-source-trail) | No | yes | yes | yes | yes |

The thyristor, JFET and optocoupler `datasheetInfo` are described in their own sections
([thyristor](#thyristor-sections), [jfet](#jfet-sections), [optocoupler](#optocoupler-sections)):
thyristor and jfet carry `part`, `electrical` XOR `dies[]`, `thermal`, `mechanical`, `provenance`
(jfet adds `matching[]`); optocoupler carries `part`, `electrical` (required), `thermal`,
`mechanical`, `provenance`. None of the three defines `modelParams` or `curves`.

`additionalProperties: false`. The diode `datasheetInfo` additionally carries the
[per-subType conditional required rules](#per-subtype-required-fields).

The mosfet `datasheetInfo` carries one further rule: `electrical` and `dies` are **mutually
exclusive** (a `oneOf` — exactly one of the two must be present), and a part whose
`part.dieConfiguration` is `dual` or `complementary` **must** carry `dies`. A package holding
two die therefore has no slot in which one die's R_DS(on) could be recorded as the part's.
See [mosfetDie](#mosfetdie).

The bjt `datasheetInfo` carries the same `electrical`-XOR-`dies` rule. In addition,
`matching` and `packagePowerDissipation` are legal only beside `dies`, and a part whose
`part.dieConfiguration` is `complementary` must not carry `part.subType` (each die states
its own polarity). As on the mosfet, a bjt whose `part.dieConfiguration` is `dual`,
`complementary` or `array` **must** carry `dies`, and therefore has no package-level
`electrical` in which one die's V_CEO, h_FE or bias resistors could be recorded as the
part's. See [bjtDie](#bjtdie).

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
| `dieConfiguration` | string (enum) | No | How many die the package holds: `single`, `dual` (two die of the same channel type / polarity), `complementary` (one n- and one p-type die), `array` (three or more die: BJT quads such as MAT14 / MMPQ3904, the 5-transistor CA3046; the count is the length of `dies`). Absent means one die. On a mosfet, `dual`/`complementary`/`array` makes [`dies`](#mosfetdie) required and forbids a package-level `electrical`. On a bjt the same three values make [`dies`](#bjtdie) required and forbid a package-level `electrical`. On an igbt only `single` is legal (multi-die IGBTs are `module` parts). On a diode only `single`/`dual` are allowed, and `dual` keeps the single `electrical` block, which then describes **one** diode: every value is per diode (per leg), never the package total. Exception: where the datasheet itself states the per-diode rating as a fixed fraction of the printed package value (e.g. ROHM "Io/2 per diode"), record that fraction; never infer a fraction when the datasheet is silent |
| `internalConnection` | string (enum) | No | How the die are wired inside the package, where the datasheet states it: for mosfet and igbt `independent`, `commonDrain`, `commonSource`, `halfBridge`; for diodes `independent`, `commonCathode`, `commonAnode`, `series` (BAV99-style); for bjt `independent`, `commonEmitter`, `commonBase`, `commonCollector` (the stated terminals bonded to one pin), `currentMirror` (bases tied and one transistor diode-connected: BCV61/62, BCM61/62). Never inferred from the package or part number |

Each device file's `datasheetInfo.part` narrows `subType` to a closed enum via `allOf`:

| Device file | Legal `subType` values |
|-------------|------------------------|
| `mosfet.json` | `nChannel`, `pChannel`, `powerBlock` |
| `diode.json` | `rectifier`, `schottky`, `sicSchottky`, `fastRecovery`, `ultrafast`, `switching`, `pin`, `zener`, `tvs`, `esd` |
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
`case` field plus optional `pinout` and `landPattern` (the **shared PEAS types**, hoisted
2026-08: the per-terminal `(pin, name, function)` map — G/D/S, `kelvinSource` on 4-lead
packages — and the manufacturer-recommended land pattern; no module defines its own variant
of these types). The extension layer is closed. No required fields.

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

**Required**: `drainSourceVoltage`, `onResistance`, `gateThresholdVoltage`, `totalGateCharge`,
and a continuous drain current rating: `continuousDrainCurrent` (case-referred, T_C = 25 °C)
**or**, for a part whose datasheet rates I_D only at an ambient temperature, at least one
[`ambientRatings`](#mosfetambientrating) point carrying `continuousDrainCurrent`.

The field set lives in `mosfet.json#/$defs/electricalBase`, which requires the first four;
`electrical` is that base plus the drain-current rule, written as
`if (some ambientRatings point has continuousDrainCurrent) else required: ["continuousDrainCurrent"]`
so a part with neither still fails with *'continuousDrainCurrent' is a required property*. A part
that prints a T_C rating is unchanged. The split exists because
[`dies[].electrical`](#mosfetdie) uses the **base**: a continuous drain current is a
package rating, and vendors such as TI publish one operating current for a package
holding two die (SLPS666), so requiring it per die would make the faithful record
unwritable. Everything that `$ref`s `#/$defs/electrical` — the package-level block and
the module `switch` block — still requires a drain-current rating.

**Case vs ambient.** `continuousDrainCurrent` and `powerDissipation` are **case-referred**
(T_C = 25 °C). Small packages without an exposed pad (SO-8, SOT-23, TSOP-6, SC-70, wafer-level
CSP) print I_D and P_D only at T_A = 25 °C with the part on a test board, usually in two columns
(10 s and steady state), and PowerPAK / DFN parts often print T_A rows beside the T_C row. A T_A
figure is **never** written into the case-referred fields — it goes in `ambientRatings`.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `drainSourceVoltage` | number | **Yes** | V | V_DS max -- maximum drain-source voltage |
| `gateSourceVoltageMax` | number | No | V | V_GS max -- maximum gate-source voltage |
| `continuousDrainCurrent` | number | **Yes, unless an ambient point carries I_D** | A | I_D at T_c=25C. Case-referred only — a T_A figure goes in `ambientRatings` |
| `continuousDrainCurrentAt100C` | number | No | A | I_D at T_c=100C |
| `pulsedDrainCurrent` | number | No | A | I_DM -- pulsed drain current |
| `powerDissipation` | number | No | W | P_D max at T_c=25C. Case-referred only — a T_A figure goes in `ambientRatings` |
| `ambientRatings` | array of [mosfetAmbientRating](#mosfetambientrating) | No | — | I_D / P_D / I_S rated at an ambient temperature, one entry per printed condition (time base + mounting). `minItems: 1`, `uniqueItems`. Also allowed per die |
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

### mosfetAmbientRating

`mosfet.json#/$defs/ambientRating` — one printed ambient-rating condition. Closed object. A
Vishay "ABSOLUTE MAXIMUM RATINGS T_A = 25 °C" table with **10 s** and **Steady State** columns is
two entries; a datasheet printing two mounting conditions (Diodes Inc.: minimum pad vs 1 in²
copper) is one entry per mounting. An R_th(j-a) row printed for a condition with no current or
power under it (Vishay "t ≤ 5 s") is an entry with `thermalResistanceJunctionAmbient` and no
`points`.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `timeBase` | string (enum) | No | — | `steadyState` or `transient`. **Absent = the datasheet does not say** (a single LIMIT column with no duration note); never inferred from P_D arithmetic |
| `duration` | number (> 0) | when `timeBase` is `transient` | s | Length of a transient rating: "t ≤ 10 s" is `10`. Not allowed on a steady-state or unstated condition |
| `mounting` | string (1–300) | No | — | The board-mounting note **as printed** ("Surface mounted on 1" x 1" FR4 board"). Absent = the datasheet prints none |
| `thermalResistanceJunctionAmbient` | [dimensionWithTolerance](#dimensionwithtolerance) | No | K/W | R_th(j-a) for this time base and mounting: typical in `nominal`, maximum in `maximum` |
| `points` | array of [mosfetAmbientRatingPoint](#mosfetambientratingpoint) | No | — | The ratings printed under this condition, one per ambient temperature (and gate drive) |

An entry carries `points`, `thermalResistanceJunctionAmbient`, or both.

### mosfetAmbientRatingPoint

`mosfet.json#/$defs/ambientRatingPoint` — the ratings at one ambient temperature. Closed
object; same field names, units and sign convention as the case-referred fields.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `ambientTemperature` | number | **Yes** | °C | T_A of the row ("T_A = 70 °C" is `70`) |
| `gateSourceVoltage` | number | No | V | Gate drive of the row, signed as printed — only where the datasheet rates I_D at more than one V_GS |
| `continuousDrainCurrent` | number | one of these three | A | I_D at this T_A |
| `powerDissipation` | number (> 0) | one of these three | W | P_D at this T_A |
| `bodyDiodeContinuousCurrent` | number | one of these three | A | I_S (diode conduction) at this T_A |

Example (Vishay Si4896DY, SO-8, document 71300 — T_A ratings only):

```json
"ambientRatings": [
  {"timeBase": "transient", "duration": 10, "mounting": "Surface Mounted on 1\" x 1\" FR4 board.",
   "thermalResistanceJunctionAmbient": {"nominal": 33, "maximum": 40},
   "points": [{"ambientTemperature": 25, "continuousDrainCurrent": 9.5, "powerDissipation": 3.1, "bodyDiodeContinuousCurrent": 2.8},
              {"ambientTemperature": 70, "continuousDrainCurrent": 7.6, "powerDissipation": 2.0}]},
  {"timeBase": "steadyState", "mounting": "Surface Mounted on 1\" x 1\" FR4 board.",
   "thermalResistanceJunctionAmbient": {"nominal": 65, "maximum": 80},
   "points": [{"ambientTemperature": 25, "continuousDrainCurrent": 6.7, "powerDissipation": 1.56, "bodyDiodeContinuousCurrent": 1.4},
              {"ambientTemperature": 70, "continuousDrainCurrent": 5.4, "powerDissipation": 1.0}]}
]
```

The schema cannot check that the steady-state I_D is below the 10 s I_D, that I_D falls with
T_A, or that P_D ≈ (T_j(max) − T_A) / R_th(j-a) — those are Blade Runner checks.

### mosfetDie

`mosfet.json#/$defs/die` — one die inside a multi-die package. Used through
`datasheetInfo.dies[]`, which is **mutually exclusive** with the package-level
`electrical` and has `minItems: 2`. Extends the shared `utils.json#/$defs/dieBase`
and is sealed with `unevaluatedProperties: false`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | The datasheet's own label for the die — "Q1", "Q2", "Channel 1". Verbatim, never invented; a datasheet that does not distinguish its die gives no die entries to write |
| `role` | string | No | The datasheet's functional name where it gives one ("Control FET", "Sync FET"), verbatim |
| `pins` | array of string | No | Pin identifiers belonging to this die, matching entries of `mechanical.pinout` |
| `subType` | string (enum) | **Yes** | Channel type OF THIS DIE: `nChannel` or `pChannel`. `powerBlock` is not legal here — it describes a package, not a die |
| `electrical` | [mosfetElectricalBase](#mosfetelectrical) | **Yes** | The complete electrical block, per die. Same fields as a single-die part, minus the `continuousDrainCurrent` requirement, which is a package rating — write one only where the vendor publishes it per die, and never put a package figure on a die |
| `thermal` | [thermal](#thermal) | No | Per-die thermal figures where the datasheet gives them; the package figure stays in `datasheetInfo.thermal` |

Every die states its own values even when the datasheet prints them as equal
("Q1 = Q2 = 95 mOhm"), so "both die are 95 mOhm" and "the part is 95 mOhm" are
different documents. A pin bonded to more than one die inside the package (the shared
drain of a common-drain dual) is listed in the `pins` of each die it belongs to. The schema
cannot check that `pins` exist in `mechanical.pinout`, that a pin listed by two die is one
`part.internalConnection` actually shares, or that `name` is unique across the array — those
are referential checks and belong to the ingest gate.

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
| `forwardCurrent` | number | A | I_F(AV) -- average forward current, per diode (per leg on a `dual` package, never the package total) |
| `surgeCurrent` | number | A | I_FSM -- non-repetitive surge current |
| `forwardVoltage` | number | V | V_F -- forward voltage drop |
| `forwardVoltageAt` | number | A | I_F at which V_F is specified |
| `reverseLeakageCurrent` | number | A | I_R -- reverse leakage current |
| `reverseRecoveryTime` | number | s | t_rr -- reverse recovery time |
| `reverseRecoveryCharge` | number | C | Q_rr -- reverse recovery charge |
| `junctionCapacitance` | number | F | C_j -- junction capacitance |
| `junctionCapacitanceVr` | number | V | V_R at which C_j is measured |
| `powerDissipation` | number | W | P_D max |
| `clampingVoltage` | number | V | V_C for TVS/ESD, at `clampingCurrent` with `clampingWaveform`. Without `clampingCurrent` the record does not state the test current |
| `clampingCurrent` | number > 0 | A | Peak test current at which `clampingVoltage` is specified (the datasheet's "V_C @ I_PP" current, or e.g. 1 A). Same name and meaning as RAS varistor `clampingCurrent`. Requires `clampingVoltage` |
| `clampingWaveform` | [PEAS `surgeWaveform`](../../PEAS/docs/architecture.md#surge-waveform-peas-rfc-0003-2026-10) | — | Impulse at which `clampingVoltage` was measured (e.g. `8/20`, `TLP 100 ns`). Requires `clampingVoltage`. Absent = not stated (no default) |
| `breakdownVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | V | V_BR for Zener/TVS/ESD. For zeners this **is** the zener voltage V_Z (min/nom/max, specified at `zenerTestCurrent`) — there is deliberately no separate `zenerVoltage` field |
| `zenerTestCurrent` | number | A | I_ZT -- test current at which V_Z (breakdownVoltage) is specified |
| `zenerImpedance` | number | Ohm | Z_ZT -- dynamic impedance at I_ZT |
| `standoffVoltage` | number | V | V_RWM -- working voltage for TVS/ESD |
| `peakPulseCurrent` | number | A | I_PP (I_PPM) rating for TVS/ESD, at `peakPulseCurrentWaveform` |
| `peakPulseCurrentWaveform` | [PEAS `surgeWaveform`](../../PEAS/docs/architecture.md#surge-waveform-peas-rfc-0003-2026-10) | — | Impulse the `peakPulseCurrent` rating is stated at (e.g. `8/20` per IEC 61000-4-5). Requires `peakPulseCurrent`. Absent = not stated (no default) |
| `peakPulsePower` | number | W | P_PP (P_PPM) rating for TVS/ESD, at `peakPulsePowerWaveform` |
| `peakPulsePowerWaveform` | [PEAS `surgeWaveform`](../../PEAS/docs/architecture.md#surge-waveform-peas-rfc-0003-2026-10) | — | Impulse the `peakPulsePower` rating is stated at (classically `10/1000`). Requires `peakPulsePower`. Absent = not stated (no default) |
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
| rectifier family (`rectifier`, `schottky`, `sicSchottky`, `fastRecovery`, `ultrafast`, `switching`, `pin`) — or `subType` absent | `reverseVoltage`, `forwardVoltage`, `forwardCurrent` |

TVS and ESD parts do not have a `forwardCurrent` (I_F(AV)) rating — that is a rectifier
parameter; their forward-direction capability, when published, is the surge `surgeCurrent`
(I_FSM).

### Pulse-rating waveforms (SAS-RFC 0003)

Each pulse rating carries its own waveform field, because ratings at different waveforms
are not comparable (an 8/20 us I_PP is many times a 10/1000 us I_PP for the same die). The
waveform values are the PEAS `surgeWaveform` enum: `8/20`, `10/1000`, `10/350`, `2/10`,
`5/320`, `10/700`, `10/560`, `9/720`, `10/160`, `TLP 100 ns` (wave and standard per value in
PEAS `docs/architecture.md`). `dependentRequired` on `diodeElectrical` makes a condition
impossible to store without the value it qualifies:

| if present | requires |
|---|---|
| `clampingCurrent` | `clampingVoltage` |
| `clampingWaveform` | `clampingVoltage` |
| `peakPulseCurrentWaveform` | `peakPulseCurrent` |
| `peakPulsePowerWaveform` | `peakPulsePower` |

The reverse is not enforced: a pulse value without a waveform stays valid and means the
record does not state it. The waveform fields are optional, and the subType required sets
are unchanged.

Example — Bourns PTVS1-022C-H (from the PTVS1-xxxC-H datasheet: I_PPM 1 kA per 8/20 us
IEC 61000-4-5; typical V_C measured at I_PPM, 8/20 us), full document in
[`examples/05_tvs_ptvs1_022c_h.json`](../examples/05_tvs_ptvs1_022c_h.json):

```json
"electrical": {
  "standoffVoltage": 22,
  "breakdownVoltage": {"minimum": 24, "maximum": 27},
  "reverseLeakageCurrent": 1e-05,
  "peakPulseCurrent": 1000,  "peakPulseCurrentWaveform": "8/20",
  "clampingVoltage": 28,     "clampingCurrent": 1000, "clampingWaveform": "8/20",
  "junctionCapacitance": 2e-09
}
```

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
| `powerDissipation` | number | No | W | P_D max. Inside a die: the **per-transistor** rating; a package total goes in `datasheetInfo.packagePowerDissipation` and is never divided down to fill this |
| `voltageNoiseDensity` | number | No | V/√Hz | e_n, input-referred voltage noise density (typical); same name and unit as AAS `amplifierCommon` |
| `voltageNoiseDensityFrequency` | number | No | Hz | Frequency at which e_n is specified; requires `voltageNoiseDensity` |
| `voltageNoiseDensityCollectorCurrent` | number | No | A | Collector current at which e_n is specified (e_n depends strongly on I_C); requires `voltageNoiseDensity` |
| `biasResistors` | [bjtBiasResistors](#bjtbiasresistors) | No | -- | Built-in bias resistors; present only on a resistor-equipped ("pre-biased", "digital", BRT/RET) transistor, and its presence is what marks one. On a multi-die part it goes in each die's `electrical` |
| `inputOnVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V | V_I(on), magnitude, stored as the **distribution** of the switching voltage: the drive that guarantees "on" is `maximum`. Toshiba prints the min..max distribution (stored as is); Nexperia/ROHM print the guarantee in a "Min" column (`V_I(on) min 2.5 V`), which goes to `maximum`. Requires `biasResistors` |
| `inputOnVoltageVce` | number | No | V | V_CE at which `inputOnVoltage` is specified (> 0); requires `inputOnVoltage` |
| `inputOnVoltageIc` | number | No | A | I_C at which `inputOnVoltage` is specified (> 0); requires `inputOnVoltage` |
| `inputOffVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V | V_I(off), magnitude, stored as the distribution: the input level that guarantees "off" is `minimum`. Nexperia/ROHM print it in a "Max" column (`V_I(off) max 0.8 V`), which goes to `minimum`. Requires `biasResistors` |
| `inputOffVoltageVce` | number | No | V | V_CE at which `inputOffVoltage` is specified (> 0); requires `inputOffVoltage` |
| `inputOffVoltageIc` | number | No | A | I_C at which `inputOffVoltage` is specified (> 0); requires `inputOffVoltage` |
| `inputVoltageMax` | number | No | V | Absolute maximum forward input voltage, input to ground (Nexperia V_I positive, onsemi V_IN(fwd)); requires `biasResistors` |
| `inputReverseVoltageMax` | number | No | V | Absolute maximum reverse input voltage, as a magnitude (Nexperia V_I -10 V is stored as 10; onsemi V_IN(rev)); requires `biasResistors` |
| `outputCurrentMax` | number | No | A | I_O, **only** where the datasheet prints it separately from, and lower than, I_C(max) (ROHM I_O 50 mA beside I_C 100 mA). Where I_O is the only current rating (Nexperia) it is `collectorCurrent` and this field is omitted. Requires `biasResistors` |

V_EBO, V_OH/V_OL, input current I_I and input gain G_I have no field yet.

### bjtBiasResistors

`bjt.json#/$defs/biasResistors` — the resistor network built into a resistor-equipped
transistor: R1 in series with the base, R2 from base to emitter. Closed; at least one of
R1 / R2 is required. There is no `prebiased` subType or flag: the presence of this block
is the marker, so it cannot contradict itself, and it works per die (a mixed pair is one
pre-biased die and one plain die). R2 "open" (R1-only types such as PDTC114T, RN1711JE)
is stated by omitting `baseEmitterResistance`, never by a sentinel. A tolerance printed as
a percentage (Panasonic "-30% 22 +30%") is stored as the limits it states.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `baseResistance` | [dimensionWithTolerance](#dimensionwithtolerance) | R1 or R2 | Ohm | R1, the series base (input) resistor; `nominal` = typical (or title) value, `minimum`/`maximum` = its limits |
| `baseEmitterResistance` | [dimensionWithTolerance](#dimensionwithtolerance) | R1 or R2 | Ohm | R2, base-emitter resistor; omitted when R2 is open. Store what is printed (often the nominal only); never derive R2 limits from R1 and the ratio |
| `resistanceRatio` | [dimensionWithTolerance](#dimensionwithtolerance) | No | 1 | The ratio **exactly as printed**, never inverted. Requires `resistanceRatioDefinition`, `baseResistance` and `baseEmitterResistance` |
| `resistanceRatioDefinition` | string (enum) | No | -- | `"R2/R1"` (Nexperia, ROHM) or `"R1/R2"` (onsemi, Toshiba, Panasonic): which ratio `resistanceRatio` holds. Requires `resistanceRatio` |

On a part whose `part.dieConfiguration` is `dual`, `complementary` or `array` there is no
package-level `electrical` at all (`dies` is required), so the resistors are stated per die
in `dies[].electrical`: a package block could not say which transistor carries which
resistors (a PUMD9 pairs an NPN 10k/47k die with a PNP die of different f_T).
See `examples/07_bjt_prebiased_dual_pumh11.json`.

### bjtDie

`bjt.json#/$defs/die` — one transistor die inside a multi-die package (dual, complementary
pair, matched pair, quad or larger array). Used through `datasheetInfo.dies[]`, which is
**mutually exclusive** with the package-level `electrical` and has `minItems: 2`. Extends
the shared `utils.json#/$defs/dieBase` and is sealed with `unevaluatedProperties: false`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | **Yes** | The datasheet's own label for the die ("Q1", "Channel 1", "TR1"), verbatim and never invented |
| `role` | string | No | The datasheet's functional name where it gives one, verbatim |
| `pins` | array of string | No | Pin identifiers belonging to this die, matching entries of `mechanical.pinout` |
| `subType` | string (enum) | **Yes** | Polarity OF THIS DIE: `npn` or `pnp` |
| `electrical` | [bjtElectrical](#bjtelectrical) | **Yes** | The complete BJT electrical block, per die, with the same required `collectorEmitterVoltage` + `collectorCurrent` (BJT duals print I_C per transistor). `powerDissipation` is the **per-transistor** rating |
| `thermal` | [thermal](#thermal) | No | Per-die figures where given; the package figure stays in `datasheetInfo.thermal` |

Every die states its own values even when the datasheet prints them once for "each
transistor", so "both transistors are 45 V" and "the part is 45 V" are different documents.
A shared pin is listed by every die bonded to it: on a `commonEmitter` pair (Toshiba RN1707JE,
ESV pin 2 = E common) pin 2 appears in both dies' `pins`. The schema cannot check that die
names are unique, that `pins` exist in the pinout, or that a pin listed by two die is one the
stated `internalConnection` shares — those are the ingest gate's referential checks.

### bjtMatching

`bjt.json#/$defs/matching` — one matching specification between die. Closed; at least one
quantity is required. Every quantity is a [dimensionWithTolerance](#dimensionwithtolerance)
(`nominal` = typical column, `maximum` = guaranteed), stated as a magnitude.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `dies` | array of string (≥2, unique) | No | -- | `dies[].name` values this spec relates; absent = between any two die (quad style) |
| `baseEmitterVoltageMatch` | dimensionWithTolerance | one of the five | V | \|ΔV_BE\| at equal I_C, the pair's offset voltage V_OS |
| `baseEmitterVoltageMatchDrift` | dimensionWithTolerance | one of the five | V/K | TCV_OS |
| `currentGainMatch` | dimensionWithTolerance | one of the five | fraction | \|Δh_FE\|/h_FE (0.005 = 0.5 %) |
| `baseCurrentMatch` | dimensionWithTolerance | one of the five | A | \|I_B1 − I_B2\|, the pair's offset current I_OS |
| `collectorCurrentMatch` | dimensionWithTolerance | one of the five | fraction | \|I_C1/I_C2 − 1\|, the mirror-ratio error |
| `testCollectorCurrent` | number | No | A | I_C per die at which the spec holds |
| `testCollectorBaseVoltage` | number | No | V | V_CB at which the spec holds |
| `testTemperature` | number | No | °C | Ambient temperature of the spec |

See `examples/06_bjt_dual_matched_ssm2212.json`.

---

## Thyristor Sections

**File**: `schemas/thyristor.json` (`$defs`)

One file for the whole four-layer family, because SCR, triac, sidac, diac and thyristor surge
protective device (TSPD) share one vocabulary (V_DRM, I_TSM, I_H, V_T, dV/dt) and datasheets name
them with the same symbols. `part.subType` is the closed enum `scr` | `triac` | `sidac` | `diac` |
`surgeProtector` (`$defs/subType`, the anchor the requirement-side `thyristorType` `$ref`s). A part
sold as a protector is a `surgeProtector` even when its silicon is a sidac. Thyristor MODULES and
press-pack discs (Infineon TT/TD/DD, Vishay VS-..RIA) are not this file.

`datasheetInfo`: `part` required; exactly one of package-level `electrical` or `dies[]`
(minItems 2). Rules (each an `allOf` member of `datasheetInfo`):

- **Multi-die gate**: `part.dieConfiguration` `dual` or `array` requires `dies[]` (multi-line telecom
  protectors such as Bourns TISP61xx). `part.internalConnection` is narrowed to `independent`,
  `commonAnode`, `commonCathode`, `series`.
- **Triac-only fields**: `quadrantRatings`, `criticalRateOfChangeCommutatingCurrent` and
  `criticalRateOfRiseCommutatingVoltage` are refused on any other member.
- **Headline ratings per member**: `scr` needs `repetitivePeakOffStateVoltage` plus
  `rmsOnStateCurrent` or `averageOnStateCurrent`; `triac` needs `repetitivePeakOffStateVoltage` +
  `rmsOnStateCurrent`; `sidac` / `diac` need `breakoverVoltage`; `surgeProtector` needs
  `repetitivePeakOffStateVoltage` + `breakoverVoltage` + `peakPulseCurrents`.
- `isolationCapacitance` requires `isolationVoltage`; every rate / test-condition field requires
  the value it qualifies (`dependentRequired`).

Pinout: a triac's main terminals use the PEAS pin functions `mainTerminal1` / `mainTerminal2`
(MT1/MT2, also the two symmetrical terminals of a bidirectional protector); an SCR uses `anode` /
`cathode` / `gate`. See `examples/08_thyristor_scr_bt151_500r.json`,
`examples/09_thyristor_triac_bta16_600b.json` and `examples/10_thyristor_protector_tisp4350h3bj.json`.

### thyristorElectrical

Closed object. Every value SI: V, A, s, A/s (50 A/us = 5e7), V/s, A^2 s, F, W. Voltages and currents
are magnitudes (a bidirectional part printing +-350 V stores 350). Littelfuse SIDACtor V_S / I_S are
the same quantities as Bourns V(BO) / I(BO) and map to `breakoverVoltage` / `breakoverCurrent`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `conductionDirection` | string (enum: `unidirectional`, `bidirectional`) | No | Whether the device blocks and conducts in one direction or both. Inherent for scr (unidirectional) and triac/diac (bidirectional); state it for sidacs and surge protectors, which come in both. |
| `repetitivePeakOffStateVoltage` | number | No | V_DRM: repetitive peak off-state voltage, in V (magnitude). For a surge protector this is its stand-off rating (the line voltage it never clamps). (exclusiveMinimum 0) |
| `repetitivePeakReverseVoltage` | number | No | V_RRM: repetitive peak reverse voltage of an SCR, in V. (exclusiveMinimum 0) |
| `rmsOnStateCurrent` | number | No | I_T(RMS): RMS on-state current, in A, at onStateCurrentTemperature. (exclusiveMinimum 0) |
| `averageOnStateCurrent` | number | No | I_T(AV): average on-state current (half-sine conduction), in A, at onStateCurrentTemperature. (exclusiveMinimum 0) |
| `onStateCurrentTemperature` | number | No | Reference temperature at which rmsOnStateCurrent / averageOnStateCurrent are rated, in degC ('T_mb <= 109 C' is 109). |
| `onStateCurrentTemperatureReference` | string (enum: `case`, `ambient`, `lead`) | No | Which temperature onStateCurrentTemperature is: 'case' (T_c, and the T_mb mounting base of TO-220 class packages), 'ambient' or 'lead'. |
| `surgeOnStateCurrent` | array of [surgeOnStateCurrent](#thyristorsurgeonstatecurrent) | No | I_TSM ratings (see thyristorSurgeOnStateCurrent). (minItems 1) |
| `currentSquaredTime` | number | No | I^2t for fusing, in A^2 s. (exclusiveMinimum 0) |
| `currentSquaredTimeDuration` | number | No | Pulse duration at which currentSquaredTime is stated, in s (0.01 for 10 ms). (exclusiveMinimum 0) |
| `criticalRateOfRiseOnStateCurrent` | number | No | dI_T/dt (di/dt) maximum, in A/s (50 A/us = 5e7). (exclusiveMinimum 0) |
| `criticalRateOfRiseOffStateVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | dV_D/dt with the gate OPEN, in V/s: the datasheet minimum (and typical where printed). A figure printed only with a gate-cathode resistor is not this value and is left out. |
| `criticalRateOfRiseOffStateVoltageTemperature` | number | No | Junction temperature at which criticalRateOfRiseOffStateVoltage is specified, in degC. |
| `criticalRateOfChangeCommutatingCurrent` | number | No | dI_com/dt of a triac: the rate of fall of current at commutation it survives without retriggering, in A/s (2 A/ms = 2000). Triac only. (exclusiveMinimum 0) |
| `criticalRateOfRiseCommutatingVoltage` | number | No | dV_com/dt of a triac, in V/s. Triac only. (exclusiveMinimum 0) |
| `gateTriggerCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_GT of an SCR (or of a triac that prints one figure for all quadrants), in A. |
| `gateTriggerVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_GT, in V. |
| `latchingCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_L, in A. |
| `holdingCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_H, in A. |
| `quadrantRatings` | array of [quadrantRating](#triacquadrantrating) | No | Per-quadrant gate figures of a triac (see triacQuadrantRating). Triac only. (minItems 1) |
| `peakGateCurrent` | number | No | I_GM, in A. (exclusiveMinimum 0) |
| `peakGateReverseVoltage` | number | No | V_RGM, in V. (exclusiveMinimum 0) |
| `peakGatePower` | number | No | P_GM, in W. (exclusiveMinimum 0) |
| `averageGatePower` | number | No | P_G(AV), in W. (exclusiveMinimum 0) |
| `onStateVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_T (V_TM), in V, at onStateVoltageCurrent. |
| `onStateVoltageCurrent` | number | No | On-state current at which onStateVoltage is specified, in A. (exclusiveMinimum 0) |
| `offStateCurrent` | array of [offStateCurrent](#thyristoroffstatecurrent) | No | Leakage at each printed condition (see thyristorOffStateCurrent). (minItems 1) |
| `gateControlledTurnOnTime` | number | No | t_gt, in s (typical as printed). (exclusiveMinimum 0) |
| `circuitCommutatedTurnOffTime` | number | No | t_q, in s (typical as printed). (exclusiveMinimum 0) |
| `isolationVoltage` | number | No | Isolation test voltage V_isol between the insulated mounting tab / heatsink and the terminals of an isolated-tab package, RMS at 50/60 Hz, in V - the same quantity and name as module.json isolationVoltage. Present only on an isolated-tab part. (exclusiveMinimum 0) |
| `isolationCapacitance` | number | No | C_isol between the terminals and the external heatsink of an isolated-tab package, in F. (exclusiveMinimum 0) |
| `breakoverVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_(BO) (Littelfuse V_S) at the slow ramp of breakoverVoltageRampRate, in V (magnitude). |
| `breakoverVoltageRampRate` | number | No | dv/dt of the ramp at which breakoverVoltage is measured, in V/s (750 V/ms = 7.5e5). (exclusiveMinimum 0) |
| `impulseBreakoverVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_(BO) under a fast impulse (overshoot rating of a protector), in V. |
| `impulseBreakoverVoltageRampRate` | number | No | dv/dt of the impulse at which impulseBreakoverVoltage is stated, in V/s. (exclusiveMinimum 0) |
| `impulseBreakoverCurrentRampRate` | number | No | di/dt of the impulse at which impulseBreakoverVoltage is stated, in A/s. (exclusiveMinimum 0) |
| `breakoverCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_(BO) (Littelfuse I_S), in A. |
| `breakbackVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | Delta V of a diac/sidac: the drop from V_(BO) to the on-state voltage at the stated current, in V. |
| `peakPulseCurrents` | array of [peakPulseCurrent](#thyristorpeakpulsecurrent) | No | Impulse current ratings of a surge protector, one per waveform (see thyristorPeakPulseCurrent). (minItems 1) |
| `offStateCapacitance` | array of [offStateCapacitance](#thyristoroffstatecapacitance) | No | C_off at each printed bias (see thyristorOffStateCapacitance). (minItems 1) |
| `powerDissipation` | number | No | P_D / P_tot maximum, in W, where the datasheet prints one. (exclusiveMinimum 0) |

### triacQuadrantRating

`thyristor.json#/$defs/quadrantRating` — gate figures of a triac in ONE quadrant (Q1 = MT2+ G+,
Q2 = MT2+ G-, Q3 = MT2- G-, Q4 = MT2- G+; WeEn/NXP print 'T2+ G+'). A 3-quadrant triac has no Q4 entry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `quadrant` | string (enum: `Q1`, `Q2`, `Q3`, `Q4`) | **Yes** |  |
| `gateTriggerCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_GT in this quadrant, in A. |
| `latchingCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_L in this quadrant, in A. |
| `gateTriggerVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_GT in this quadrant, in V. |

### thyristorSurgeOnStateCurrent

`thyristor.json#/$defs/surgeOnStateCurrent` — one I_TSM rating at line frequency; datasheets print
two or three, so it is an array entry.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current` | number | **Yes** | Peak surge current, in A. (exclusiveMinimum 0) |
| `duration` | number | **Yes** | Duration of the surge, in s (0.01 for a 10 ms half sine, 0.02 for one 50 Hz full cycle, 1000 for Bourns' '1000 s 50/60 Hz a.c.'). (exclusiveMinimum 0) |
| `shape` | string (enum: `halfSine`, `fullSine`) | **Yes** | 'halfSine' = one line-frequency half cycle (the usual SCR rating); 'fullSine' = whole line-frequency cycles for the stated duration (the usual triac / protector rating). |

### thyristorPeakPulseCurrent

`thyristor.json#/$defs/peakPulseCurrent` — one impulse rating (I_TSP / I_PP) of a surge protector.
Protector datasheets print six to nine, so it is an array (unlike the scalar diode
`peakPulseCurrent`). The waveform is **required** and is the PEAS `surgeWaveform` label exactly as
printed; a rating whose waveform is not a member is left out, never approximated.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current` | number | **Yes** | Peak impulse current, in A. (exclusiveMinimum 0) |
| `waveform` | PEAS [surgeWaveform](#pulse-rating-waveforms-sas-rfc-0003) | **Yes** |  |

### thyristorOffStateCurrent

`thyristor.json#/$defs/offStateCurrent` — leakage at one condition (25 C and T_j(max) differ by
three orders of magnitude, so each is its own entry).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `current` | [dimensionWithTolerance](#dimensionwithtolerance) | **Yes** | I_D / I_DRM (and I_R / I_RRM where printed as the same row), in A, as a magnitude. |
| `voltage` | number | No | Off-state voltage at which it is specified, in V (magnitude). (minimum 0) |
| `temperature` | number | No | Junction (or ambient, as printed) temperature of the test, in degC. |

### thyristorOffStateCapacitance

`thyristor.json#/$defs/offStateCapacitance` — C_off of a protector at one DC bias.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `capacitance` | [dimensionWithTolerance](#dimensionwithtolerance) | **Yes** | C_off, in F. |
| `biasVoltage` | number | No | DC bias across the device during the measurement, in V, signed as printed. |
| `frequency` | number | No | Measurement frequency, in Hz. (exclusiveMinimum 0) |

### thyristorDie

`thyristor.json#/$defs/die` — extends `utils.json#/$defs/dieBase` (`name`, `role`, `pins`) with
an optional per-die `subType`, the required per-die `electrical` ([thyristorElectrical](#thyristorelectrical))
and optional per-die `thermal`; sealed with `unevaluatedProperties: false`. Per-die values are
stated as printed "per device"; a package total is never divided down.

---

## JFET Sections

**File**: `schemas/jfet.json` (`$defs`)

Junction FETs: Si small-signal and low-noise parts (J111, 2SK, U40x, JFE150, LSK389) and
normally-on SiC power JFETs (UnitedSiC UJ3N, `part.technology` `SiC`). `part.subType` is
`nChannel` | `pChannel` (`$defs/subType`, the anchor of the requirement-side `channel`). A SiC
cascode (JFET + LV MOSFET, UJ3C/UJ4C/UF3C) is normally-off and is a `mosfet.json` part.

`datasheetInfo`: `part` required; exactly one of `electrical` or `dies[]` (minItems 2). Rules:
`part.dieConfiguration` `dual` requires `dies[]`; `matching[]` is legal only beside `dies[]`;
`part.internalConnection` is narrowed to `independent`. Field names reuse the mosfet ones where the
quantity is the same, and the AAS / bjt noise names, so one query spans op amps, matched BJTs and JFETs.

### jfetElectrical

Closed object. **Required**: a drain rating, `drainSourceVoltage` **or** `gateDrainVoltageMax`
(small-signal JFETs often print only V_DG). Absolute-maximum voltages and currents are magnitudes;
bias quantities whose sign carries meaning (V_GS(off), test V_GS) are signed exactly as printed
(negative for an n-channel part).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `drainSourceVoltage` | number | No | V_DS / V_DSS absolute maximum (or the guaranteed V_(BR)DSS where that is the only drain rating), in V. (exclusiveMinimum 0) |
| `gateDrainVoltageMax` | number | No | V_GD / V_DG absolute maximum reverse gate-drain voltage, in V - the drain rating many small-signal JFETs print instead of V_DS (J111 'V_DG 35 V'). (exclusiveMinimum 0) |
| `gateSourceVoltageMax` | number | No | V_GS / V_GSS absolute maximum reverse gate-source voltage (or V_(BR)GSS), in V, as a magnitude. Same name as the mosfet field. (exclusiveMinimum 0) |
| `gateForwardCurrentMax` | number | No | I_GF / I_GS absolute maximum forward gate current, in A. (exclusiveMinimum 0) |
| `continuousDrainCurrent` | number | No | I_D / I_DS absolute maximum drain current, in A. Same name as the mosfet field. (exclusiveMinimum 0) |
| `saturationDrainCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_DSS: drain current at V_GS = 0, in A (magnitude), at saturationDrainCurrentVds. Graded parts (2SK209-GR) are catalogued per orderable grade. |
| `saturationDrainCurrentVds` | number | No | Drain-source voltage at which saturationDrainCurrent is specified, in V, signed as printed. |
| `gateSourceCutoffVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_GS(off) / V_P / V_GSC: gate-source voltage at which the drain current falls to cutoffDrainCurrent, in V, SIGNED as printed (-1.5..-0.9 V for an n-channel part). |
| `cutoffDrainCurrent` | number | No | Drain current that defines gateSourceCutoffVoltage, in A (0.1 uA = 1e-7). (exclusiveMinimum 0) |
| `cutoffDrainSourceVoltage` | number | No | Drain-source voltage at which gateSourceCutoffVoltage is specified, in V, signed as printed. |
| `transconductance` | array of [transconductance](#jfettransconductance) | No | g_fs / g_m at each printed bias (see jfetTransconductance). (minItems 1) |
| `onResistance` | [dimensionWithTolerance](#dimensionwithtolerance) | No | r_DS(on) at V_GS = 0 (switch JFETs, SiC JFETs), in Ohm. Same name as the mosfet field. |
| `gateLeakageCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_GSS / I_G gate leakage (reverse gate current), in A (magnitude), at gateLeakageVoltage. |
| `gateLeakageVoltage` | number | No | Gate-source voltage at which gateLeakageCurrent is specified, in V, signed as printed. |
| `inputCapacitance` | number | No | C_iss, in F, at capacitanceMeasurementVds. Same name as the mosfet field. (exclusiveMinimum 0) |
| `reverseTransferCapacitance` | number | No | C_rss, in F. Same name as the mosfet field. (exclusiveMinimum 0) |
| `outputCapacitance` | number | No | C_oss, in F. Same name as the mosfet field. (exclusiveMinimum 0) |
| `capacitanceMeasurementVds` | number | No | Drain-source voltage at which the capacitances are specified, in V. Same name as the mosfet field. |
| `totalGateCharge` | number | No | Q_g of a power JFET, in C. Same name as the mosfet field. (exclusiveMinimum 0) |
| `powerDissipation` | number | No | P_D maximum, in W. (exclusiveMinimum 0) |
| `voltageNoiseDensity` | number | No | Input-referred voltage noise density e_n, in V/sqrt(Hz). Same name and unit as AAS amplifierCommon.voltageNoiseDensity and bjt.json, so one query covers op amps, matched BJTs and JFETs. Typical column. (minimum 0) |
| `voltageNoiseDensityFrequency` | number | No | Frequency at which voltageNoiseDensity is specified, in Hz. (exclusiveMinimum 0) |
| `voltageNoiseDensityDrainCurrent` | number | No | Drain current at which voltageNoiseDensity is specified, in A (a JFET's e_n falls with I_D). (exclusiveMinimum 0) |
| `currentNoiseDensity` | number | No | Input current noise density i_n, in A/sqrt(Hz) (the AAS name). Typical column. (minimum 0) |
| `currentNoiseDensityFrequency` | number | No | Frequency at which currentNoiseDensity is specified, in Hz. (exclusiveMinimum 0) |

### jfetTransconductance

`jfet.json#/$defs/transconductance` — g_fs / g_m at one bias (full conduction V_GS = 0 and an
operating current are both printed, each an entry).

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `transconductance` | [dimensionWithTolerance](#dimensionwithtolerance) | **Yes** | g_fs / g_m, in S. |
| `drainCurrent` | number | No | Drain current of the test, in A (magnitude). Absent with gateSourceVoltage 0 = full conduction. (exclusiveMinimum 0) |
| `gateSourceVoltage` | number | No | Gate-source voltage of the test, in V, signed as printed (0 for full conduction). |
| `drainSourceVoltage` | number | No | Drain-source voltage of the test, in V, signed as printed. |

### jfetDie

`jfet.json#/$defs/die` — same shape as [thyristorDie](#thyristordie) with the JFET electrical
block ([jfetElectrical](#jfetelectrical)) per die.

### jfetMatching

`jfet.json#/$defs/matching` — one matching specification between the die of a dual (LSK389,
U401-U406), the [bjtMatching](#bjtmatching) pattern. Closed; at least one quantity is required.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `dies` | array of string | No | Names (dies[].name) of the die related. Absent = any two die of the part. (minItems 2) |
| `gateSourceVoltageMatch` | [dimensionWithTolerance](#dimensionwithtolerance) | No | \|V_GS1 - V_GS2\| at equal drain current (the pair's offset), in V. |
| `gateSourceVoltageMatchDrift` | [dimensionWithTolerance](#dimensionwithtolerance) | No | Temperature drift of the V_GS match, in V/K. |
| `saturationDrainCurrentMatch` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_DSS match \|1 - I_DSS1/I_DSS2\| as a fraction. |
| `transconductanceMatch` | [dimensionWithTolerance](#dimensionwithtolerance) | No | g_fs match \|1 - g_fs1/g_fs2\| as a fraction. |
| `gateCurrentMatch` | [dimensionWithTolerance](#dimensionwithtolerance) | No | \|I_G1 - I_G2\|, in A. |
| `testDrainCurrent` | number | No | Drain current per die at which the matching is specified, in A. (exclusiveMinimum 0) |
| `testDrainGateVoltage` | number | No | Drain-gate voltage at which the matching is specified, in V. |
| `testTemperature` | number | No | Ambient temperature of the test, in degC. |

See `examples/12_jfet_jfe150.json`.

---

## Optocoupler Sections

**File**: `schemas/optocoupler.json` (`$defs`)

LED input, photo-detector output, galvanic isolation barrier. `part.subType` is the OUTPUT stage:
`phototransistor` | `photodarlington` | `logicOutput` | `gateDriver` | `photoThyristor` |
`photovoltaic` | `linear` (`$defs/subType`, the anchor of the requirement-side `outputType`).
Optical gate-drive couplers (TLP250, HCPL-3120, ACPL-332J) are `gateDriver` here. Boundaries: a part
the vendor sells as a PhotoMOS / photorelay / solid-state relay is an EMAS relay (technology
`solidState`); an optical isolation amplifier (TLP78xx) is CTAS; magnetic and capacitive isolators are
AAS / CTAS. `part.technology` is the material of the output (detector) die.

`datasheetInfo`: `part` and `electrical` required (no `dies[]`). Channels, not die: a multi-channel
part states `electrical.numberOfChannels` and every value is per channel; `part.dieConfiguration` and
`part.internalConnection` are refused (`{"not": {}}`). Rules:

- `electrical.isolation.withstandVoltageRms` (V_ISO) is **required** — every optocoupler datasheet prints it.
- `phototransistor` / `photodarlington` require `collectorEmitterVoltage` + `currentTransferRatio`.
- The bipolar-output fields (`collectorEmitterVoltage`, `emitterCollectorVoltage`, `collectorCurrent`,
  `collectorPeakCurrent`, `collectorDarkCurrent`, `saturationVoltage`, `currentTransferRatio`) are
  refused on every other output.
- `zeroCrossing` and `peakBlockingVoltage` are `photoThyristor` only.

**CTR is a fraction** (100 % = 1.0), like `dissipationFactor`. The schema cannot tell 100 (percent)
from 1.0 (fraction); the TAS ingest gate bounds `currentTransferRatio` instead.

### optocouplerElectrical

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `numberOfChannels` | integer | No | Number of identical coupler channels in the package. Absent = 1. (minimum 1) |
| `inputForwardCurrentMax` | number | No | I_F absolute maximum continuous LED forward current, in A. (exclusiveMinimum 0) |
| `inputReverseVoltageMax` | number | No | V_R absolute maximum LED reverse voltage, in V. (exclusiveMinimum 0) |
| `inputSurgeCurrent` | number | No | I_FSM LED forward surge current, in A, for inputSurgeCurrentDuration. (exclusiveMinimum 0) |
| `inputSurgeCurrentDuration` | number | No | Pulse duration of inputSurgeCurrent, in s. (exclusiveMinimum 0) |
| `inputPowerDissipation` | number | No | LED power dissipation P_diss, in W. (exclusiveMinimum 0) |
| `inputForwardVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_F, in V, at inputForwardVoltageCurrent. |
| `inputForwardVoltageCurrent` | number | No | Forward current at which inputForwardVoltage is specified, in A. (exclusiveMinimum 0) |
| `inputThresholdCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | Input threshold current I_FT / I_FLH / I_FT(on) of a logicOutput, gateDriver or photoThyristor coupler: the LED current that guarantees the output switches, in A (the guarantee is the maximum). |
| `collectorEmitterVoltage` | number | No | V_CEO absolute maximum of a transistor output, in V. (exclusiveMinimum 0) |
| `emitterCollectorVoltage` | number | No | V_ECO absolute maximum of a transistor output, in V. (exclusiveMinimum 0) |
| `collectorCurrent` | number | No | I_C absolute maximum continuous output current of a transistor output, in A. (exclusiveMinimum 0) |
| `collectorPeakCurrent` | number | No | I_CM peak output current of a transistor output, in A. (exclusiveMinimum 0) |
| `collectorDarkCurrent` | [dimensionWithTolerance](#dimensionwithtolerance) | No | I_CEO (dark current) of a transistor output, in A, at collectorDarkCurrentVce. |
| `collectorDarkCurrentVce` | number | No | Collector-emitter voltage at which collectorDarkCurrent is specified, in V. (exclusiveMinimum 0) |
| `saturationVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V_CE(sat) of a transistor output, in V, at saturationVoltageForwardCurrent / saturationVoltageCollectorCurrent. |
| `saturationVoltageForwardCurrent` | number | No | LED forward current of the saturationVoltage test, in A. (exclusiveMinimum 0) |
| `saturationVoltageCollectorCurrent` | number | No | Collector current of the saturationVoltage test, in A. (exclusiveMinimum 0) |
| `currentTransferRatio` | [dimensionWithTolerance](#dimensionwithtolerance) | No | CTR = I_C / I_F as a FRACTION (a 100..200 % bin is minimum 1.0, maximum 2.0), at currentTransferRatioForwardCurrent and currentTransferRatioVce. A CTR-binned part (VO617A-3) is catalogued per orderable bin with that bin's limits. |
| `currentTransferRatioForwardCurrent` | number | No | LED forward current of the CTR test, in A. (exclusiveMinimum 0) |
| `currentTransferRatioVce` | number | No | Collector-emitter voltage of the CTR test, in V. (exclusiveMinimum 0) |
| `outputPowerDissipation` | number | No | Output-side power dissipation, in W. (exclusiveMinimum 0) |
| `totalPowerDissipation` | number | No | P_tot of the coupler (both sides), in W. (exclusiveMinimum 0) |
| `peakBlockingVoltage` | number | No | V_DRM of a photoThyristor output, in V. (exclusiveMinimum 0) |
| `zeroCrossing` | boolean | No | photoThyristor output only: true for a zero-cross (zero-voltage-switching) triac driver, false for a random-phase one. |
| `outputPeakCurrent` | number | No | I_OPK peak output current of a gateDriver output stage (source or sink, the lower of the two as printed), in A. (exclusiveMinimum 0) |
| `supplyVoltageMax` | number | No | Absolute maximum output-side supply voltage V_CC (logicOutput, gateDriver), in V. (exclusiveMinimum 0) |
| `propagationDelayHighToLow` | [dimensionWithTolerance](#dimensionwithtolerance) | No | t_PHL, in s. |
| `propagationDelayLowToHigh` | [dimensionWithTolerance](#dimensionwithtolerance) | No | t_PLH, in s. |
| `dataRate` | number | No | Maximum signalling rate of a logicOutput coupler, in bit/s (Bd as printed). (exclusiveMinimum 0) |
| `riseTime` | [dimensionWithTolerance](#dimensionwithtolerance) | No | Output rise time t_r, in s, in the test circuit of switchingLoadResistance. |
| `fallTime` | [dimensionWithTolerance](#dimensionwithtolerance) | No | Output fall time t_f, in s. |
| `turnOnTime` | [dimensionWithTolerance](#dimensionwithtolerance) | No | t_on, in s. |
| `turnOffTime` | [dimensionWithTolerance](#dimensionwithtolerance) | No | t_off, in s. |
| `switchingLoadResistance` | number | No | Load resistor R_L of the switching-time test circuit, in Ohm (the times scale with it). (exclusiveMinimum 0) |
| `switchingSaturated` | boolean | No | true when the switching times are the SATURATED test (output driven into saturation), false for the non-saturated (linear) test. Vendors print both; the record carries one set. |
| `cutoffFrequency` | number | No | Small-signal cut-off frequency f_ctr / f_c, in Hz. (exclusiveMinimum 0) |
| `isolation` | PEAS [isolationRating](#optocoupler-isolation) | **Yes** | Galvanic-isolation barrier rating (the shared PEAS isolationRating, hoisted from CTAS with its key names). V_ISO -> withstandVoltageRms + withstandVoltageDuration, V_IORM -> workingVoltage, V_IOTM -> transientVoltage, C_C / C_IO coupling capacitance -> barrierCapacitance, CMTI -> cmti. |

### Optocoupler isolation

`electrical.isolation` is the shared PEAS `utils.json#/$defs/isolationRating` (the CTAS key names,
hoisted to PEAS so CTAS controllers, AAS isolators and SAS optocouplers use one definition), at the
same place AAS and CTAS put it. Datasheet mapping: V_ISO -> `withstandVoltageRms` +
`withstandVoltageDuration` (+ the standard), V_IORM -> `workingVoltage`, V_IOTM -> `transientVoltage`,
C_C / C_IO -> `barrierCapacitance`, CMTI -> `cmti`, plus creepage / clearance / insulation thickness /
CTI / material group / pollution degree. See the PEAS schema reference for the full field list and
`examples/11_optocoupler_vo617a_3.json`.

---

## Power Module Sections

**File**: `schemas/module.json` (`$defs`)

A power module is a multi-die part: several switch positions (plus optional co-pack diodes
and an NTC) in one isolated package. The circuit arrangement is carried by
`electrical.topology`, the die technology by `electrical.switchTechnology`, and the
per-switch ratings **reuse the discrete device shapes by `$ref`** — same physics, same field
names. `datasheetInfo` carries the same `part` / `thermal` / `provenance` sections as the
other devices (`part.subType`, when present, mirrors `electrical.topology`); `mechanical` is
module-specific (adds `terminalStyle`). No `modelParams` section is defined (a single
`.model` card cannot describe a multi-die module); the device-body `spiceModel` remains
available for subcircuit-sourced parts.

For **baseplate-less modules** (e.g. Infineon EasyPACK) the datasheet quotes a
junction-to-heatsink R_th(j-s); store it in `thermal.thermalResistanceJunctionCase` (the
module bottom *is* the heatsink interface). R_th values are per switch position.

### moduleElectrical

Closed object. **Required**: `topology`, `switchTechnology`, `numberOfSwitches`, `switch`.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `topology` | string (enum) | **Yes** | -- | Circuit arrangement of the dies — see [moduleTopology](#moduletopology) |
| `switchTechnology` | string (enum) | **Yes** | -- | Die technology: `siliconIgbt`, `siliconMosfet`, `sicMosfet`, `ganHemt`. Implies `part.technology` (`Si`/`SiC`/`GaN`) |
| `numberOfSwitches` | integer (>= 1) | **Yes** | -- | Main switch positions (2 = half-bridge, 4 = full-bridge, 6 = sixpack). Paralleled dies in one position count as one switch |
| `switch` | [mosfetElectrical](#mosfetelectrical) or [igbtElectrical](#igbtelectrical) | **Yes** | -- | Ratings of ONE switch position. The shape is pinned by `switchTechnology` (`if`/`then`): `siliconIgbt` -> `igbt.json#/$defs/electrical`; `siliconMosfet` / `sicMosfet` / `ganHemt` -> `mosfet.json#/$defs/electrical` |
| `diode` | [diodeElectrical](#diodeelectrical) | No | -- | Separate co-pack / freewheeling diode ratings per switch position (typical for IGBT modules). MOSFET modules that only characterize the body diode use `switch.bodyDiode*` instead |
| `switchingEnergy` | [moduleSwitchingEnergy](#moduleswitchingenergy) | No | -- | Loop-measured per-switch E_on / E_off with test conditions |
| `isolationVoltage` | number | No | V | V_isol baseplate-to-terminals, RMS at 50/60 Hz for 1 min |
| `ntcIntegrated` | boolean | No | -- | Whether the module integrates an NTC thermistor |
| `ntcRatedResistance` | number | No | Ohm | NTC R25 at 25 C. **Only allowed when `ntcIntegrated` is `true`** |
| `ntcBValue` | number | No | K | NTC B-value (B25/100 preferred). **Only allowed when `ntcIntegrated` is `true`** |

### moduleSwitchingEnergy

Closed; no required fields. Module switching energies are measured in the module's own
commutation loop (they depend on the module stray inductance), so they are module-level
data — this block is their canonical home. For IGBT-technology modules, leave the
`switch` block's own `turnOnEnergy` / `turnOffEnergy` unset.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `turnOnEnergy` | number | No | J | E_on per pulse at the stated test conditions |
| `turnOffEnergy` | number | No | J | E_off per pulse at the stated test conditions |
| `reverseRecoveryEnergy` | number | No | J | E_rr of the commutating diode per pulse |
| `testVoltage` | number | No | V | DC-link voltage of the switching test |
| `testCurrent` | number | No | A | Switched current of the switching test |
| `junctionTemperature` | number | No | C | Junction temperature of the switching test |

### moduleMechanical

Same shape as the shared [mechanical](#mechanical) section (PEAS `datasheetInfoMechanical`
plus `case`), with one extra field:

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `terminalStyle` | string (enum) | No | Power/auxiliary terminal technology: `screw` (SEMITRANS, 62 mm), `pressFit` (Infineon Easy PressFIT), `solderPin` (Vincotech flow), `spring` (MiniSKiiP/SKiiP), `busbar` |

### moduleCurves

All fields are PEAS [curve](#curve) objects, all optional, per switch position.

| Field | X-axis | Y-axis | Description |
|-------|--------|--------|-------------|
| `rdsOnVsTj` | T_j (C) | R_DS(on) (Ohm) | On-resistance vs junction temperature (FET-die modules) |
| `vceVsIc` | I_C (A) | V_CE(sat) (V) | Saturation voltage vs collector current (IGBT-die modules) |
| `eonVsIc` | I (A) | E_on (J) | Turn-on energy vs switched current |
| `eoffVsIc` | I (A) | E_off (J) | Turn-off energy vs switched current |
| `diodeVf` | I_F (A) | V_F (V) | Co-pack / body diode forward characteristic |
| `thermalImpedance` | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |
| `soa` | V (V) | I (A) | Safe Operating Area boundary |

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
| `deviceType` | string (enum) | **Yes** | `"mosfet"`, `"diode"`, `"igbt"`, `"bjt"`, `"thyristor"`, `"jfet"`, `"optocoupler"`, `"module"` — selects the per-type branch below |
| `maximumJunctionTemperature` | number | No | Maximum allowed junction temperature, in Celsius |
| `maximumPowerDissipation` | number (>= 0) | No | Maximum allowed continuous power dissipation, in W |
| `role` | string (enum) | No | Semiconductor role in the converter: `mainSwitch`, `synchronousRectifier`, `freewheelingDiode`, `clampDiode`, `bootstrapDiode`, `lineRectifier`, `bridgeRectifier`, `bodyDiode`, `inrushLimiter`, `esdProtection`, `tvs`, `zenerReference`, `smallSignal`, `acSwitch`, `overvoltageProtection`, `isolatedFeedback` |
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
| `mosfet` | `channel` (`nChannel`/`pChannel`, optional; absent = either), `ratedDrainSourceVoltage` (V), `ratedContinuousDrainCurrent` (A), `maximumOnResistance` (Ohm), `maximumGateCharge` (C), `maximumOutputCapacitance` (F), `maximumSwitchingLossPerCycle` (J), `maximumReverseRecoveryCharge` (C) |
| `diode` | `ratedReverseVoltage` (V), `ratedForwardCurrent` (A), `maximumForwardVoltage` (V), `maximumReverseRecoveryCharge` (C), `maximumReverseRecoveryTime` (s), `maximumReverseLeakage` (A) |
| `igbt` | `ratedCollectorEmitterVoltage` (V), `ratedCollectorCurrent` (A), `maximumSaturationVoltage` (V), `maximumSwitchingLossPerCycle` (J) |
| `bjt` | `polarity` (`npn`/`pnp`, optional; absent = either), `ratedCollectorEmitterVoltage` (V), `ratedCollectorCurrent` (A), `maximumSaturationVoltage` (V), `minimumDcCurrentGain` (--) |
| `thyristor` | `thyristorType` (enum, `$ref`s the part-side anchor `thyristor.json#/$defs/subType`), `ratedOffStateVoltage` (V, minimum V_DRM), `ratedRmsOnStateCurrent` (A, minimum I_T(RMS)), `maximumGateTriggerCurrent` (A, worst quadrant for a triac), `maximumBreakoverVoltage` (V) |
| `jfet` | `channel` (enum, anchor `jfet.json#/$defs/subType`), `ratedDrainSourceVoltage` (V, minimum V_DS or V_GD), `minimumSaturationDrainCurrent` (A, I_DSS), `maximumVoltageNoiseDensity` (V/sqrt(Hz)) |
| `optocoupler` | `outputType` (enum, anchor `optocoupler.json#/$defs/subType`), `minimumIsolationVoltage` (V RMS, V_ISO), `minimumCurrentTransferRatio` (fraction), `ratedCollectorEmitterVoltage` (V), `numberOfChannels` (integer >= 1) |
| `module` | `moduleTopology` (enum, `$ref`s the part-side anchor `module.json#/$defs/topology` — named `moduleTopology` because the PEAS base already carries a converter-level `topology`), `allowedSwitchTechnologies` (array, anchor `module.json#/$defs/switchTechnology`), `ratedBlockingVoltage` (V, per switch), `ratedContinuousCurrent` (A, per switch), `maximumSwitchingLossPerCycle` (J, per switch), `minimumIsolationVoltage` (V), `requireIntegratedNtc` (boolean) |

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
top-level field: `mosfet`, `diode`, `igbt`, `bjt`, `thyristor`, `jfet`, `optocoupler`, or
`module`. The only `deviceType` enum in SAS is in `inputs.designRequirements` (the same eight
values), where it states the *required* device type.

### technology

Semiconductor material technology (`part.technology`, required).

| Value | Description |
|-------|-------------|
| `"Si"` | Silicon |
| `"SiC"` | Silicon Carbide |
| `"GaN"` | Gallium Nitride |
| `"GaAs"` | Gallium Arsenide |
| `"Ge"` | Germanium |

### moduleTopology

`module` circuit arrangement (`electrical.topology`, required; also the `moduleTopology`
requirement field and the module `part.subType` narrowing). Value set derived from the
vendor survey (2026-07-02): Digi-Key's IGBT-module **Configuration** parametric filter and
the Vincotech by-topology catalog.

| Value | Vendor filter names covered |
|-------|-----------------------------|
| `"singleSwitch"` | Single, Single Switch (one switch + freewheeling diode) |
| `"chopper"` | Single Chopper, Dual Brake Chopper (switch + series diode) |
| `"boost"` | Boost Chopper, Dual Boost Chopper; Vincotech Booster |
| `"buck"` | Buck Chopper, Dual Buck Chopper |
| `"halfBridge"` | Half Bridge, Half Bridge Inverter |
| `"fullBridge"` | Full Bridge, Full Bridge Inverter; H-bridge / fourpack |
| `"dualCommonSource"` | Dual Common Source; Dual Common Emitter (IGBT) |
| `"dualIndependent"` | 2 Independent, Dual, Dual Parallel (isolated positions) |
| `"asymmetricBridge"` | Asymmetrical Bridge (SRM drives) |
| `"sixpack"` | Three Phase Inverter (3x half-bridge) |
| `"sixpackWithBrake"` | Three Phase Inverter with Brake; sevenpack |
| `"pim"` | Vincotech PIM (CIB): rectifier + brake + sixpack |
| `"threeLevel"` | Three Level Inverter, T-Type; NPC / MNPC / ANPC / FC |

### moduleSwitchTechnology

`module` die technology (`electrical.switchTechnology`, required; also the
`allowedSwitchTechnologies` requirement items). Combines process and device kind; implies
`part.technology` and pins the `switch` block shape.

| Value | part.technology | switch shape |
|-------|-----------------|--------------|
| `"siliconIgbt"` | `Si` | [igbtElectrical](#igbtelectrical) |
| `"siliconMosfet"` | `Si` | [mosfetElectrical](#mosfetelectrical) |
| `"sicMosfet"` | `SiC` | [mosfetElectrical](#mosfetelectrical) |
| `"ganHemt"` | `GaN` | [mosfetElectrical](#mosfetelectrical) |

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
| `"switching"` | diode | Small-signal / high-speed switching diode (e.g. 1N4148, BAV99) |
| `"pin"` | diode | PIN diode (RF switching / attenuator; thick intrinsic layer) |
| `"zener"` | diode | Zener voltage reference diode |
| `"tvs"` | diode | Transient Voltage Suppressor |
| `"esd"` | diode | ESD protection diode |
| `"npn"` | bjt | NPN bipolar transistor |
| `"pnp"` | bjt | PNP bipolar transistor |
| `"scr"` | thyristor | Silicon controlled rectifier (unidirectional, gate-triggered) |
| `"triac"` | thyristor | Bidirectional gate-triggered thyristor (MT1/MT2; 3Q and 4Q) |
| `"sidac"` | thyristor | Bidirectional voltage-triggered switch without a gate |
| `"diac"` | thyristor | Low-current bidirectional trigger diode |
| `"surgeProtector"` | thyristor | Thyristor surge protective device (TISP, SIDACtor, SMCP, Trisil) |
| `"nChannel"` / `"pChannel"` | jfet | JFET channel type |
| `"phototransistor"` | optocoupler | Bipolar phototransistor output |
| `"photodarlington"` | optocoupler | Photodarlington output |
| `"logicOutput"` | optocoupler | Photodiode + amplifier, digital output (6N137, TLP2361) |
| `"gateDriver"` | optocoupler | Optical IGBT/MOSFET gate driver (TLP250, HCPL-3120) |
| `"photoThyristor"` | optocoupler | Photo-SCR / photo-triac output, incl. zero-cross triac drivers |
| `"photovoltaic"` | optocoupler | Photovoltaic output (floating gate voltage) |
| `"linear"` | optocoupler | Photodiode-output analog coupler (HCNR201, IL300) |
| [moduleTopology](#moduletopology) values | module | Mirrors `electrical.topology`; prefer omitting `subType` |

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
