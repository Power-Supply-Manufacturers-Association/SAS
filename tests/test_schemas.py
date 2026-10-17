"""Validation tests for the SAS schemas.

Run with:   pytest tests/
or:         python3 -m pytest tests/test_schemas.py -v

Covers:
  * every SAS schema parses and passes Draft 2020-12 meta-validation
  * cross-document $refs resolve (SAS + PEAS schemas registered)
  * the canonical examples validate
  * negative cases:
      - top-level oneOf (must have exactly one of mosfet/diode/igbt/bjt/thyristor/jfet/optocoupler/module)
      - manufacturerInfo is required
      - electrical is required inside datasheetInfo
      - per-type-specific required electrical fields
      - extra properties rejected (additionalProperties: false)
      - dimensionWithTolerance shape
      - designRequirements deviceType discriminator drives required ratings
"""

import copy
import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator
from referencing import Registry, Resource
from referencing.jsonschema import DRAFT202012

REPO = Path(__file__).resolve().parents[1]
SCHEMA_DIR = REPO / "schemas"
EXAMPLES_DIR = REPO / "examples"
PEAS_SCHEMA_DIR = REPO.parent / "PEAS" / "schemas"

SAS_SCHEMA_FILES = [
    "SAS.json",
    "inputs.json",
    "outputs.json",
    "utils.json",
    "mosfet.json",
    "diode.json",
    "igbt.json",
    "bjt.json",
    "thyristor.json",
    "jfet.json",
    "optocoupler.json",
    "module.json",
    "inputs/designRequirements.json",
]


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def _load(path: Path):
    return json.loads(path.read_text())


@pytest.fixture(scope="session")
def schemas():
    out = {}
    for rel in SAS_SCHEMA_FILES:
        s = _load(SCHEMA_DIR / rel)
        out[s["$id"]] = s
    # Pull every PEAS schema we might $ref so the registry resolves them.
    for path in PEAS_SCHEMA_DIR.rglob("*.json"):
        s = _load(path)
        out[s["$id"]] = s
    return out


@pytest.fixture(scope="session")
def registry(schemas):
    resources = [
        (sid, Resource(contents=s, specification=DRAFT202012))
        for sid, s in schemas.items()
    ]
    return Registry().with_resources(resources)


@pytest.fixture(scope="session")
def sas_validator(schemas, registry):
    return Draft202012Validator(
        schemas["https://psma.com/sas/SAS.json"],
        registry=registry,
    )


@pytest.fixture
def mosfet_doc():
    return _load(EXAMPLES_DIR / "01_mosfet_ipb017n10n5.json")


@pytest.fixture
def diode_doc():
    return _load(EXAMPLES_DIR / "02_diode_stps30l60ct.json")


@pytest.fixture
def module_doc():
    return _load(EXAMPLES_DIR / "03_module_ff2mr12w3m1h.json")


@pytest.fixture
def multi_die_doc():
    return _load(EXAMPLES_DIR / "04_mosfet_dual_iaucn04s7l025ah.json")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def assert_valid(validator, doc):
    errs = sorted(validator.iter_errors(doc), key=lambda e: list(e.path))
    assert not errs, "expected valid, got errors:\n" + "\n".join(
        f"  - {e.message} @ {list(e.absolute_path)}" for e in errs
    )


def assert_invalid(validator, doc, *, contains=None):
    errs = list(validator.iter_errors(doc))
    assert errs, "expected invalid, got no errors"
    if contains:
        joined = " | ".join(e.message for e in errs)
        assert contains in joined, f"expected error containing {contains!r}, got: {joined}"


# ---------------------------------------------------------------------------
# Schema-level tests
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("rel", SAS_SCHEMA_FILES)
def test_schema_parses(rel):
    _load(SCHEMA_DIR / rel)


@pytest.mark.parametrize("rel", SAS_SCHEMA_FILES)
def test_schema_meta_valid(rel):
    Draft202012Validator.check_schema(_load(SCHEMA_DIR / rel))


# ---------------------------------------------------------------------------
# Positive examples
# ---------------------------------------------------------------------------

def test_mosfet_example_validates(sas_validator, mosfet_doc):
    assert_valid(sas_validator, mosfet_doc)


def test_diode_example_validates(sas_validator, diode_doc):
    assert_valid(sas_validator, diode_doc)


def test_module_example_validates(sas_validator, module_doc):
    assert_valid(sas_validator, module_doc)


# ---------------------------------------------------------------------------
# Top-level oneOf: exactly one of mosfet/diode/igbt/bjt/thyristor/jfet/optocoupler/module
# ---------------------------------------------------------------------------

def test_missing_device_type_field_invalid(sas_validator, mosfet_doc):
    del mosfet_doc["mosfet"]
    assert_invalid(sas_validator, mosfet_doc)


def test_two_device_type_fields_invalid(sas_validator, mosfet_doc, diode_doc):
    mosfet_doc["diode"] = diode_doc["diode"]
    assert_invalid(sas_validator, mosfet_doc)


def test_unknown_device_type_field_rejected(sas_validator, mosfet_doc):
    mosfet_doc["vacuumTube"] = mosfet_doc.pop("mosfet")
    assert_invalid(sas_validator, mosfet_doc)


# ---------------------------------------------------------------------------
# inputs / outputs structural requirements
# ---------------------------------------------------------------------------

def test_inputs_required(sas_validator, mosfet_doc):
    del mosfet_doc["inputs"]
    assert_invalid(sas_validator, mosfet_doc)


def test_outputs_required(sas_validator, mosfet_doc):
    del mosfet_doc["outputs"]
    assert_invalid(sas_validator, mosfet_doc)


def test_outputs_must_be_array(sas_validator, mosfet_doc):
    mosfet_doc["outputs"] = {}
    assert_invalid(sas_validator, mosfet_doc)


def test_operating_points_min_one(sas_validator, mosfet_doc):
    mosfet_doc["inputs"]["operatingPoints"] = []
    assert_invalid(sas_validator, mosfet_doc)


# ---------------------------------------------------------------------------
# Per-type schema requirements
# ---------------------------------------------------------------------------

def test_manufacturer_info_required(sas_validator, mosfet_doc):
    del mosfet_doc["mosfet"]["manufacturerInfo"]
    assert_invalid(sas_validator, mosfet_doc)


def test_datasheet_info_required(sas_validator, mosfet_doc):
    del mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]
    assert_invalid(sas_validator, mosfet_doc)


def test_electrical_required_in_datasheet_info(sas_validator, mosfet_doc):
    del mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["electrical"]
    assert_invalid(sas_validator, mosfet_doc)


def test_part_required_in_datasheet_info(sas_validator, mosfet_doc):
    del mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["part"]
    assert_invalid(sas_validator, mosfet_doc)


def test_mosfet_required_electrical_fields(sas_validator, mosfet_doc):
    elec = mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["electrical"]
    for field in ("drainSourceVoltage", "onResistance", "continuousDrainCurrent"):
        bad = copy.deepcopy(mosfet_doc)
        del bad["mosfet"]["manufacturerInfo"]["datasheetInfo"]["electrical"][field]
        assert_invalid(sas_validator, bad)


