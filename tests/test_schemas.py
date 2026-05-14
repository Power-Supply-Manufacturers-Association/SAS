"""Validation tests for the SAS schemas.

Run with:   pytest tests/
or:         python3 -m pytest tests/test_schemas.py -v

Covers:
  * every SAS schema parses and passes Draft 2020-12 meta-validation
  * cross-document $refs resolve (SAS + PEAS schemas registered)
  * the canonical examples validate
  * negative cases:
      - top-level oneOf (must have exactly one of mosfet/diode/igbt/bjt)
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
        schemas["http://openconverters.com/schemas/SAS/SAS.json"],
        registry=registry,
    )


@pytest.fixture
def mosfet_doc():
    return _load(EXAMPLES_DIR / "01_mosfet_ipb017n10n5.json")


@pytest.fixture
def diode_doc():
    return _load(EXAMPLES_DIR / "02_diode_stps30l60ct.json")


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


def test_design_requirements_mosfet_requires_voltage_and_current(sas_validator, mosfet_doc):
    bad = copy.deepcopy(mosfet_doc)
    del bad["inputs"]["designRequirements"]["ratedDrainSourceVoltage"]
    assert_invalid(sas_validator, bad)
    bad = copy.deepcopy(mosfet_doc)
    del bad["inputs"]["designRequirements"]["ratedContinuousDrainCurrent"]
    assert_invalid(sas_validator, bad)


def test_design_requirements_diode_requires_voltage_and_current(sas_validator, diode_doc):
    bad = copy.deepcopy(diode_doc)
    del bad["inputs"]["designRequirements"]["ratedReverseVoltage"]
    assert_invalid(sas_validator, bad)
    bad = copy.deepcopy(diode_doc)
    del bad["inputs"]["designRequirements"]["ratedForwardCurrent"]
    assert_invalid(sas_validator, bad)


def test_unknown_device_type_in_design_requirements_rejected(sas_validator, mosfet_doc):
    mosfet_doc["inputs"]["designRequirements"]["deviceType"] = "thyristor"
    assert_invalid(sas_validator, mosfet_doc)


def test_allowed_technologies_enum(sas_validator, mosfet_doc):
    mosfet_doc["inputs"]["designRequirements"]["allowedTechnologies"] = ["unobtainium"]
    assert_invalid(sas_validator, mosfet_doc)
