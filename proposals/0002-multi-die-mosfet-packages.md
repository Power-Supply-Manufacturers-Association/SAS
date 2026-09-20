# SAS-RFC 0002 — Multi-die MOSFET packages (duals and complementary pairs)

- **Status:** Proposed, awaiting owner decision. Nothing has been edited; no schema file was touched.
- **Type:** Additive (non-breaking) schema change.
- **Author:** drafted 2026-09-20
- **Created:** 2026-09-20
- **Depends on:** nothing new. This is the design for item 5 of **SAS-RFC 0001**
  ("Multi-die / modules / half-bridges — no representation at all; data resorts to
  `subType: "powerBlock"` on single-die shapes"), narrowed to the discrete two-die packages.
  Intra-SAS `$ref`s only (`mosfet.json` → `utils.json`), so no PEAS change and no
  cross-module edge.

## Summary

`mosfet.json` describes exactly one die. `datasheetInfo.required` is `["part", "electrical"]`
and `electrical.required` is
`["drainSourceVoltage", "onResistance", "continuousDrainCurrent", "gateThresholdVoltage", "totalGateCharge"]`
— five single-valued fields. A package holding two die therefore has to pick one die's numbers
and present them as the part's, or not be stored at all. 73 parts are currently not stored at
all, and 119 are stored the wrong way.

The proposal adds an optional `dies[]` array to `mosfetDatasheetInfo`, mutually exclusive with
the package-level `electrical`, plus the two `part` fields that say a package holds more than
one die. The mutual exclusion is the point: a part that declares `dies` has **no slot** in
which one die's r_DS(on) can be written as the part's.

## Evidence

Measured 2026-09-20 against this checkout (`TAS/data/mosfets.ndjson`, 9,556 records;
`TAS/data/quarantine.ndjson`, 98,690).

**(a) 73 parts are unrepresentable, and the split is 33 / 40 as stated.** All 73 are YAGEO
XSemi rows sitting in `quarantine.ndjson` with
`quarantineReason: "quarantined from the yageo import: source catalogue category could not be
mapped"`. Census of their `_yageoRaw.params.Configuration`:

| Configuration, verbatim | rows |
|---|---|
| `Complementary` | 25 |
| `Complementary Common-Drain` | 5 |
| `Complementary (with ESD Diode)` | 3 |
| **complementary total** | **33** |
| `Dual` | 23 |
| `Dual Channel` | 11 |
| `Dual (with ESD Diode)` | 3 |
| `Dual Common-Drain (with ESD Diode)` | 3 |
| **dual total** | **40** |

Confirmed: 33 complementary, 40 same-channel duals, 73 in all. (For scale, the same import
carried 501 `Single` and 21 `Single (with ESD Diode)` rows, which are stored fine.)

**(b) The vendor data is already per-die; only the schema is not.** `XP6932MT`
(`Configuration: "Dual Channel"`) carries a full second set of parameters:

```json
{"Series": "XP6932MT", "Configuration": "Dual Channel",
 "Drain-Source Voltage": "30 VDS",        "Drain-Source Voltage Channel 2": "30 VDS",
 "Gate Threshold Voltage": "2.2 V",       "Gate Threshold Voltage Channel 2": "2.2 V",
 "Gate-Source Voltage": "20 VGS",         "Gate-Source Voltage Channel 2": "20 VGS",
 "Total_Power_Dissipation": "1.78",       "Total Power Dissipation Channel 2": "2.08",
 "Total_Gate_Charge": "19/30.4",          "Total Gate Charge Channel 2": "40/64",
 "Technology": "N-Channel", "Package": "PMPAK-5x6(MT)"}
```

Note `Total Power Dissipation` 1.78 W vs 2.08 W for channel 2 — the die are **not** identical,
so "store one and call it the part's" is not even approximately true. And note `Technology:
"N-Channel"` on every one of the 33 **complementary** rows (`XP6C036AM`, `XP6C036MT`,
`XP6C058YT`, `XP10C036LMT`, …): the vendor's own single-valued field describes one die of a
pair whose whole point is that the two differ in channel type.

**(c) 119 live rows are stored as one die of two.** Of 9,556 `mosfets.ndjson` records, 119 say
in their own `case`/`package`/`description` that the package holds two die:

| `case`, verbatim | rows |
|---|---|
| `SO-8FL Dual / DFN-8` | 65 |
| `Dual SSO8` | 34 |
| `LFPAK56D; Dual LFPAK` | 11 |
| `Dual SSO8 HB` | 7 |
| `TSOP-6 Dual` | 1 |
| `WDFN8 3x3 (Power 33)` | 1 |

Each holds a single `onResistance`. One of them states the loss in words, in the field
reserved for names:

> `FDMC7200` — `"description": "Dual N-channel 30 V MOSFET; the stored electricals are Q1, the
> control FET (Q2 on the same package is the synchronous FET)"`, `onResistance: 0.0235`.

**(d) `subType: "powerBlock"` is the workaround, and it loses half the datasheet.** 6 rows use
it: `CSD86336Q3D`, `CSD88584Q5DC`, `CSD87334Q3D`, `CSD87333Q3D`, `CSD87351Q5D`, `CSD86330Q3D`
— all TI two-FET buck power blocks. Our record for `CSD86336Q3D` holds `onResistance: 0.0091`.
Its datasheet (TI SLPS666) has a table of contents that is itself the argument for the shape
proposed here:

```
5.3 Thermal Information .................................. 3
5.4 Power Block Performance ............................... 3
5.5 Electrical Characteristics – Q1 Control FET ........... 4
5.6 Electrical Characteristics – Q2 Sync FET .............. 5
```

with, verbatim from those two sections:

| | Q1 Control FET | Q2 Sync FET |
|---|---|---|
| `VGS(th)` typ | 1.1 V | 1.0 V |
| `ZDS(on)` | 9.1 mΩ | 3.4 mΩ |
| `Qg` total (4.5 V) | 2.9 nC | 5.7 nC |
| `CISS` typ | 380 pF | 728 pF |

Our stored `0.0091` is Q1's. Q2's 3.4 mΩ — the die that carries most of the conduction loss in
a buck — is absent. One `Thermal Information` section and one package serve both.

**(e) The corpus hazard is documented in our own importer, which cannot do better.**
`TAS/scripts/onsemi_csv_import.py`:

```python
def mohms(v):
    """'95' / 'Q1=Q2=95' / 'Q1: 62.0, Q2: 62.0' -> ohms. onsemi publishes a
    multi-channel r_DS(on) with the channel labels INLINE ... Strip the labels
    first, and refuse the cell when the channels disagree -- there is no single
    onResistance for the record then."""
    vals = {float(x) for x in re.findall(r"[-+]?\d*\.?\d+", re.sub(r"[Qq]\d+\s*[:=]", " ", v))}
    return vals.pop()*1e-3 if len(vals) == 1 else None
```

Both branches are forced by the schema, and both are wrong. When the die agree
(`Q1=Q2=95`) the part is recorded as a 95 mΩ MOSFET, byte-identical to a single-die 95 mΩ
part — the information that there are two 95 mΩ die is gone. When the die differ
(`Q1 = 42, Q2 = 1.4`) the value is refused and the part loses a required field, which is how
parts reach quarantine as "incomplete". **Any shape that cannot distinguish "both die are 95"
from "the part is 95" re-creates this, which is why the proposal makes the two states
structurally different rather than adding an optional second number.**

## The shape, and why this one

Two idioms already exist in the workspace, and the right move is to take the closer one rather
than invent a third.

**MAS — one part, one electrical block, per-winding positional arrays.**
`magneticDatasheetTransformerElectrical` carries `dcResistances[]`, `ratedCurrents[]`,
`turnsRatios[]`: parallel arrays indexed by winding. It also has an `electrical[]` variant
array whose entries carry a `name` ("4 x current compensated") for alternative *connection
configurations of the same part*. This works for windings because a winding has a handful of
quantities and no identity beyond its index. It does not transfer: `mosfetElectrical` has 27
properties, so a die would become 27 parallel arrays that can go ragged with nothing to
cross-check them, the channel type would become another parallel array, and the five required
fields would have to become "required arrays of equal length", which JSON Schema cannot state.
The `electrical[]` variant idiom is also semantically wrong here — its entries are alternative
*configurations of one device*, not two devices.

**CIAS — an array of named whole components.** A brick's `components[]` entries are
`{name, data}`, where `name` is "a reference designator unique within THIS brick ('Qh', 'Lr',
'C_in'). Connection endpoints refer to it by this name." Identity by **name**, one complete
device per entry. A die is a complete device with a full parameter set and a label the
datasheet itself prints (`Q1 Control FET`, `Q2 Sync FET`, `Channel 2`). This is the idiom to
follow.

