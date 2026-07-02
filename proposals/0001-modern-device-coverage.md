# SAS-RFC 0001 — Modern-device coverage (SiC/GaN gate ratings, IGBT co-pack, modules)

- **Status:** Draft (stub — from the 2026-07 workspace review, scoped but not designed)
- **Created:** 2026-07-02

## Problem

The current device schemas cannot faithfully carry several mainstream modern parts:

1. **Asymmetric gate ratings** — `gateSourceVoltageMax` is a single number; SiC MOSFETs are
   rated e.g. −8/+19 V and GaN gates are similarly asymmetric. No recommended V_GS(on)/(off)
   fields exist either.
2. **GaN device structure** — only `technology: "GaN"`; enhancement-mode vs cascode vs
   depletion is not representable, though drive requirements differ fundamentally.
3. **IGBT co-packed diode** — no fields for the anti-parallel diode (V_F, t_rr/Q_rr), though
   the TAS catalog already carries co-pack parts (e.g. IXGH48N60A3D1).
4. **IGBT electrical thinness** — no switching times (t_d/t_r/t_f), no C_oes/C_res, no
   I_C(100°C)/I_CM, unlike the MOSFET schema.
5. **Multi-die / modules / half-bridges** — no representation at all; data resorts to
   `subType: "powerBlock"` on single-die shapes.

## Direction (to be designed)

Asymmetric ratings as `{minimum, maximum}` pairs on the gate fields; a GaN `structure` enum;
an optional closed `copackDiode` object on igbt (and mosfet, for co-pack SiC Schottky);
a `module` representation (probably a new discriminator carrying die references + topology
enum half/full-bridge/sixpack) rather than overloading the single-die files.
