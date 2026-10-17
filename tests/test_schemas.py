"""Validation tests for the SAS schemas.

Run with:   pytest tests/
or:         python3 -m pytest tests/test_schemas.py -v

Covers:
  * every SAS schema parses and passes Draft 2020-12 meta-validation
  * cross-document $refs resolve (SAS + PEAS schemas registered)
  * the canonical examples validate
  * negative cases:
      - top-level oneOf (must have exactly one of mosfet/diode/igbt/bjt/module)
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
# Top-level oneOf: exactly one of mosfet/diode/igbt/bjt
# ---------------------------------------------------------------------------

def test_missing_device_type_field_invalid(sas_validator, mosfet_doc):
    del mosfet_doc["mosfet"]
    assert_invalid(sas_validator, mosfet_doc)


def test_two_device_type_fields_invalid(sas_validator, mosfet_doc, diode_doc):
    mosfet_doc["diode"] = diode_doc["diode"]
    assert_invalid(sas_validator, mosfet_doc)


def test_unknown_device_type_field_rejected(sas_validator, mosfet_doc):
    mosfet_doc["jfet"] = mosfet_doc.pop("mosfet")
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
    mosfet_doc["inputs"]["designRequirements"]["deviceType"] = "thyristor"
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