So: **`dies[]`, each entry a named die with its own complete `electrical` block.**

**What identifies a die:** its `name`, taken verbatim from the datasheet — `Q1`, `Q2`,
`Channel 1`. Never invented: if the datasheet does not distinguish the die, there is nothing
to write. An optional `role` carries the datasheet's functional word (`Control FET`,
`Sync FET`) and an optional `pins[]` binds the die to the package pinout so a CIAS brick can
wire to one die rather than to the part. JSON Schema cannot check that those pin ids exist in
`mechanical.pinout`, nor that `name` is unique across the array (`uniqueItems` compares whole
objects); both are referential checks, of the same kind as CIAS's component URIs, and belong
to the ingest gate. Stated, not assumed.

**Per-package vs per-die:**

| | where it lives | why |
|---|---|---|
| package dimensions, pinout, land pattern, case | `datasheetInfo.mechanical` (unchanged) | one package |
| `RθJA`, mounting/soldering data | `datasheetInfo.thermal` (unchanged) | TI SLPS666 has one §5.3 for both die |
| `RθJC`, per-die power dissipation | optional `dies[].thermal` | YAGEO publishes 1.78 W / 2.08 W per channel |
| r_DS(on), V_GS(th), Q_g, capacitances, body diode, switching times | `dies[].electrical` (required per die) | TI SLPS666 §5.5 / §5.6; YAGEO "Channel 2" columns |
| channel type | `dies[].subType` (required per die) | the only place a complementary pair can be stated |

