# SAS-RFC 0003 — TVS/ESD pulse ratings state their waveform

- **Status:** ACCEPTED 2026-10-17 (owner approval) and implemented the same day.
- **Type:** Additive (non-breaking). Four optional fields and one `dependentRequired` block on
  `diode.json#/$defs/electrical`; the object stays closed (`additionalProperties: false`).
- **Depends on:** PEAS-RFC 0003 (`utils.json#/$defs/surgeWaveform`). Module → PEAS only.

## Problem

`peakPulseCurrent`, `peakPulsePower` and `clampingVoltage` had no field for the test waveform or
the test current, and their descriptions contradicted each other. In the live catalogue the TVS
trio is mostly one 10/1000 us pulse and ESD rows are mostly 8/20 us, but no record said which.
Parts rated only at 8/20 us (e.g. Bourns PTVS 1–20 kA, CDSOD323 350 W at 8/20 us) could not be
stored without mixing incomparable ratings.

## Change

| field | type | meaning |
|---|---|---|
| `clampingCurrent` | number > 0, A | peak test current at which `clampingVoltage` is specified (same name and meaning as RAS varistor) |
| `clampingWaveform` | PEAS `surgeWaveform` | impulse at which `clampingVoltage` was measured |
| `peakPulseCurrentWaveform` | PEAS `surgeWaveform` | impulse the `peakPulseCurrent` rating is stated at |
| `peakPulsePowerWaveform` | PEAS `surgeWaveform` | impulse the `peakPulsePower` rating is stated at |

```json
"dependentRequired": {
    "clampingCurrent": ["clampingVoltage"],
    "clampingWaveform": ["clampingVoltage"],
    "peakPulseCurrentWaveform": ["peakPulseCurrent"],
    "peakPulsePowerWaveform": ["peakPulsePower"]
}
```

A condition can never be stored without the value it qualifies. The reverse (a value requires its
waveform) is NOT enforced: absent means "not stated", never a default, so the legacy rows stay
valid. The `tvs`/`esd` required sets are unchanged. Descriptions of the three existing scalars
were rewritten to point at their condition fields.

## Rejected alternatives

- A graded `pulseRatings[]` table: a breaking restructure of ~14k rows for a need no held part has
  (each publishes at most one waveform per quantity). Can be added later, additively.
- `{frontTime, timeToHalfValue}` in seconds: breaks the RAS strings, makes "the 8/20 rating" a
  float-equality query, cannot express TLP.

## Data impact

0 of 34,746 live diode rows become invalid (0 invalid before and after, 2026-10-17).

## Follow-ups (not in this RFC)

- Stamping waveforms on the legacy TVS/ESD rows, from each row's own datasheet only.
- Possibly making a waveform required for NEW rows once coverage is measured (needs its own approval).
- Typical vs maximum `clampingVoltage` and TVS polarity have no field yet.

## Tests and example

`examples/05_tvs_ptvs1_022c_h.json` (Bourns PTVS1-022C-H, values read from the PTVS1-xxxC-H
datasheet). `tests/test_schemas.py` covers: the example validates; each waveform without its value
is rejected (`dependentRequired`); `clampingCurrent` without `clampingVoltage` is rejected; unknown
waveform strings are rejected; `clampingCurrent` must be > 0; values without waveforms stay valid.
With the schema change reverted the negative tests fail.
