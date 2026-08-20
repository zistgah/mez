# The desk — start here

میز. A desk you own, that runs with the network unplugged.

```bash
./mez bearings     # where you are, in ten seconds
./mez doctor       # what is built, what is wired-but-unproven, what is honestly not built
./mez serve        # the 2D rung on 127.0.0.1:7373
```

Nothing here needs an account, a key or a cloud. `$MEZ_HOME` (default `~/.mez`) holds plain
CSV and JSON, and the export format **is** the storage format.

## What the desk is, and what it is not

The desk composes. It does not compute what another component already computes: it calls
[chakra](02-genie.md) for time, research-kundali for a researcher's own record, transeg for
embodiment. When mez said those were "not built", it was wrong four times over — they existed
and the desk could not reach them. **A wiring gap is not a missing build**, and telling them
apart is most of the work.

## The four new seats at the desk

| | |
|---|---|
| [`mez studio`](05-studio.md) | the spine: CLI, IDE and dome rungs, with everything else as a drop-in |
| [`mez cycler`](01-cycler.md) | the six output cyclers — print, visual, audio, immersive, embodied, record |
| [`mez genie`](02-genie.md) | the prompt operating system: build an artifact from nothing |
| [`mez matrix`](03-matrix.md) | what is reachable, what exists unwired, what is a genuine gap |
| [`mez badges`](04-badges.md) | our numbers, against a standard we did not invent |

## The rules the desk keeps

- **M1** local-first, standard library only.
- **M2 never pretend.** No stub that looks alive. A tab that pretends is worse than one that is
  honest. Anything absent exits 3 and says what is missing.
- **M3 your data is yours.** Plain files. Cells you set by hand are never overwritten by an
  import — `owned.json` records them, and `--force` is required to lose a prioritisation pass.
- **M4** your role changes what is *shown*, never what is computed.
- **M5** no vendor. Providers are data; delete them all and the desk still works.
- **M6** loopback only. Exposing it to a network is a separate, deliberate act.