**Why not required-by-default:** `dies` is optional and mutually exclusive with `electrical`,
so all 9,556 existing records stay valid untouched. But once a part declares
`part.dieConfiguration: "dual" | "complementary"`, `dies` becomes **required** and
`electrical` becomes **forbidden**. That conditional is the anti-defect gate: a two-die part
cannot carry a package-level r_DS(on), so "both die are 95" is two entries each saying 95, and
"the part is 95" is not expressible for such a part at all.

**Where the definitions live.** `dieConfiguration`, `internalConnection` and a generic
`dieBase` go in `SAS/schemas/utils.json`; the MOSFET-specific `die` (which binds `dieBase` to
`mosfet.json#/$defs/electrical`) goes in `mosfet.json`. Both are intra-module `$ref`s, which
the dependency rule allows. Not PEAS: only SAS needs a die today, and a type used by one
module stays in that module. Dual diodes, dual BJTs and dual-IGBT packages exist in the same
corpus, and `dieBase` in `utils.json` lets them adopt the identical shape later without a
second design — but this RFC proposes the change for `mosfet.json` only, because that is
where the 73 + 119 + 6 parts are.

Note one mechanical constraint that dictates file placement: `utils.json#/$defs/part` is
`additionalProperties: false`, and `mosfet.json` only *narrows* `subType` on top of it. So the
two new `part` fields **must** be added in `utils.json`; they cannot be added in `mosfet.json`.
They are optional there, so diode/igbt/bjt documents are unaffected.

## Proposed change

### 1. `SAS/schemas/utils.json` — new `$defs`, and two optional `part` properties