def test_diode_required_electrical_fields(sas_validator, diode_doc):
    for field in ("reverseVoltage", "forwardVoltage", "forwardCurrent"):
        bad = copy.deepcopy(diode_doc)
        del bad["diode"]["manufacturerInfo"]["datasheetInfo"]["electrical"][field]
        assert_invalid(sas_validator, bad)


def test_part_no_device_type_property(sas_validator, mosfet_doc):
    # The deviceType field is intentionally removed from `part` — the field name
    # at the top level of the doc is the discriminator. additionalProperties:false
    # on `part` should reject it.
    mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["part"]["deviceType"] = "mosfet"
    assert_invalid(sas_validator, mosfet_doc)


def test_part_unknown_field_rejected(sas_validator, mosfet_doc):
    mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["part"]["bogus"] = "x"
    assert_invalid(sas_validator, mosfet_doc)


def test_electrical_unknown_field_rejected(sas_validator, mosfet_doc):
    mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["electrical"]["bogus"] = 1
    assert_invalid(sas_validator, mosfet_doc)


def test_dimension_with_tolerance_requires_one_field(sas_validator, mosfet_doc):
    mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]["electrical"]["gateThresholdVoltage"] = {}
    assert_invalid(sas_validator, mosfet_doc)


# ---------------------------------------------------------------------------
# designRequirements deviceType discriminator
# ---------------------------------------------------------------------------

def test_design_requirements_device_type_required(sas_validator, mosfet_doc):
    del mosfet_doc["inputs"]["designRequirements"]["deviceType"]
    assert_invalid(sas_validator, mosfet_doc)


def test_design_requirements_mosfet_rated_fields_optional(sas_validator, mosfet_doc):
    # Deliberately seed-friendly (commit 1540d54): a pre-sourcing seed with only
    # deviceType must validate; rated* fields are optional.
    ok = copy.deepcopy(mosfet_doc)
    del ok["inputs"]["designRequirements"]["ratedDrainSourceVoltage"]
    del ok["inputs"]["designRequirements"]["ratedContinuousDrainCurrent"]
    assert_valid(sas_validator, ok)


def test_design_requirements_diode_rated_fields_optional(sas_validator, diode_doc):
    ok = copy.deepcopy(diode_doc)
    del ok["inputs"]["designRequirements"]["ratedReverseVoltage"]
    del ok["inputs"]["designRequirements"]["ratedForwardCurrent"]
    assert_valid(sas_validator, ok)


def test_unknown_device_type_in_design_requirements_rejected(sas_validator, mosfet_doc):
    mosfet_doc["inputs"]["designRequirements"]["deviceType"] = "vacuumTube"
    assert_invalid(sas_validator, mosfet_doc)


def test_design_requirements_mosfet_channel(sas_validator, mosfet_doc):
    for ch in ("nChannel", "pChannel"):
        ok = copy.deepcopy(mosfet_doc)
        ok["inputs"]["designRequirements"]["channel"] = ch
        assert_valid(sas_validator, ok)
    mosfet_doc["inputs"]["designRequirements"]["channel"] = "powerBlock"  # a package, not a channel
    assert_invalid(sas_validator, mosfet_doc)


def test_design_requirements_channel_is_mosfet_only(sas_validator, diode_doc):
    diode_doc["inputs"]["designRequirements"]["channel"] = "nChannel"
    assert_invalid(sas_validator, diode_doc)


def test_design_requirements_bjt_polarity(sas_validator, mosfet_doc):
    dr = mosfet_doc["inputs"]["designRequirements"]
    for k in [k for k in dr if k.startswith(("rated", "maximum"))]:
        del dr[k]
    dr["deviceType"] = "bjt"
    for pol in ("npn", "pnp"):
        dr["polarity"] = pol
        errs = [e for e in sas_validator.iter_errors(mosfet_doc) if "designRequirements" in e.json_path]
        assert not errs, [e.message for e in errs]
    dr["polarity"] = "nChannel"
    errs = [e for e in sas_validator.iter_errors(mosfet_doc) if "designRequirements" in e.json_path]
    assert errs


def test_allowed_technologies_enum(sas_validator, mosfet_doc):
    mosfet_doc["inputs"]["designRequirements"]["allowedTechnologies"] = ["unobtainium"]
    assert_invalid(sas_validator, mosfet_doc)


# ---------------------------------------------------------------------------
# Power module (module.json)
# ---------------------------------------------------------------------------

def _module_electrical(module_doc):
    return module_doc["module"]["manufacturerInfo"]["datasheetInfo"]["electrical"]


def test_module_seed_valid(sas_validator):
    # A bare pre-sourcing seed must validate (maxProperties: 1 at the top,
    # empty device body allowed by maxProperties: 0).
    assert_valid(sas_validator, {"module": {}})


def test_module_and_mosfet_together_invalid(sas_validator, module_doc, mosfet_doc):
    module_doc["mosfet"] = mosfet_doc["mosfet"]
    assert_invalid(sas_validator, module_doc)


def test_module_required_electrical_fields(sas_validator, module_doc):
    for field in ("topology", "switchTechnology", "numberOfSwitches", "switch"):
        bad = copy.deepcopy(module_doc)
        del _module_electrical(bad)[field]
        assert_invalid(sas_validator, bad)


def test_module_unknown_topology_rejected(sas_validator, module_doc):
    _module_electrical(module_doc)["topology"] = "quadPack"
    assert_invalid(sas_validator, module_doc)


def test_module_unknown_switch_technology_rejected(sas_validator, module_doc):
    _module_electrical(module_doc)["switchTechnology"] = "germaniumBjt"
    assert_invalid(sas_validator, module_doc)


def test_module_switch_shape_pinned_by_technology(sas_validator, module_doc):
    # sicMosfet pins the mosfet electrical shape: an igbt-shaped switch block
    # must be rejected (collectorEmitterVoltage is not a mosfet field, and the
    # mosfet required quintet is missing).
    _module_electrical(module_doc)["switch"] = {
        "collectorEmitterVoltage": 1200,
        "collectorEmitterSaturation": 1.85,
        "continuousCollectorCurrent": 115,
    }
    assert_invalid(sas_validator, module_doc)


def test_module_igbt_switch_shape_accepted(sas_validator, module_doc):
    # siliconIgbt pins the igbt electrical shape.
    elec = _module_electrical(module_doc)
    elec["switchTechnology"] = "siliconIgbt"
    elec["switch"] = {
        "collectorEmitterVoltage": 1200,
        "collectorEmitterSaturation": 1.85,
        "continuousCollectorCurrent": 115,
    }
    # sicMosfet-only requirement fields stay valid (allowedSwitchTechnologies is a
    # requirement, not a datasheet constraint), but keep the doc self-consistent.
    module_doc["inputs"]["designRequirements"]["allowedSwitchTechnologies"] = ["siliconIgbt"]
    module_doc["module"]["manufacturerInfo"]["datasheetInfo"]["part"]["technology"] = "Si"
    assert_valid(sas_validator, module_doc)


