# SAS Schema Reference

Complete field-by-field documentation for the Semiconductor Agnostic Structure schema.

**Schema version**: JSON Schema 2020-12
**Base URI**: `http://openconverters.com/schemas/SAS/`

---

## Table of Contents

- [Top-Level Structure (SAS.json)](#top-level-structure)
- [Semiconductor Object (semiconductor.json)](#semiconductor-object)
- [Shared Sections](#shared-sections)
  - [part](#part)
  - [thermal](#thermal)
  - [mechanical](#mechanical)
  - [business](#business)
- [MOSFET Sections](#mosfet-sections)
  - [mosfetElectrical](#mosfetelectrical)
  - [mosfetModelParams](#mosfetmodelparams)
  - [mosfetCurves](#mosfetcurves)
- [Diode Sections](#diode-sections)
  - [diodeElectrical](#diodeelectrical)
  - [diodeModelParams](#diodemodelparams)
  - [diodeCurves](#diodecurves)
- [IGBT Sections](#igbt-sections)
  - [igbtElectrical](#igbtelectrical)
  - [igbtModelParams](#igbtmodelparams)
  - [igbtCurves](#igbtcurves)
- [BJT Sections](#bjt-sections)
  - [bjtElectrical](#bjtelectrical)
- [Utility Types (utils.json)](#utility-types)
  - [dimensionWithTolerance](#dimensionwithtolerance)
  - [curve](#curve)
- [Enum Reference](#enum-reference)

---

## Top-Level Structure

**File**: `schemas/SAS.json`

The top-level SAS document wraps a semiconductor component with its design context.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `inputs` | object | Yes | Design requirements and operating points for this semiconductor |
| `semiconductor` | [semiconductor](#semiconductor-object) | Yes | The semiconductor component data |
| `outputs` | object or array | Yes | Computed results (conduction loss, switching loss, thermal, etc.) |

`additionalProperties: false` -- no extra fields allowed at the top level.

---

## Semiconductor Object

**File**: `schemas/semiconductor.json`

The root semiconductor object. Contains manufacturer info and optional distributor info.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `manufacturerInfo` | [manufacturerInfo](#manufacturerinfo) | Yes | Manufacturer-specific information |
| `distributorsInfo` | array of [distributorInfo](#distributorinfo) | No | Where to buy this component |

`additionalProperties: false`

### manufacturerInfo

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | No | Manufacturer name (e.g., "Infineon", "STMicroelectronics") |
| `reference` | string | No | Manufacturer part number |
| `status` | string (enum) | No | Production status. Values: `"production"`, `"nrnd"`, `"obsolete"`, `"preview"` |
| `datasheetUrl` | string (URI) | No | URL to the datasheet PDF |
| `datasheetInfo` | [datasheetInfo](#datasheetinfo) | Yes | All information extracted from the datasheet |

### distributorInfo

Defined in `utils.json`.

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `name` | string | -- | Distributor name (e.g., "Digi-Key", "Mouser") |
| `reference` | string | -- | Distributor part number |
| `link` | string | -- | URL to product page |
| `cost` | number | -- | Unit cost |
| `stock` | integer | -- | Available stock |

### datasheetInfo

The central structure that holds all datasheet-extracted data. Uses a `oneOf` discriminator on `part.deviceType` to select device-specific sections.

**Shared properties** (present for all device types):

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `part` | [part](#part) | Yes | Basic part identification |
| `thermal` | [thermal](#thermal) | No | Thermal characteristics |
| `mechanical` | [mechanical](#mechanical) | No | Mechanical specifications |
| `business` | [business](#business) | No | Commercial information |

**Device-specific properties** (selected by `oneOf` based on `part.deviceType`):

| deviceType | electrical | modelParams | curves | Required |
|------------|-----------|-------------|--------|----------|
| `"mosfet"` | [mosfetElectrical](#mosfetelectrical) | [mosfetModelParams](#mosfetmodelparams) | [mosfetCurves](#mosfetcurves) | electrical |
| `"diode"` | [diodeElectrical](#diodeelectrical) | [diodeModelParams](#diodemodelparams) | [diodeCurves](#diodecurves) | electrical |
| `"igbt"` | [igbtElectrical](#igbtelectrical) | [igbtModelParams](#igbtmodelparams) | [igbtCurves](#igbtcurves) | electrical |
| `"bjt"` | [bjtElectrical](#bjtelectrical) | -- | -- | electrical |

`additionalProperties: false`

---

## Shared Sections

### part

Basic part identification, shared across all semiconductor types.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `partNumber` | string | Yes | -- | Full part number (e.g., "IPB017N10N5") |
| `series` | string or null | No | -- | Product family (e.g., "OptiMOS 5") |
| `deviceType` | string (enum) | Yes | -- | `"mosfet"`, `"diode"`, `"igbt"`, `"bjt"`, `"jfet"` |
| `technology` | string (enum) | Yes | -- | `"Si"`, `"SiC"`, `"GaN"`, `"GaAs"` |
| `subType` | string or null (enum) | No | -- | Device subtype (see [subType values](#subtype-values)) |
| `case` | string | Yes | -- | Package code (e.g., "TO-220", "SOT-23", "TO-263-3 (D2PAK)") |
| `matchcodeDescription` | string or null | No | -- | Additional description or matchcode |

`additionalProperties: false`

### thermal

Thermal characteristics, shared across all semiconductor types.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `thermalResistanceJunctionCase` | number | No | K/W | R_th(j-c) -- junction to case |
| `thermalResistanceJunctionAmbient` | number | No | K/W | R_th(j-a) -- junction to ambient |
| `thermalResistanceCaseSink` | number | No | K/W | R_th(c-s) -- case to heatsink |
| `junctionTemperatureMax` | number | No | Celsius | Maximum operating junction temperature |
| `junctionTemperatureMin` | number | No | Celsius | Minimum operating junction temperature |
| `fosterNetwork` | array | No | -- | Foster RC network for transient thermal impedance |

#### fosterNetwork items

Each element in the Foster network array:

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `resistance` | number | Yes | K/W | Thermal resistance of this RC stage |
| `timeConstant` | number | Yes | seconds | Time constant of this RC stage |

### mechanical

Mechanical specifications, shared across all semiconductor types.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `assemblyType` | string (enum) | No | -- | `"SMT"`, `"THT"`, `"Chassis"` |
| `case` | string | No | -- | Package name (e.g., "TO-220", "SOT-23") |
| `length` | number | No | meters | Package length |
| `width` | number | No | meters | Package width |
| `height` | number | No | meters | Package height |
| `weight` | number | No | kg | Package weight |

### business

Commercial information, shared across all semiconductor types.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `packaging` | string or null | No | -- | Packaging type (e.g., "Tape and Reel", "Tube", "Tray") |
| `vpe` | integer or null | No | -- | Units per package |
| `moq` | integer or null | No | -- | Minimum order quantity |
| `leadTime` | number or null | No | weeks | Lead time |
| `stock` | integer or null | No | -- | Available stock |
| `cost` | number or null | No | -- | Unit cost |

---

## MOSFET Sections

### mosfetElectrical

Electrical characteristics specific to MOSFETs (Si, SiC, GaN).

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
| `gateThresholdVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V | V_GS(th) with min/nom/max |
| `inputCapacitance` | number | No | F | C_iss -- input capacitance |
| `outputCapacitance` | number | No | F | C_oss -- output capacitance |
| `reverseTransferCapacitance` | number | No | F | C_rss -- reverse transfer capacitance |
| `capacitanceMeasurementVds` | number | No | V | V_DS at which capacitances are measured |
| `totalGateCharge` | number | No | C | Q_g -- total gate charge |
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

SPICE model parameters for MOSFET simulation.

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

Characteristic curves digitized from MOSFET datasheets.

| Field | Type | Required | X-axis | Y-axis | Description |
|-------|------|----------|--------|--------|-------------|
| `rdsOnVsTj` | [curve](#curve) | No | T_j (C) | R_DS(on) (Ohm) | On-resistance vs junction temperature |
| `rdsOnVsId` | [curve](#curve) | No | I_D (A) | R_DS(on) (Ohm) | On-resistance vs drain current |
| `cissVsVds` | [curve](#curve) | No | V_DS (V) | C_iss (F) | Input capacitance vs drain-source voltage |
| `cossVsVds` | [curve](#curve) | No | V_DS (V) | C_oss (F) | Output capacitance vs drain-source voltage |
| `crssVsVds` | [curve](#curve) | No | V_DS (V) | C_rss (F) | Reverse transfer capacitance vs V_DS |
| `gateCharge` | [curve](#curve) | No | Q_g (C) | V_GS (V) | Gate voltage vs gate charge |
| `bodyDiodeVf` | [curve](#curve) | No | V_SD (V) | I_SD (A) | Body diode forward voltage vs current |
| `soa` | [curve](#curve) | No | V_DS (V) | I_D (A) | Safe Operating Area boundary |
| `thermalImpedance` | [curve](#curve) | No | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |

---

## Diode Sections

### diodeElectrical

Electrical characteristics specific to diodes.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `reverseVoltage` | number | **Yes** | V | V_RRM -- repetitive peak reverse voltage |
| `forwardCurrent` | number | **Yes** | A | I_F(AV) -- average forward current |
| `surgeCurrent` | number | No | A | I_FSM -- non-repetitive surge current |
| `forwardVoltage` | number | **Yes** | V | V_F -- forward voltage drop |
| `forwardVoltageAt` | number | No | A | I_F at which V_F is specified |
| `reverseLeakageCurrent` | number | No | A | I_R -- reverse leakage current |
| `reverseRecoveryTime` | number | No | s | t_rr -- reverse recovery time |
| `reverseRecoveryCharge` | number | No | C | Q_rr -- reverse recovery charge |
| `junctionCapacitance` | number | No | F | C_j -- junction capacitance |
| `junctionCapacitanceVr` | number | No | V | V_R at which C_j is measured |
| `powerDissipation` | number | No | W | P_D max |
| `clampingVoltage` | number | No | V | V_C at I_PP -- TVS clamping voltage |
| `breakdownVoltage` | [dimensionWithTolerance](#dimensionwithtolerance) | No | V | V_BR -- Zener/TVS breakdown voltage (min/nom/max) |
| `standoffVoltage` | number | No | V | V_WM -- TVS working standoff voltage |
| `peakPulseCurrent` | number | No | A | I_PP -- TVS peak pulse current |

### diodeModelParams

SPICE model parameters for diode simulation.

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

Characteristic curves digitized from diode datasheets.

| Field | Type | Required | X-axis | Y-axis | Description |
|-------|------|----------|--------|--------|-------------|
| `forwardVoltageVsCurrent` | [curve](#curve) | No | I_F (A) | V_F (V) | Forward voltage vs forward current |
| `forwardVoltageVsTj` | [curve](#curve) | No | T_j (C) | V_F (V) | Forward voltage vs junction temperature |
| `reverseCurrentVsVoltage` | [curve](#curve) | No | V_R (V) | I_R (A) | Reverse leakage vs reverse voltage |
| `capacitanceVsVoltage` | [curve](#curve) | No | V_R (V) | C_j (F) | Junction capacitance vs reverse voltage |
| `thermalImpedance` | [curve](#curve) | No | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |
| `soa` | [curve](#curve) | No | V_R (V) | I_F (A) | Safe Operating Area boundary |

---

## IGBT Sections

### igbtElectrical

Electrical characteristics specific to IGBTs.

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

SPICE model parameters for IGBT simulation.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `vto` | number | No | V | Threshold voltage |
| `kp` | number | No | A/V^2 | Transconductance parameter |
| `eon` | number | No | J | Turn-on energy |
| `eoff` | number | No | J | Turn-off energy |

### igbtCurves

Characteristic curves digitized from IGBT datasheets.

| Field | Type | Required | X-axis | Y-axis | Description |
|-------|------|----------|--------|--------|-------------|
| `vceVsIc` | [curve](#curve) | No | I_C (A) | V_CE(sat) (V) | Saturation voltage vs collector current |
| `eonVsIc` | [curve](#curve) | No | I_C (A) | E_on (J) | Turn-on energy vs collector current |
| `eoffVsIc` | [curve](#curve) | No | I_C (A) | E_off (J) | Turn-off energy vs collector current |
| `thermalImpedance` | [curve](#curve) | No | pulse width (s) | Z_th(j-c) (K/W) | Transient thermal impedance |
| `soa` | [curve](#curve) | No | V_CE (V) | I_C (A) | Safe Operating Area boundary |

---

## BJT Sections

### bjtElectrical

Electrical characteristics specific to BJTs. No `modelParams` or `curves` sections are defined for BJTs.

| Field | Type | Required | Unit | Description |
|-------|------|----------|------|-------------|
| `collectorEmitterVoltage` | number | **Yes** | V | V_CEO -- collector-emitter voltage (base open) |
| `collectorBasevoltage` | number | No | V | V_CBO -- collector-base voltage (emitter open) |
| `collectorCurrent` | number | **Yes** | A | I_C max -- maximum collector current |
| `dcCurrentGain` | [dimensionWithTolerance](#dimensionwithtolerance) | No | -- | h_FE -- DC current gain (min/nom/max) |
| `saturationVoltage` | number | No | V | V_CE(sat) -- collector-emitter saturation voltage |
| `transitionFrequency` | number | No | Hz | f_T -- gain-bandwidth product |
| `powerDissipation` | number | No | W | P_D max |

---

## Utility Types

**File**: `schemas/utils.json`

### dimensionWithTolerance

A value with tolerance bounds. At least one of the three fields must be present.

```json
{
    "minimum": 2.2,
    "nominal": 3.0,
    "maximum": 3.8
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `minimum` | number | At least one required | Minimum value |
| `nominal` | number | At least one required | Nominal (typical) value |
| `maximum` | number | At least one required | Maximum value |

Validation rule: `anyOf` -- at least one of `minimum`, `nominal`, or `maximum` must be provided.

**Used for**: gateThresholdVoltage (MOSFET, IGBT), breakdownVoltage (diode), dcCurrentGain (BJT).

### curve

X-Y data points representing a characteristic curve digitized from a datasheet.

```json
{
    "xData": [1, 5, 10, 25, 50, 80, 100],
    "yData": [40e-9, 10e-9, 5.5e-9, 2.8e-9, 1.5e-9, 0.9e-9, 0.7e-9]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `xData` | array of number | No | X-axis values |
| `yData` | array of number | No | Y-axis values (same length as xData) |

`additionalProperties: false`

The `xData` and `yData` arrays must have the same length. Each pair `(xData[i], yData[i])` represents one data point on the curve.

---

## Enum Reference

### deviceType

Identifies the semiconductor device category.

| Value | Description |
|-------|-------------|
| `"mosfet"` | Metal-Oxide-Semiconductor Field-Effect Transistor |
| `"diode"` | Diode (all subtypes) |
| `"igbt"` | Insulated-Gate Bipolar Transistor |
| `"bjt"` | Bipolar Junction Transistor |
| `"jfet"` | Junction Field-Effect Transistor |

### technology

Semiconductor material technology.

| Value | Description |
|-------|-------------|
| `"Si"` | Silicon |
| `"SiC"` | Silicon Carbide |
| `"GaN"` | Gallium Nitride |
| `"GaAs"` | Gallium Arsenide |

### subType

Device subtype. The valid values depend on `deviceType`:

| Value | Applicable deviceType | Description |
|-------|----------------------|-------------|
| `"nChannel"` | mosfet, igbt | N-channel MOSFET or N-channel IGBT |
| `"pChannel"` | mosfet | P-channel MOSFET |
| `"schottky"` | diode | Silicon Schottky diode |
| `"sicSchottky"` | diode | Silicon Carbide Schottky diode |
| `"ultrafast"` | diode | Ultrafast recovery diode |
| `"standard"` | diode | Standard recovery diode |
| `"zener"` | diode | Zener voltage reference diode |
| `"tvs"` | diode | Transient Voltage Suppressor |
| `"npn"` | bjt | NPN bipolar transistor |
| `"pnp"` | bjt | PNP bipolar transistor |
| `null` | any | Subtype not specified |

### assemblyType

Package mounting technology.

| Value | Description |
|-------|-------------|
| `"SMT"` | Surface Mount Technology |
| `"THT"` | Through-Hole Technology |
| `"Chassis"` | Chassis or screw-mounted |

### status

Production lifecycle status.

| Value | Description |
|-------|-------------|
| `"production"` | Currently in active production |
| `"nrnd"` | Not Recommended for New Designs |
| `"obsolete"` | Discontinued |
| `"preview"` | Pre-release / sampling |