```json
"dieConfiguration": {
  "title": "dieConfiguration",
  "description": "How many die the package holds and how their channels relate. Absent means the package holds one die, which is the overwhelming majority; state it explicitly only when the datasheet does. 'dual' = two die of the SAME channel type (onsemi SO-8FL Dual, Infineon Dual SSO8, TI two-FET power blocks); 'complementary' = one n-channel and one p-channel die in one package (YAGEO XP6C..., Vishay Si...DS). A part declaring 'dual' or 'complementary' MUST carry per-die data and MUST NOT carry a package-level electrical block — see mosfet.json.",
  "type": "string",
  "enum": ["single", "dual", "complementary"]
},
"internalConnection": {
  "title": "dieInternalConnection",
  "description": "How the die are wired to each other INSIDE the package, when the datasheet says so. 'independent' = no internal connection between the die; 'commonDrain' / 'commonSource' = the stated terminals are bonded internally (YAGEO prints 'Common-Drain' in its own Configuration column); 'halfBridge' = the drain of one die is bonded to the source of the other, forming a switching node (Infineon 'Dual SSO8 HB', TI power blocks). Omit when the datasheet does not state the internal arrangement — do not infer it from the package or the part number.",
  "type": "string",
  "enum": ["independent", "commonDrain", "commonSource", "halfBridge"]
},
"dieBase": {
  "title": "semiconductorDieBase",
  "description": "Identity of ONE die inside a multi-die package, shared by the device schemas. Device files extend it with their own electrical/thermal blocks and seal the result with unevaluatedProperties: false (the RAS pattern); this base is deliberately unsealed so it can be extended.",
  "type": "object",
  "required": ["name"],
  "properties": {
    "name": {
      "description": "The datasheet's own label for this die — 'Q1', 'Q2', 'Channel 1'. Unique within the part. Taken verbatim and never invented: a datasheet that does not distinguish its die gives no die entries to write.",
      "type": "string",
      "minLength": 1
    },
    "role": {
      "description": "The datasheet's functional name for the die where it gives one ('Control FET', 'Sync FET', 'High-Side'), verbatim. Free text because vendors do not share a vocabulary; it is a label, never a substitute for the electrical data.",
      "type": "string"
    },
    "pins": {
      "description": "Pin identifiers belonging to this die, matching entries of mechanical.pinout, so a circuit can bind to one die rather than to the package. Note what the schema cannot check: that the pinout contains these ids, that no pin is claimed by two die, and that die names are unique — those are the ingest gate's job, exactly as for CIAS component URIs.",
      "type": "array",
      "minItems": 1,
      "items": { "type": "string" }
    }
  }
}
```

and, inside `$defs.part.allOf[1].properties` (the closed object that already holds
`partNumber`, `series`, `case`, `technology`, `subType`, `package`, …):

```diff
     "matchcodeDescription": { "type": "string" },
+    "dieConfiguration": { "$ref": "#/$defs/dieConfiguration" },
+    "internalConnection": { "$ref": "#/$defs/internalConnection" }
   },
   "additionalProperties": false,
   "required": ["technology"]
```

### 2. `SAS/schemas/mosfet.json` — the per-die block, and the XOR

New `$defs.die`:

```json
"die": {
  "title": "mosfetDie",
  "description": "One MOSFET die inside a multi-die package, with the complete electrical block the discrete file already defines — the same physics and the same field names as a single-die part, stated once per die. Every die states its own values even when the datasheet prints them as equal ('Q1 = Q2 = 95'), so 'both die are 95 mOhm' and 'the part is 95 mOhm' are different documents.",
  "unevaluatedProperties": false,
  "allOf": [
    { "$ref": "./utils.json#/$defs/dieBase" },
    {
      "type": "object",
      "required": ["subType", "electrical"],
      "properties": {
        "subType": {
          "description": "Channel type OF THIS DIE. This is the field a complementary pair needs and the single-die shape cannot provide: the n-channel die says nChannel and the p-channel die says pChannel, in one part. 'powerBlock' is not legal here — it describes a package, not a die.",
          "type": "string",
          "enum": ["nChannel", "pChannel"]
        },
        "electrical": { "$ref": "#/$defs/electrical" },
        "thermal": {
          "description": "Per-die thermal figures where the datasheet gives them (junction-to-case, per-die power dissipation). The package-level figure stays in datasheetInfo.thermal — one package, one R_th(j-a).",
          "$ref": "./utils.json#/$defs/thermal"
        }
      }
    }
  ]
}
```

and in `$defs.datasheetInfo`:

```diff
   "properties": {
     "part":        { ... },
     "electrical":  { "$ref": "#/$defs/electrical" },
+    "dies": {
+      "description": "One entry per die in a multi-die package. Present INSTEAD OF the package-level electrical block, never beside it: a two-die part has no single r_DS(on), V_GS(th) or Q_g, and leaving a package-level slot open is what let one die's numbers be recorded as the part's. Order carries no meaning; die are identified by name.",
+      "type": "array",
+      "minItems": 2,
+      "items": { "$ref": "#/$defs/die" }
+    },
     "thermal":     { ... },
     "mechanical":  { ... },
     ...
   },
-  "required": ["part", "electrical"]
+  "required": ["part"],
+  "oneOf": [
+    { "required": ["electrical"], "not": { "required": ["dies"] } },
+    { "required": ["dies"],       "not": { "required": ["electrical"] } }
+  ],
+  "allOf": [
+    {
+      "$comment": "A package that declares two die must describe them per die. This is the gate: with no package-level electrical block available, one die's numbers cannot be written as the part's.",
+      "if": {
+        "required": ["part"],
+        "properties": {
+          "part": {
+            "required": ["dieConfiguration"],
+            "properties": { "dieConfiguration": { "enum": ["dual", "complementary"] } }
+          }
+        }
+      },
+      "then": { "required": ["dies"] }
+    }
+  ]
```

