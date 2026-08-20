# `mez studio` — the spine

```
mez studio               the console rung: what is mounted, what is reachable
mez studio serve         the IDE rung on 127.0.0.1:7373
mez studio dome          the immersive rung, mounted from zistgah/dome
mez studio mount <id>    what to type for that one
mez studio doctor        present · on disk and idle · not reachable
```

## A spine, not an application

It **mounts**. It does not reimplement. Kitab, the six cyclers, the AAB painter, the dome, misty
and the estate tooling all keep their own repos, their own studios and their own contracts. This
gives you a place to stand and a way to reach them.

That distinction is the correction. The recurring defect here has been a capability that exists in
the estate and cannot be reached from the desk — chakra, research-kundali and transeg were each
once marked "not built" while running. **A wiring gap is not a missing build**, and a spine that
reimplemented its components would create the drift it exists to prevent.

## Three rungs

| | |
|---|---|
| **console** | the CLI. Everything is here first. |
| **ide** | rail on the left, the component's own surface in the middle, the estate's state on the right |
| **dome** | the immersive rung, mounted from `zistgah/dome` |

The rung changes what is **shown**, never what is computed. A console user and a dome user get the
same numbers. Your role picks a default rung; it does not gate a capability.

## Four states, and the middle two matter

| | |
|---|---|
| ● **live** | answering on its port right now |
| ○ **present** | on disk, its server is not running — a **wiring gap** |
| × **absent** | not reachable; it tells you the four places it looked and the `git clone` line |

Nothing absent is ever framed. There is no stub that looks alive.

## Drop-in components

`config/components.json` is **data**. Adding a component means adding an entry — it does not mean
editing `mez_studio.py`, and a self-test asserts that **no component id appears in the spine's
code**. Delete the registry and the spine still runs.

Each entry declares what it is, which rungs it appears on, how the spine reaches it (`static`,
`serve`, `cli`, `panel`, `dome`), and its own `guidance` — which shows whether the component is
present or absent, because it is the recovery path as much as the manual.

`/local/<id>/<path>` serves a component's own files **from its own repo**. No copy is made, and a
path that tries to climb out of the component is refused.

## What is mounted now

**compose** kitab · genie · **cycler** matba · khwab · awaz · tilasm · pench · yadein ·
**make** aab painter · dome · **operate** estate · misty · chakra

## The three panels that carry corrections

The **DOI** panel: `misty ots stamp <path>` — `ots` takes a subcommand, one path, no globs. And a
new plate for an existing corpus is a **version**, not a new deposit; splitting a lineage is not
undoable without the registrar. Both cost real deposits to learn.

The **estate** panel: the twelve stages are zops's — init → preflight → clone-or-reuse → contract →
diff → gate → receipt → stamp → reseal → push → mark → done. The spine calls them. It also names
the live defect: `_z_create_remote_if_needed` is defined in canonical zops and never called, so
create the remote explicitly before any seal.

The **dome** panel: one library, one world config per zistgah, **never a fork**. Any code that
branches on world identity is a redundancy defect. Vehicles swap physics profiles through one
flight seam, not three controllers, and the orrery reuses chakra-core's ephemeris rather than
growing a second one.