def test_module_ntc_fields_require_ntc_integrated(sas_validator, module_doc):
    del _module_electrical(module_doc)["ntcIntegrated"]
    assert_invalid(sas_validator, module_doc)


def test_module_electrical_unknown_field_rejected(sas_validator, module_doc):
    _module_electrical(module_doc)["bogus"] = 1
    assert_invalid(sas_validator, module_doc)


def test_module_part_subtype_mirrors_topology_enum(sas_validator, module_doc):
    module_doc["module"]["manufacturerInfo"]["datasheetInfo"]["part"]["subType"] = "nChannel"
    assert_invalid(sas_validator, module_doc)


def test_module_terminal_style_enum(sas_validator, module_doc):
    mech = module_doc["module"]["manufacturerInfo"]["datasheetInfo"]["mechanical"]
    mech["terminalStyle"] = "weldTab"
    assert_invalid(sas_validator, module_doc)


def test_module_design_requirements_seed_friendly(sas_validator, module_doc):
    # Only deviceType is required in the module requirements branch.
    module_doc["inputs"]["designRequirements"] = {"deviceType": "module"}
    assert_valid(sas_validator, module_doc)


def test_module_design_requirements_topology_enum(sas_validator, module_doc):
    module_doc["inputs"]["designRequirements"]["moduleTopology"] = "quadPack"
    assert_invalid(sas_validator, module_doc)


def test_module_topology_field_rejected_on_other_device_types(sas_validator, mosfet_doc):
    # moduleTopology belongs to the module branch only.
    mosfet_doc["inputs"]["designRequirements"]["moduleTopology"] = "halfBridge"
    assert_invalid(sas_validator, mosfet_doc)


# ---------------------------------------------------------------------------
# Multi-die MOSFET packages (SAS-RFC 0002)
# ---------------------------------------------------------------------------

def _mosfet_di(mosfet_doc):
    return mosfet_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]


def _die(name, r_ds_on, sub_type="nChannel"):
    return {
        "name": name,
        "subType": sub_type,
        "electrical": {
            "drainSourceVoltage": 30,
            "onResistance": r_ds_on,
            "continuousDrainCurrent": 10,
            "gateThresholdVoltage": {"nominal": 1.5},
            "totalGateCharge": 10e-9,
        },
    }


def _make_two_die(mosfet_doc, r1=0.095, r2=0.095):
    di = _mosfet_di(mosfet_doc)
    di.pop("electrical")
    di["part"]["dieConfiguration"] = "dual"
    di["dies"] = [_die("Q1", r1), _die("Q2", r2)]
    return mosfet_doc


def test_two_die_document_validates(sas_validator, mosfet_doc):
    assert_valid(sas_validator, _make_two_die(mosfet_doc, 0.0091, 0.0034))


def test_two_equal_die_validate_and_differ_from_single_die(sas_validator, mosfet_doc):
    """'Both die are 95 mOhm' and 'the part is 95 mOhm' must be different documents."""
    single = copy.deepcopy(mosfet_doc)
    single["mosfet"]["manufacturerInfo"]["datasheetInfo"]["electrical"]["onResistance"] = 0.095
    assert_valid(sas_validator, single)
    dual = _make_two_die(mosfet_doc, 0.095, 0.095)
    assert_valid(sas_validator, dual)
    assert dual != single


def test_dual_die_configuration_forbids_package_electrical(sas_validator, mosfet_doc):
    """THE GATE: a package declaring two die cannot carry one die's R_DS(on) as the part's."""
    di = _mosfet_di(mosfet_doc)
    di["part"]["dieConfiguration"] = "dual"
    assert_invalid(sas_validator, mosfet_doc)


def test_electrical_and_dies_together_rejected(sas_validator, mosfet_doc):
    di = _mosfet_di(mosfet_doc)
    di["dies"] = [_die("Q1", 0.095), _die("Q2", 0.095)]
    assert_invalid(sas_validator, mosfet_doc)


def test_neither_electrical_nor_dies_rejected(sas_validator, mosfet_doc):
    _mosfet_di(mosfet_doc).pop("electrical")
    assert_invalid(sas_validator, mosfet_doc)


def test_dies_requires_at_least_two_entries(sas_validator, mosfet_doc):
    doc = _make_two_die(mosfet_doc)
    _mosfet_di(doc)["dies"] = _mosfet_di(doc)["dies"][:1]
    assert_invalid(sas_validator, doc)


def test_die_subtype_power_block_rejected(sas_validator, mosfet_doc):
    doc = _make_two_die(mosfet_doc)
    _mosfet_di(doc)["dies"][0]["subType"] = "powerBlock"
    assert_invalid(sas_validator, doc)


def test_die_requires_subtype_and_electrical(sas_validator, mosfet_doc):
    doc = _make_two_die(mosfet_doc)
    _mosfet_di(doc)["dies"][0].pop("subType")
    assert_invalid(sas_validator, doc)


def test_die_unknown_property_rejected(sas_validator, mosfet_doc):
    doc = _make_two_die(mosfet_doc)
    _mosfet_di(doc)["dies"][0]["onResistance"] = 0.095
    assert_invalid(sas_validator, doc)


def test_complementary_pair_carries_both_channel_types(sas_validator, mosfet_doc):
    di = _mosfet_di(mosfet_doc)
    di.pop("electrical")
    di["part"]["dieConfiguration"] = "complementary"
    di["part"]["internalConnection"] = "commonDrain"
    di["dies"] = [_die("Q1", 0.05, "nChannel"), _die("Q2", 0.09, "pChannel")]
    assert_valid(sas_validator, mosfet_doc)


def test_die_configuration_enum_closed(sas_validator, mosfet_doc):
    _mosfet_di(mosfet_doc)["part"]["dieConfiguration"] = "triple"
    assert_invalid(sas_validator, mosfet_doc)


def test_internal_connection_enum_closed(sas_validator, mosfet_doc):
    _mosfet_di(mosfet_doc)["part"]["internalConnection"] = "backToBack"
    assert_invalid(sas_validator, mosfet_doc)


def test_single_die_configuration_does_not_require_dies(sas_validator, mosfet_doc):
    _mosfet_di(mosfet_doc)["part"]["dieConfiguration"] = "single"
    assert_valid(sas_validator, mosfet_doc)


def test_multi_die_example_validates(sas_validator, multi_die_doc):
    assert_valid(sas_validator, multi_die_doc)


def test_multi_die_example_carries_no_package_electrical(sas_validator, multi_die_doc):
    """The example is the whole point: two die, no package-level electrical slot."""
    di = multi_die_doc["mosfet"]["manufacturerInfo"]["datasheetInfo"]
    assert "electrical" not in di
    assert len(di["dies"]) == 2
    assert {d["electrical"]["onResistance"] for d in di["dies"]} == {0.00256, 0.00504}
    di["electrical"] = dict(di["dies"][0]["electrical"])
    assert_invalid(sas_validator, multi_die_doc)


