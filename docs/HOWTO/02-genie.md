# `mez genie` — the prompt operating system

> Every prompt must either **CREATE, VERIFY, EXECUTE, MEASURE, FALSIFY or INTEGRATE** an artifact.
> Each cycle must leave behind a more complete, executable artifact than the previous one.

```
mez genie cycle                          the eleven nodes
mez genie modes                          where you can start
mez genie formalize --domain "…"         the prompt for that node
mez genie discover --mode ab-initio
```

## Start from nothing

**ab-initio** is the mode that matters. You have an idea and no artifact; the cycle *constructs*
one. The earlier tools all assumed the artifact already existed and only captioned it — that is
`ingest`, and it is the lesser mode. `correct` starts at FALSIFY: establish the defect first, then
re-enter at the step that produces the component it broke. **Never edit a sealed artifact; make the
next one.**

## The eleven nodes

```
discover   CREATE      a framed opportunity, written down
specify    CREATE      a specification precise enough to be wrong
formalize  CREATE      the formal statement, every line tagged
implement  CREATE      the thing itself — code, a model, a build
verify     VERIFY      a report naming what held and what did not
simulate   EXECUTE     a run, reproducible by someone else
experiment MEASURE     a protocol and a measurement with its uncertainty
falsify    FALSIFY     the smallest test that could kill it, and its result
document   INTEGRATE   the record: method, result, context
audit      VERIFY      a completeness report — what is missing, named
refine     INTEGRATE   the next cycle's starting artifact
```

A step that produces *prose about* a thing is not producing the thing. `validateStep` refuses any
step whose product begins describe / explain / summarise / discuss.

## Every statement carries its status

`DEF · AX · ASSUMP · DER · CONJ · HYP · EMP · OPEN · FAIL`

A hypothesis that arrives untagged will be read as derived, **which would be a lie**. Retrieved,
inferred, proposed and unresolved are kept apart so one never silently contaminates another. Where
you do not know: write UNRESOLVED. Do not supply a plausible value.

## Gates and completeness

A gate returns PASS / FAIL / BLOCKED / PARTIAL. A PASS with no evidence is an assertion, not a
gate, and is refused. A FAIL must name the correction; BLOCKED must name the blocker.

Completeness is reported **per component**, never as one flattering number. The system does not say
"this research is complete". It says which components exist, which are partial, and which do not
exist yet — and when every one is done it says so while noting that done is not the same as correct.

## Time, and the other components the desk calls

`mez cal` calls **project-ilm/chakra** for the panchanga and ten calendars — computed, never looked
up. `mez kundali` calls **research-kundali** (ORCID, OpenAlex, Crossref, DataCite, all keyless).
`mez embody` calls **transeg**. The desk computes none of it, and says so when any of them is
absent rather than fabricating an answer.
