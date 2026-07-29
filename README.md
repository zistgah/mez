# mez — the desk

**میز · मेज़** — table.

© 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI. GPL-3.0-or-later.

Local-first. Pure Python standard library — **no pip, no account, no API key, no
cloud**. It runs with the network unplugged and loses only what is genuinely
remote.

## Three rungs, one set of data

| rung | how |
|---|---|
| console | `./mez bearings` — works over ssh, in a tty, with no display |
| 2D | `./mez serve` — a local page on loopback, no framework, no build step |
| immersive | mounted in the Zistgah dome — **not built** |

**The role selects what is shown, never what is computed** (CONTRACT C33).
`?role=clinician` hides engineering surfaces; it does not change one number.

## Start

```
./mez doctor                      # what is built, what is not, what is installed
./mez wbs import ../WBS.csv       # your work breakdown
./mez bearings                    # where you are when you sit down
./mez serve                       # http://127.0.0.1:7373
```

## Your spreadsheet is yours

`wbs import` takes a CSV you edited anywhere — Sheets, Excel, LibreOffice, a text
editor. **A cell you set yourself is never overwritten by an import.** Re-import a
regenerated skeleton as often as you like; your Priority, Status and Notes
survive. `--force` if you actually mean to lose them.

CSV, not an integration. No OAuth, no account, nothing to be locked out of
(CONTRACT C32).

## Seeding a conversation

Tick rows, choose a provider, and the prompt is built from your own breakdown.
Providers are data — remove every one of them and the desk still works, it just
stops seeding. `local` needs no network and no account at all.

## What is not built

`./mez doctor` prints it. The six that remained are now wired local-first:
mail reads a local Maildir/mbox and composes to an outbox; msg and social
queue to that outbox and send only through a transport you configure;
meetings parses a local .ics and summarises a transcript via `mez ai` (your
ollama); classes plans from a syllabus. `samd` scaffolds the C34 evidence
framework and certifies nothing — doctor prints it as a framework, not as
built. `mez ai` talks only to a model you run.

Four that were on this list are now wired — and they were never builds. CHAKRA,
research-kundali, TransEg and the dome already existed; the desk calls them and
computes none of it. `embody` is wired but has not been run against a live
gateway from here, so `doctor` prints it apart from the rest (CONTRACT C37).

They are named because they are coming, and marked because they are not here.

## Where your data lives

`$MEZ_HOME`, default `~/.mez`. Plain JSON and CSV. Delete the directory and
nothing else in the world changes.