def test_die_electrical_does_not_require_continuous_drain_current(sas_validator, mosfet_doc):
    """A continuous drain current is a PACKAGE rating: TI's power-block datasheets
    publish one operating current for both die, so requiring it per die would make
    the faithful record unwritable."""
    doc = _make_two_die(mosfet_doc, 0.0091, 0.0034)
    for die in _mosfet_di(doc)["dies"]:
        die["electrical"].pop("continuousDrainCurrent")
    assert_valid(sas_validator, doc)


def test_package_electrical_still_requires_continuous_drain_current(sas_validator, mosfet_doc):
    """The relaxation is scoped to dies[]: a single-die part still rates its I_D."""
    _mosfet_di(mosfet_doc)["electrical"].pop("continuousDrainCurrent")
    assert_invalid(sas_validator, mosfet_doc, contains="'continuousDrainCurrent' is a required property")


def test_module_switch_still_requires_continuous_drain_current(sas_validator, module_doc):
    """module.json $refs the mosfet electrical block; splitting out the base must
    not have loosened it there."""
    sw = module_doc["module"]["manufacturerInfo"]["datasheetInfo"]["electrical"]["switch"]
    sw.pop("continuousDrainCurrent", None)
    assert_invalid(sas_validator, module_doc, contains="'continuousDrainCurrent' is a required property")


# ---------------------------------------------------------------------------
# TVS/ESD pulse-rating waveforms (SAS-RFC 0003, PEAS-RFC 0003 surgeWaveform)
# ---------------------------------------------------------------------------

@pytest.fixture
def tvs_doc():
    return _load(EXAMPLES_DIR / "05_tvs_ptvs1_022c_h.json")


def _tvs_electrical(doc):
    return doc["diode"]["manufacturerInfo"]["datasheetInfo"]["electrical"]


def test_tvs_example_validates(sas_validator, tvs_doc):
    assert_valid(sas_validator, tvs_doc)


def test_tvs_example_states_every_waveform(tvs_doc):
    el = _tvs_electrical(tvs_doc)
    assert el["peakPulseCurrentWaveform"] == "8/20"
    assert el["clampingWaveform"] == "8/20"
    assert el["clampingCurrent"] == el["peakPulseCurrent"]


@pytest.mark.parametrize("subtype, electrical", [
    # peakPulseCurrentWaveform without peakPulseCurrent (rating given as power)
    ("tvs", {"standoffVoltage": 5, "clampingVoltage": 9.8, "peakPulsePower": 350,
             "peakPulseCurrentWaveform": "8/20"}),
    # peakPulsePowerWaveform without peakPulsePower
    ("tvs", {"standoffVoltage": 5, "clampingVoltage": 9.8, "peakPulseCurrent": 20,
             "peakPulsePowerWaveform": "10/1000"}),
    # clampingWaveform without clampingVoltage (esd needs no V_C)
    ("esd", {"standoffVoltage": 5, "peakPulseCurrent": 20,
             "clampingWaveform": "TLP 100 ns"}),
])
def test_waveform_without_its_value_rejected(sas_validator, tvs_doc, subtype, electrical):
    tvs_doc["diode"]["manufacturerInfo"]["datasheetInfo"]["part"]["subType"] = subtype
    tvs_doc["diode"]["manufacturerInfo"]["datasheetInfo"]["electrical"] = electrical
    assert_invalid(sas_validator, tvs_doc, contains="is a dependency of")


def test_clamping_current_without_clamping_voltage_rejected(sas_validator, tvs_doc):
    el = _tvs_electrical(tvs_doc)
    del el["clampingVoltage"]
    del el["clampingWaveform"]
    tvs_doc["diode"]["manufacturerInfo"]["datasheetInfo"]["part"]["subType"] = "esd"
    assert_invalid(sas_validator, tvs_doc, contains="is a dependency of")


@pytest.mark.parametrize("field", [
    "peakPulseCurrentWaveform", "clampingWaveform",
])
@pytest.mark.parametrize("bad", ["8x20", "8/20us", "ISO 7637-2 pulse 1", "IEC 61000-4-2", ""])
def test_unknown_waveform_rejected(sas_validator, tvs_doc, field, bad):
    _tvs_electrical(tvs_doc)[field] = bad
    assert_invalid(sas_validator, tvs_doc, contains="is not one of")


def test_peak_pulse_power_waveform_unknown_rejected(sas_validator, tvs_doc):
    el = _tvs_electrical(tvs_doc)
    el["peakPulsePower"] = 350
    el["peakPulsePowerWaveform"] = "10/1000us"
    assert_invalid(sas_validator, tvs_doc, contains="is not one of")


def test_peak_pulse_power_waveform_accepted(sas_validator, tvs_doc):
    el = _tvs_electrical(tvs_doc)
    el["peakPulsePower"] = 350
    el["peakPulsePowerWaveform"] = "10/1000"
    assert_valid(sas_validator, tvs_doc)


def test_clamping_current_must_be_positive(sas_validator, tvs_doc):
    _tvs_electrical(tvs_doc)["clampingCurrent"] = 0
    assert_invalid(sas_validator, tvs_doc)


def test_pulse_values_without_waveform_still_valid(sas_validator, tvs_doc):
    """Absent waveform = not stated; the 14k legacy TVS/ESD rows stay valid."""
    el = _tvs_electrical(tvs_doc)
    for k in ("peakPulseCurrentWaveform", "clampingWaveform", "clampingCurrent"):
        del el[k]
    assert_valid(sas_validator, tvs_doc)


# ---------------------------------------------------------------------------
# Multi-die BJT packages: dies[] + matching[], gated like the MOSFET
# ---------------------------------------------------------------------------

@pytest.fixture
def bjt_pair_doc():
    return _load(EXAMPLES_DIR / "06_bjt_dual_matched_ssm2212.json")


def _bjt_di(doc):
    return doc["bjt"]["manufacturerInfo"]["datasheetInfo"]


def _bjt_single(doc):
    """The SSM2212 rewritten as a single-die record (package electrical, no dies/matching)."""
    di = _bjt_di(doc)
    di["electrical"] = copy.deepcopy(di.pop("dies")[0]["electrical"])
    di.pop("matching")
    di["part"].pop("dieConfiguration")
    return doc


def test_bjt_matched_pair_example_validates(sas_validator, bjt_pair_doc):
    assert_valid(sas_validator, bjt_pair_doc)


def test_bjt_matched_pair_example_is_per_die(bjt_pair_doc):
    di = _bjt_di(bjt_pair_doc)
    assert "electrical" not in di
    assert [d["name"] for d in di["dies"]] == ["Channel 1", "Channel 2"]
    assert di["matching"][0]["baseEmitterVoltageMatch"] == {"nominal": 1e-05, "maximum": 0.0002}


def test_bjt_single_die_record_still_valid(sas_validator, bjt_pair_doc):
    assert_valid(sas_validator, _bjt_single(bjt_pair_doc))