Nothing else changes. `electrical` keeps its five required fields for single-die parts;
`mechanical`, `thermal`, `curves`, `modelParams` and `provenance` are untouched; the
`subType` enum keeps `powerBlock` (see *Implementation*, note 5).

## Compatibility

Every currently valid document stays valid, and nothing previously invalid becomes valid:

- A document with `electrical` and no `dies` — which is all 9,556 `mosfets.ndjson` records and
  `SAS/examples/01_mosfet_ipb017n10n5.json` — satisfies the first `oneOf` branch. The relaxation
  of `required` from `["part", "electrical"]` to `["part"]` is not a loosening in practice,
  because the `oneOf` still forces one of the two blocks: a document with neither was invalid
  before and is invalid after.
- `dies`, `dieConfiguration` and `internalConnection` are new optional properties added inside
  objects that are `additionalProperties: false` / sealed, so those objects only become less
  restrictive.
- The two new `part` properties are added to the SAS-shared `part` def and are optional, so
  `diode.json`, `igbt.json` and `bjt.json` documents are unaffected.
- The 6 `powerBlock` rows keep validating unchanged; they gain a better home but are not
  invalidated.
- No consumer that reads `datasheetInfo.electrical` breaks on existing data. Consumers do need
  to learn that a part may carry `dies` instead — that is unavoidable for any shape that fixes
  this, and is why `dies` is a visibly different key rather than a silent change of meaning.

No migration is forced, and no data is written in advance of the decision.

## Alternatives considered

1. **Per-die positional arrays, MAS-style (`onResistances[]`, `gateThresholdVoltages[]`, …).**
   Rejected. 27 parallel arrays with no structural guarantee they are the same length, the
   channel type reduced to another array, no place for a die's name or pins, and the five
   required fields unexpressible. MAS gets away with it because a winding has few quantities
   and no identity; a die has both.

2. **Make `electrical` an array, MAS `electrical[]`-style.** Rejected on two counts: it
   invalidates all 9,556 existing records, and the MAS variant array means "alternative
   connection configurations of one device", which is a different fact from "two devices in
   one package". Overloading it would make `electrical[0]` mean different things in different
   records.

3. **Add optional second-die scalars (`onResistance2`, `gateThresholdVoltage2`, …).**
   Rejected. It leaves the package-level field in place, so `Q1 = Q2 = 95` still lands as a
   part-level 95 with the second slot empty — the exact defect this RFC exists to prevent —
   and it caps the design at two die by construction.

4. **Store each die as its own record.** Rejected. Two rows would claim the same orderable
   part number, and the catalogue has already been taught what duplicate rows of one part do
   (see CAS-RFC 0001, where the same-part duplicates were deleted and one of the two rated
   voltages went with them). It also gives the two die no way to say they share a package, a
   thermal path or a switching node.

5. **File duals under the existing `module.json`.** Rejected as the primary shape, with a
   caveat below. `module.json` exists for bolt-down power modules: its `electrical` requires
   `topology`, `switchTechnology`, `numberOfSwitches` and `switch`, and carries
   `isolationVoltage` (baseplate-to-terminals), `ntcIntegrated`, and a `terminalStyle` enum of
   `screw | pressFit | solderPin | spring | busbar`. An SO-8 dual is not that part, and filing
   it there to reach a field is the re-subtyping move MAS-RFC 0018 rejected for the same
   reason: it puts a false statement in the catalogue to avoid a schema change. Decisively,
   `module.json` would not even fix the problem — its `switch` is **one** electrical block
   described as "Electrical characteristics of ONE switch position", so `CSD86336Q3D`'s 9.1 mΩ
   Q1 and 3.4 mΩ Q2 still collapse to one number, and `switchTechnology` has no notion of
   channel type, so a complementary pair remains unrepresentable.
   *Caveat, flagged and deliberately not proposed here:* that single shared `switch` block is
   the same defect in `module.json`, for asymmetric modules. If `dieBase` lands in
   `utils.json`, `module.json` can adopt `switches[]` on the identical pattern later. That is
   a separate RFC with its own evidence, and folding it in here would widen this change past
   the parts that motivate it.

