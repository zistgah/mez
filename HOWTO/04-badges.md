# `mez badges` — our numbers, against a standard we did not invent

```
mez badges                       full table
mez badges --brief               the four counts
mez badges --estate /path
```

## The benchmark

**ACM Artifact Review and Badging v1.1**, the **NISO Recommended Practice on Reproducibility
Badging and Definitions**, and the **FAIR4RS Principles**. Four levels:

| badge | what it means |
|---|---|
| **Available** | archived in a public repository that assigns a DOI and guarantees persistence, under an open licence |
| **Functional** | documented, consistent, complete, exercisable, with evidence of verification and validation |
| **Reusable** | Functional, *and* packaged so others can reuse and repurpose it |
| **Results Reproduced** | an independent party regenerated the results |

The vocabulary underneath: *repeatability* is the same team and setup, *replicability* a different
team with the same setup, *reproducibility* a different team with a different setup, *reusability*
documentation and structure good enough that reuse is facilitated.

## What this tool will not do

**It never awards Results Reproduced.** By definition that badge requires a party other than the
author, and a badge awarded by its own author is not a badge. The scorer prints a dash and says so.

It scores from **evidence on disk**, and an absent file is an absent badge — no benefit of the
doubt. A placeholder DOI is not a DOI: a tail of `NNNNNNNN` on a real prefix scores zero, which is
exactly the defect once found live in a public README.

## The caveat that belongs on the record

A badge is a **scoped, disclosed certification, not a general seal of research quality.**
*Available* says nothing about whether the artifact works. *Functional* says nothing about whether
the conclusions are correct beyond what was checked. Anyone relying on a badge before building on
the work should check which badge, and what that committee actually verified.

## Closing the gaps

The table's last column names what is missing per repository. In practice the cheapest moves are:
a `CITATION.cff`, a `CONTRACT.md` and `CONTEXT.md` stating what the thing promises and refuses, an
entry point under `docs/`, and a test file that actually runs. Those four turn *Functional* into
*Reusable* without touching the science.

## References

- ACM, *Artifact Review and Badging* v1.1 — acm.org/publications/policies/artifact-review-badging
- NISO, *Reproducibility Badging and Definitions* (Recommended Practice)
- Chue Hong, Katz, Barker et al., *FAIR Principles for Research Software (FAIR4RS)*
- Méndez, Graziotin, Wagner, Seibold, *Open Science in Software Engineering*, arXiv:1904.06499