def test_bjt_dies_beside_package_electrical_rejected(sas_validator, bjt_pair_doc):
    di = _bjt_di(bjt_pair_doc)
    di["electrical"] = copy.deepcopy(di["dies"][0]["electrical"])
    assert_invalid(sas_validator, bjt_pair_doc)


def test_bjt_neither_electrical_nor_dies_rejected(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc).pop("dies")
    _bjt_di(bjt_pair_doc).pop("matching")
    assert_invalid(sas_validator, bjt_pair_doc)


def test_bjt_matching_requires_dies(sas_validator, bjt_pair_doc):
    doc = _bjt_single(bjt_pair_doc)
    _bjt_di(doc)["matching"] = [{"baseEmitterVoltageMatch": {"maximum": 2e-4}}]
    assert_invalid(sas_validator, doc, contains="'dies' is a required property")


def test_bjt_complementary_forbids_part_subtype(sas_validator, bjt_pair_doc):
    di = _bjt_di(bjt_pair_doc)
    di["part"]["dieConfiguration"] = "complementary"
    di["dies"][1]["subType"] = "pnp"
    assert_invalid(sas_validator, bjt_pair_doc)
    di["part"].pop("subType")
    assert_valid(sas_validator, bjt_pair_doc)


def test_bjt_matching_entry_needs_a_quantity(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["matching"] = [{"testCollectorCurrent": 1e-3}]
    assert_invalid(sas_validator, bjt_pair_doc)


def test_bjt_matching_unknown_field_rejected(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["matching"][0]["offsetVoltage"] = 1e-5
    assert_invalid(sas_validator, bjt_pair_doc, contains="unexpected")


def test_bjt_dies_requires_two_entries(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["dies"] = _bjt_di(bjt_pair_doc)["dies"][:1]
    assert_invalid(sas_validator, bjt_pair_doc, contains="is too short")


def test_bjt_die_requires_collector_current(sas_validator, bjt_pair_doc):
    """BJT duals print I_C per transistor, so the die keeps the single-part requirement."""
    _bjt_di(bjt_pair_doc)["dies"][0]["electrical"].pop("collectorCurrent")
    assert_invalid(sas_validator, bjt_pair_doc, contains="'collectorCurrent' is a required property")


def test_bjt_die_requires_polarity(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["dies"][0].pop("subType")
    assert_invalid(sas_validator, bjt_pair_doc, contains="'subType' is a required property")


def test_bjt_quad_as_array(sas_validator, bjt_pair_doc):
    di = _bjt_di(bjt_pair_doc)
    di["part"]["dieConfiguration"] = "array"
    di["dies"] = [dict(copy.deepcopy(di["dies"][0]), name=f"Q{i}") for i in range(1, 5)]
    assert_valid(sas_validator, bjt_pair_doc)


def test_bjt_die_configuration_quad_rejected(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["part"]["dieConfiguration"] = "quad"
    assert_invalid(sas_validator, bjt_pair_doc)


@pytest.mark.parametrize("cfg", ["dual", "complementary", "array"])
def test_bjt_multi_die_with_package_electrical_rejected(sas_validator, bjt_pair_doc, cfg):
    """The gate: a package declaring two or more die must describe them per die."""
    doc = _bjt_single(bjt_pair_doc)
    _bjt_di(doc)["part"]["dieConfiguration"] = cfg
    if cfg == "complementary":
        _bjt_di(doc)["part"].pop("subType")
    assert_invalid(sas_validator, doc, contains="'dies' is a required property")


@pytest.mark.parametrize("cfg", ["dual", "complementary", "array"])
def test_bjt_multi_die_with_dies_accepted(sas_validator, bjt_pair_doc, cfg):
    di = _bjt_di(bjt_pair_doc)
    di["part"]["dieConfiguration"] = cfg
    if cfg == "complementary":
        di["part"].pop("subType")
        di["dies"][1]["subType"] = "pnp"
    assert_valid(sas_validator, bjt_pair_doc)


@pytest.mark.parametrize("cfg", ["single", None])
def test_bjt_single_die_package_electrical_not_gated(sas_validator, bjt_pair_doc, cfg):
    doc = _bjt_single(bjt_pair_doc)
    if cfg:
        _bjt_di(doc)["part"]["dieConfiguration"] = cfg
    assert_valid(sas_validator, doc)


@pytest.mark.parametrize("value", ["commonEmitter", "commonBase", "commonCollector", "currentMirror", "independent"])
def test_bjt_internal_connection_bjt_words(sas_validator, bjt_pair_doc, value):
    _bjt_di(bjt_pair_doc)["part"]["internalConnection"] = value
    assert_valid(sas_validator, bjt_pair_doc)


@pytest.mark.parametrize("value", ["commonDrain", "commonSource", "halfBridge", "commonCathode"])
def test_bjt_internal_connection_other_device_words_rejected(sas_validator, bjt_pair_doc, value):
    _bjt_di(bjt_pair_doc)["part"]["internalConnection"] = value
    assert_invalid(sas_validator, bjt_pair_doc)


def test_bjt_package_power_dissipation_beside_dies(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["packagePowerDissipation"] = 0.3
    assert_valid(sas_validator, bjt_pair_doc)


def test_bjt_package_power_dissipation_requires_dies(sas_validator, bjt_pair_doc):
    doc = _bjt_single(bjt_pair_doc)
    _bjt_di(doc)["packagePowerDissipation"] = 0.3
    assert_invalid(sas_validator, doc, contains="'dies' is a required property")


@pytest.mark.parametrize("field", ["voltageNoiseDensityFrequency", "voltageNoiseDensityCollectorCurrent"])
def test_bjt_noise_condition_requires_noise_value(sas_validator, bjt_pair_doc, field):
    el = _bjt_di(bjt_pair_doc)["dies"][0]["electrical"]
    el.pop("voltageNoiseDensity")
    for k in ("voltageNoiseDensityFrequency", "voltageNoiseDensityCollectorCurrent"):
        if k != field:
            el.pop(k)
    assert_invalid(sas_validator, bjt_pair_doc, contains="is a dependency of")


def test_bjt_old_noise_name_rejected(sas_validator, bjt_pair_doc):
    _bjt_di(bjt_pair_doc)["dies"][0]["electrical"]["noiseVoltageDensity"] = 8.5e-10
    assert_invalid(sas_validator, bjt_pair_doc, contains="unexpected")


def test_mosfet_array_requires_dies(sas_validator, mosfet_doc):
    """'array' joins the shared enum; on a MOSFET it is gated exactly like 'dual'."""
    _mosfet_di(mosfet_doc)["part"]["dieConfiguration"] = "array"
    assert_invalid(sas_validator, mosfet_doc, contains="'dies' is a required property")


@pytest.mark.parametrize("value", ["dual", "complementary", "array"])
def test_igbt_multi_die_configuration_rejected(sas_validator, value):
    doc = {"igbt": {"manufacturerInfo": {"name": "X", "datasheetInfo": {
        "part": {"partNumber": "X1", "technology": "Si", "dieConfiguration": value},
        "electrical": {"collectorEmitterVoltage": 1200, "collectorEmitterSaturation": 1.7,
                       "continuousCollectorCurrent": 40}}}}}
    assert_invalid(sas_validator, doc)
    doc["igbt"]["manufacturerInfo"]["datasheetInfo"]["part"]["dieConfiguration"] = "single"
    assert_valid(sas_validator, doc)


# ---------------------------------------------------------------------------
# Resistor-equipped ("pre-biased", "digital", BRT/RET) BJTs: electrical.biasResistors
# and the input-voltage fields. The presence of biasResistors is the only marker.
# ---------------------------------------------------------------------------

PREBIAS_KEYS = ("biasResistors", "inputOnVoltage", "inputOnVoltageVce", "inputOnVoltageIc",
                "inputOffVoltage", "inputOffVoltageVce", "inputOffVoltageIc", "inputVoltageMax",
                "inputReverseVoltageMax", "outputCurrentMax")


@pytest.fixture
def brt_pair_doc():
    return _load(EXAMPLES_DIR / "07_bjt_prebiased_dual_pumh11.json")


@pytest.fixture
def brt_single_doc(brt_pair_doc):
    """The PUMH11's TR1 block as a single-die record (package electrical)."""
    di = _bjt_di(brt_pair_doc)
    di["electrical"] = copy.deepcopy(di.pop("dies")[0]["electrical"])
    di.pop("packagePowerDissipation")
    di["part"].pop("dieConfiguration")
    di["part"].pop("internalConnection")
    di["mechanical"]["pinout"] = di["mechanical"]["pinout"][:3]
    return brt_pair_doc


def _brt_el(doc):
    return _bjt_di(doc)["electrical"]


def _plain(doc):
    for k in PREBIAS_KEYS:
        _brt_el(doc).pop(k, None)
    return doc


def test_brt_pair_example_validates(sas_validator, brt_pair_doc):
    assert_valid(sas_validator, brt_pair_doc)


def test_brt_pair_example_is_per_die(brt_pair_doc):
    di = _bjt_di(brt_pair_doc)
    assert "electrical" not in di
    for die in di["dies"]:
        br = die["electrical"]["biasResistors"]
        assert br["resistanceRatioDefinition"] == "R2/R1"
        # Nexperia prints VI(on) 'Min 2.5' (the guarantee) -> the distribution's maximum.
        assert die["electrical"]["inputOnVoltage"] == {"nominal": 1.8, "maximum": 2.5}
        assert die["electrical"]["inputOffVoltage"] == {"minimum": 0.8, "nominal": 1.1}


def test_brt_single_die_validates(sas_validator, brt_single_doc):
    assert_valid(sas_validator, brt_single_doc)
    _bjt_di(brt_single_doc)["part"]["dieConfiguration"] = "single"
    assert_valid(sas_validator, brt_single_doc)


def test_brt_plain_record_without_prebias_fields_valid(sas_validator, brt_single_doc):
    assert_valid(sas_validator, _plain(brt_single_doc))


@pytest.mark.parametrize("drop, missing", [
    ("resistanceRatioDefinition", "'resistanceRatioDefinition' is a dependency of 'resistanceRatio'"),
    ("baseEmitterResistance", "'baseEmitterResistance' is a dependency of 'resistanceRatio'"),
    ("resistanceRatio", "'resistanceRatio' is a dependency of 'resistanceRatioDefinition'"),
])
def test_brt_ratio_dependencies(sas_validator, brt_single_doc, drop, missing):
    _brt_el(brt_single_doc)["biasResistors"].pop(drop)
    assert_invalid(sas_validator, brt_single_doc, contains=missing)


def test_brt_ratio_direction_enum_closed(sas_validator, brt_single_doc):
    _brt_el(brt_single_doc)["biasResistors"]["resistanceRatioDefinition"] = "R1:R2"
    assert_invalid(sas_validator, brt_single_doc, contains="is not one of")


def test_brt_ratio_r1_over_r2_accepted(sas_validator, brt_single_doc):
    _brt_el(brt_single_doc)["biasResistors"]["resistanceRatioDefinition"] = "R1/R2"
    assert_valid(sas_validator, brt_single_doc)


def test_brt_empty_bias_resistors_rejected(sas_validator, brt_single_doc):
    """biasResistors needs R1 or R2 (anyOf): an empty block cannot mark a part as pre-biased."""
    _brt_el(brt_single_doc)["biasResistors"] = {}
    assert_invalid(sas_validator, brt_single_doc, contains="{} is not valid under any of the given schemas")


def test_brt_bias_resistors_closed(sas_validator, brt_single_doc):
    _brt_el(brt_single_doc)["biasResistors"]["tolerancePercent"] = 30
    assert_invalid(sas_validator, brt_single_doc, contains="'tolerancePercent' was unexpected")


def test_brt_r1_only_and_r2_only(sas_validator, brt_single_doc):
    el = _brt_el(brt_single_doc)
    el["biasResistors"] = {"baseResistance": {"minimum": 7000, "nominal": 10000, "maximum": 13000}}
    assert_valid(sas_validator, brt_single_doc)
    el["biasResistors"] = {"baseEmitterResistance": {"nominal": 10000}}
    assert_valid(sas_validator, brt_single_doc)


def test_brt_resistance_must_be_dimension(sas_validator, brt_single_doc):
    _brt_el(brt_single_doc)["biasResistors"]["baseResistance"] = 10000
    assert_invalid(sas_validator, brt_single_doc, contains="is not of type 'object'")


@pytest.mark.parametrize("field, value", [
    ("inputOnVoltage", {"nominal": 1.8, "maximum": 2.5}),
    ("inputOffVoltage", {"minimum": 0.8}),
    ("inputVoltageMax", 40),
    ("inputReverseVoltageMax", 10),
    ("outputCurrentMax", 0.05),
])
def test_brt_input_fields_require_bias_resistors(sas_validator, brt_single_doc, field, value):
    doc = _plain(brt_single_doc)
    _brt_el(doc)[field] = value
    assert_invalid(sas_validator, doc, contains=f"'biasResistors' is a dependency of '{field}'")


@pytest.mark.parametrize("cond, value", [
    ("inputOnVoltageVce", "inputOnVoltage"), ("inputOnVoltageIc", "inputOnVoltage"),
    ("inputOffVoltageVce", "inputOffVoltage"), ("inputOffVoltageIc", "inputOffVoltage"),
])
def test_brt_condition_requires_its_voltage(sas_validator, brt_single_doc, cond, value):
    el = _brt_el(brt_single_doc)
    el.pop(value)
    for k in (value + "Vce", value + "Ic"):
        if k != cond:
            el.pop(k)
    assert_invalid(sas_validator, brt_single_doc, contains=f"'{value}' is a dependency of '{cond}'")


def test_brt_input_voltage_shapes(sas_validator, brt_single_doc):
    el = _brt_el(brt_single_doc)
    el["inputOnVoltageVce"] = 0
    assert_invalid(sas_validator, brt_single_doc, contains="less than or equal to the minimum")
    el["inputOnVoltageVce"] = 0.3
    el["inputOnVoltage"] = 2.5
    assert_invalid(sas_validator, brt_single_doc, contains="is not of type 'object'")


@pytest.mark.parametrize("cfg", ["dual", "complementary", "array"])
def test_brt_multi_die_forbids_package_bias_resistors(sas_validator, brt_single_doc, cfg):
    di = _bjt_di(brt_single_doc)
    di["part"]["dieConfiguration"] = cfg
    if cfg == "complementary":
        di["part"].pop("subType")
    assert_invalid(sas_validator, brt_single_doc, contains="'dies' is a required property")


def test_brt_multi_die_plain_package_block_rejected(sas_validator, brt_single_doc):
    doc = _plain(brt_single_doc)
    _bjt_di(doc)["part"]["dieConfiguration"] = "dual"
    assert_invalid(sas_validator, doc, contains="'dies' is a required property")


def test_brt_mixed_pair(sas_validator, brt_pair_doc):
    for k in PREBIAS_KEYS:
        _bjt_di(brt_pair_doc)["dies"][1]["electrical"].pop(k, None)
    assert_valid(sas_validator, brt_pair_doc)


def test_brt_complementary_pair_with_different_resistors(sas_validator, brt_pair_doc):
    di = _bjt_di(brt_pair_doc)
    di["part"]["dieConfiguration"] = "complementary"
    di["part"].pop("subType")
    di["dies"][1]["subType"] = "pnp"
    di["dies"][1]["electrical"]["biasResistors"] = {
        "baseResistance": {"minimum": 7000, "nominal": 10000, "maximum": 13000},
        "baseEmitterResistance": {"nominal": 47000},
        "resistanceRatio": {"minimum": 3.7, "nominal": 4.7, "maximum": 5.7},
        "resistanceRatioDefinition": "R2/R1"}
    assert_valid(sas_validator, brt_pair_doc)


def test_brt_bias_resistors_outside_electrical_rejected(sas_validator, brt_pair_doc):
    di = _bjt_di(brt_pair_doc)
    br = copy.deepcopy(di["dies"][0]["electrical"]["biasResistors"])
    di["dies"][0]["biasResistors"] = br
    assert_invalid(sas_validator, brt_pair_doc, contains="'biasResistors' was unexpected")
    di["dies"][0].pop("biasResistors")
    di["biasResistors"] = br
    assert_invalid(sas_validator, brt_pair_doc, contains="'biasResistors' was unexpected")


def test_common_emitter_pair_may_share_a_pin(sas_validator, brt_pair_doc):
    """A shared emitter pin is listed by both die (dieBase.pins); the schema does not forbid it."""
    di = _bjt_di(brt_pair_doc)
    di["part"]["internalConnection"] = "commonEmitter"
    di["dies"][0]["pins"] = ["1", "2", "6"]
    di["dies"][1]["pins"] = ["1", "3", "5"]
    assert_valid(sas_validator, brt_pair_doc)


# ---------------------------------------------------------------------------
# Thyristor / JFET / optocoupler kinds (2026-10)
# ---------------------------------------------------------------------------

NEW_KIND_EXAMPLES = {
    "08_thyristor_scr_bt151_500r.json": "thyristor",
    "09_thyristor_triac_bta16_600b.json": "thyristor",
    "10_thyristor_protector_tisp4350h3bj.json": "thyristor",
    "11_optocoupler_vo617a_3.json": "optocoupler",
    "12_jfet_jfe150.json": "jfet",
}


def _ex(name):
    return _load(EXAMPLES_DIR / name)


def _di(doc):
    return doc[next(iter(doc))]["manufacturerInfo"]["datasheetInfo"]


def assert_invalid_deep(validator, doc, contains):
    """Like assert_invalid, but also searches the nested oneOf/anyOf branch errors, where the
    reason a body fails a kind's rule actually lives."""
    errs = list(validator.iter_errors(doc))
    assert errs, "expected invalid, got no errors"
    msgs, stack = [], list(errs)
    while stack:
        e = stack.pop()
        msgs.append(e.message)
        stack.extend(e.context or [])
    assert any(contains in m for m in msgs), f"expected an error containing {contains!r}"


@pytest.mark.parametrize("name, kind", NEW_KIND_EXAMPLES.items())
def test_new_kind_example_validates(sas_validator, name, kind):
    doc = _ex(name)
    assert list(doc) == [kind]
    assert_valid(sas_validator, doc)


@pytest.mark.parametrize("kind", ["thyristor", "jfet", "optocoupler"])
def test_new_kind_seed_valid(sas_validator, kind):
    assert_valid(sas_validator, {kind: {}})


def test_two_new_kinds_in_one_document_rejected(sas_validator):
    doc = {"thyristor": _ex("08_thyristor_scr_bt151_500r.json")["thyristor"],
           "jfet": _ex("12_jfet_jfe150.json")["jfet"]}
    assert_invalid(sas_validator, doc, contains="is valid under each of")


def test_thyristor_subtype_closed(sas_validator):
    doc = _ex("08_thyristor_scr_bt151_500r.json")
    _di(doc)["part"]["subType"] = "tvs"
    assert_invalid(sas_validator, doc, contains="is not one of")


def test_quadrant_ratings_are_triac_only(sas_validator):
    doc = _ex("08_thyristor_scr_bt151_500r.json")
    _di(doc)["electrical"]["quadrantRatings"] = [{"quadrant": "Q1", "gateTriggerCurrent": {"maximum": 0.015}}]
    assert_invalid(sas_validator, doc, contains="should not be valid under")


def test_triac_requires_rms_on_state_current(sas_validator):
    doc = _ex("09_thyristor_triac_bta16_600b.json")
    _di(doc)["electrical"].pop("rmsOnStateCurrent")
    assert_invalid(sas_validator, doc, contains="'rmsOnStateCurrent' is a required property")


def test_triac_pinout_uses_main_terminals(sas_validator):
    doc = _ex("09_thyristor_triac_bta16_600b.json")
    funcs = {p.get("function") for p in _di(doc)["mechanical"]["pinout"]}
    assert {"mainTerminal1", "mainTerminal2", "gate"} <= funcs


def test_surge_protector_requires_peak_pulse_currents(sas_validator):
    doc = _ex("10_thyristor_protector_tisp4350h3bj.json")
    _di(doc)["electrical"].pop("peakPulseCurrents")
    assert_invalid(sas_validator, doc, contains="'peakPulseCurrents' is a required property")


def test_protector_example_keeps_every_printed_waveform():
    doc = _ex("10_thyristor_protector_tisp4350h3bj.json")
    wf = [r["waveform"] for r in _di(doc)["electrical"]["peakPulseCurrents"]]
    assert {"5/310", "5/200", "0.2/310"} <= set(wf)


def test_impulse_rating_requires_its_waveform(sas_validator):
    doc = _ex("10_thyristor_protector_tisp4350h3bj.json")
    _di(doc)["electrical"]["peakPulseCurrents"].append({"current": 100})
    assert_invalid(sas_validator, doc, contains="'waveform' is a required property")


@pytest.mark.parametrize("bad", ["10x1000", "10/1000us", ""])
def test_impulse_rating_unknown_waveform_rejected(sas_validator, bad):
    doc = _ex("10_thyristor_protector_tisp4350h3bj.json")
    _di(doc)["electrical"]["peakPulseCurrents"][0]["waveform"] = bad
    assert_invalid(sas_validator, doc, contains="is not one of")


def test_surge_on_state_current_requires_shape(sas_validator):
    doc = _ex("08_thyristor_scr_bt151_500r.json")
    _di(doc)["electrical"]["surgeOnStateCurrent"][0].pop("shape")
    assert_invalid(sas_validator, doc, contains="'shape' is a required property")


def test_isolation_capacitance_requires_isolation_voltage(sas_validator):
    doc = _ex("08_thyristor_scr_bt151_500r.json")
    _di(doc)["electrical"]["isolationCapacitance"] = 1e-11
    assert_invalid(sas_validator, doc, contains="'isolationVoltage' is a dependency")


def test_dual_thyristor_requires_dies(sas_validator):
    doc = _ex("08_thyristor_scr_bt151_500r.json")
    _di(doc)["part"]["dieConfiguration"] = "dual"
    assert_invalid(sas_validator, doc, contains="'dies' is a required property")


def _dual_protector():
    """Synthetic STRUCTURE fixture (not a catalogue part): two copies of the TISP die block."""
    doc = _ex("10_thyristor_protector_tisp4350h3bj.json")
    di = _di(doc)
    di["part"]["dieConfiguration"] = "dual"
    di["dies"] = [{"name": n, "electrical": copy.deepcopy(di["electrical"])} for n in ("line A", "line B")]
    return doc


def test_dual_protector_described_per_die(sas_validator):
    doc = _dual_protector()
    _di(doc).pop("electrical")
    assert_valid(sas_validator, doc)


def test_thyristor_dies_beside_package_electrical_rejected(sas_validator):
    assert_invalid_deep(sas_validator, _dual_protector(), contains="should not be valid under")


def test_jfet_requires_a_drain_voltage_rating(sas_validator):
    doc = _ex("12_jfet_jfe150.json")
    el = _di(doc)["electrical"]
    el.pop("drainSourceVoltage")
    assert_valid(sas_validator, doc)          # V_DG alone is enough (small-signal JFETs)
    el.pop("gateDrainVoltageMax")
    assert_invalid_deep(sas_validator, doc, contains="is a required property")


def _dual_jfet():
    """Synthetic STRUCTURE fixture: the JFE150 die block twice, with one matching spec."""
    doc = _ex("12_jfet_jfe150.json")
    di = _di(doc)
    di["part"]["dieConfiguration"] = "dual"
    di["dies"] = [{"name": n, "electrical": copy.deepcopy(di["electrical"])} for n in ("Q1", "Q2")]
    di.pop("electrical")
    di["matching"] = [{"gateSourceVoltageMatch": {"maximum": 0.02}, "testDrainCurrent": 1e-3}]
    return doc


def test_dual_jfet_with_matching_valid(sas_validator):
    assert_valid(sas_validator, _dual_jfet())


def test_jfet_matching_requires_dies(sas_validator):
    doc = _ex("12_jfet_jfe150.json")
    _di(doc)["matching"] = [{"gateSourceVoltageMatch": {"maximum": 0.02}}]
    assert_invalid(sas_validator, doc, contains="'dies' is a required property")


def test_jfet_internal_connection_narrowed(sas_validator):
    doc = _dual_jfet()
    _di(doc)["part"]["internalConnection"] = "commonSource"
    assert_invalid(sas_validator, doc, contains="is not one of")


def test_jfet_matching_entry_needs_a_quantity(sas_validator):
    doc = _dual_jfet()
    _di(doc)["matching"] = [{"testDrainCurrent": 1e-3}]
    assert_invalid_deep(sas_validator, doc, contains="is a required property")


def test_optocoupler_requires_isolation_voltage(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    _di(doc)["electrical"]["isolation"].pop("withstandVoltageRms")
    assert_invalid(sas_validator, doc, contains="'withstandVoltageRms' is a required property")


def test_optocoupler_requires_electrical(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    _di(doc).pop("electrical")
    assert_invalid(sas_validator, doc, contains="'electrical' is a required property")


def test_phototransistor_requires_ctr(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    el = _di(doc)["electrical"]
    for k in ("currentTransferRatio", "currentTransferRatioForwardCurrent", "currentTransferRatioVce"):
        el.pop(k)
    assert_invalid(sas_validator, doc, contains="'currentTransferRatio' is a required property")


def test_bipolar_output_fields_refused_on_logic_output(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    _di(doc)["part"]["subType"] = "logicOutput"
    assert_invalid(sas_validator, doc, contains="should not be valid under")


def test_zero_crossing_is_photothyristor_only(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    _di(doc)["electrical"]["zeroCrossing"] = True
    assert_invalid(sas_validator, doc, contains="should not be valid under")


def test_optocoupler_has_no_die_configuration(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    _di(doc)["part"]["dieConfiguration"] = "dual"
    assert_invalid(sas_validator, doc, contains="should not be valid under {}")


def test_optocoupler_isolation_is_the_shared_peas_block(sas_validator):
    doc = _ex("11_optocoupler_vo617a_3.json")
    _di(doc)["electrical"]["isolation"]["isolationVoltage"] = 5300
    assert_invalid(sas_validator, doc, contains="'isolationVoltage' was unexpected")


def test_optocoupler_ctr_is_a_fraction_in_the_example():
    """CTR is stored as a fraction (100 % = 1.0); the schema cannot tell percent from fraction,
    so the ingest gate bounds it. The example must follow the rule."""
    ctr = _di(_ex("11_optocoupler_vo617a_3.json"))["electrical"]["currentTransferRatio"]
    assert ctr == {"minimum": 1.0, "maximum": 2.0}


@pytest.mark.parametrize("kind, extra", [
    ("thyristor", {"thyristorType": "triac", "ratedOffStateVoltage": 600}),
    ("jfet", {"channel": "nChannel", "ratedDrainSourceVoltage": 30}),
    ("optocoupler", {"outputType": "phototransistor", "minimumIsolationVoltage": 5000,
                     "role": "isolatedFeedback"}),
])
def test_design_requirements_new_kinds(sas_validator, mosfet_doc, kind, extra):
    mosfet_doc["inputs"]["designRequirements"] = {"deviceType": kind, **extra}
    assert_valid(sas_validator, mosfet_doc)


def test_design_requirements_thyristor_type_anchored(sas_validator, mosfet_doc):
    mosfet_doc["inputs"]["designRequirements"] = {"deviceType": "thyristor", "thyristorType": "tvs"}
    assert_invalid_deep(sas_validator, mosfet_doc, contains="is not one of")
