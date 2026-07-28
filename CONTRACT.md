# CONTRACT — zistgah/mez

_Thin overlay. The [master](https://github.com/zistgah/governance/blob/main/CONTRACT.md)
governs; this ADDS and never relaxes._

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI.

**M1 — Local-first, and that is load-bearing.** The desk runs with no network, no
account and no API key. A capability that cannot degrade to local is offered, not
depended upon. Standard library only; a pip dependency is a decision, not a
convenience.

**M2 — Never pretend.** Every capability is either working or printed as **not
built**. No stub that looks alive, no tab that fails when it is finally needed.
`mez doctor` is the truth and is part of the interface.

**M3 — His data is his.** Plain CSV and JSON under `$MEZ_HOME`. A cell he set is
never overwritten by an import without `--force`. Deleting the directory breaks
nothing outside it. Export is not a feature, it is the storage format.

**M4 — The role changes the view, never the computation** (master C33). Engineer,
researcher, clinician, teacher, learner, institution, visitor. A clinician does
not pass through an engineering surface to reach clinical function.

**M5 — No vendor, anywhere** (master C32). Providers are data. Remove all of them
and the desk still works. Nothing here holds a credential on anyone's behalf.

**M6 — Loopback only.** `mez serve` binds 127.0.0.1. Exposing the desk to a
network is a separate, deliberate act with its own gate — never a default and
never a flag added quietly.