6. **Model a dual as a CIAS brick containing two single-die MOSFET parts.** Rejected as the
   shape for the catalogue record, though it composes with this one. A brick has no
   `manufacturerInfo`, no `distributorsInfo`, no package and no part number, so the orderable
   SKU disappears — you could no longer buy the thing the brick describes. With `dies[]` in
   place a brick can still reference the part by `partNumber` and bind a net to one die
   through `pins`, which is the right division: CIAS describes wiring, SAS describes the part.

7. **Keep one electrical block and record the rest in `description`.** Rejected: this is the
   status quo (`FDMC7200`), it is prose no query can filter on, and it violates the house rule
   that a name or description field holds names, not data.

8. **Hoist `die` into PEAS.** Rejected by the dependency rule. Only SAS needs it today; PEAS
   is the root and must never `$ref` a module, so a PEAS `die` with one consumer would be a
   definition placed where it cannot see the electrical blocks that give it meaning.

9. **A new PEAS discriminator for multi-die packages** (the direction SAS-RFC 0001 sketched:
   "a `module` representation … rather than overloading the single-die files"). Rejected for
   *this* cohort: a dual SO-8 is an ordinary MOSFET part that happens to contain two die, and
   it is bought, priced, mounted and filtered as a MOSFET. Adding `dies[]` does not preclude a
   future module discriminator; it makes one less necessary.

## Implementation

If accepted:

1. Two edits: `SAS/schemas/utils.json` (three `$defs` + two optional `part` properties) and
   `SAS/schemas/mosfet.json` (`$defs.die`, the `dies` property, the `oneOf` and the `if`/`then`).
2. `SAS/README.md` documents the per-device field sets and the closed `subType` enums; it gains
   the `dies[]` block and the two `part` fields in the same change, per the workspace rule that
   schema and docs move together.
3. One example: `SAS/examples/` gains a two-die MOSFET document (`CSD86336Q3D` is the natural
   candidate — its datasheet publishes both die in full), joining the existing single-die
   MOSFET, diode and module examples.
4. The checks that measure the change, not ones that would pass either way:
   - A **real** two-die document built from TI SLPS666 (`Q1` 9.1 mΩ / 1.1 V / 2.9 nC, `Q2`
     3.4 mΩ / 1.0 V / 5.7 nC, one package-level `thermal` and `mechanical`) validated with the
     full sibling registry: **valid after the change, invalid before it**, both asserted.
   - The gate, asserted as a **negative**: a document with `part.dieConfiguration: "dual"` and
     a package-level `electrical` must FAIL, and so must one with both `electrical` and `dies`.
     Revert the `oneOf`/`if`-`then` and confirm that test fails — a guard that passes in both
     states proves nothing and looks identical to one that works.
   - The equality case, asserted explicitly: two die each stating `onResistance: 0.095`
     validates and is a *different document* from a single-die part with `onResistance: 0.095`.
     This is the `Q1 = Q2 = 95` corpus hazard, encoded as a test rather than a hope.
   - A die with `subType: "powerBlock"` must be rejected; `dies` with fewer than 2 entries must
     be rejected.
   - `pytest SAS/tests/ -q` green, and the count of matched cases checked to be non-zero (a
     deleted test reports "no tests ran", which reads like success).
5. `subType: "powerBlock"` is **retained** by this RFC, not deprecated. Once `dies[]` exists it
   has no job left, but removing an enum value is a breaking change affecting 6 live rows and
   deserves its own decision. Flagged for you rather than decided here.
6. Data lands separately and only after acceptance: the 73 quarantined YAGEO parts return with
   per-die records; the 6 TI power blocks are re-read from their datasheets; the 119 live
   single-die-of-two rows are re-sourced per die and are **not** rewritten by the schema
   change — a schema cannot supply a number the record never held.
