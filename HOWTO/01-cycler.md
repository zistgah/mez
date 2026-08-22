# `mez cycler` — the six output cyclers

Classified by **what comes out**, not by what goes in.

```
mez cycler            list them
mez cycler tilasm     how to run that one
```

| | output | |
|---|---|---|
| **matba** مطبع | print | books, papers, posters, manuals, filings |
| **khwab** خواب | visual | images, skits, features, series |
| **awaz** آواز | audio | songs, podcasts, lectures, oral history |
| **tilasm** طلسم | immersive | AR, XR, VR — stations a person can be in |
| **pench** پیچ | embodied | robotics, cyberphysical, sim2real, real2sim |
| **yadein** یادیں | record | a multimodal diary, staggered, toward TransEg |

## What is shared, and what is emphatically not

The **engine** is common: the clipboard loop, the answer routing, the artefact inbox, the AI
source table. Byte for byte, in all six.

The **workflow is not**, and treating it as shared was an error that reached six live DOIs. Each
cycler declares its own purpose, contract, context, state, invariants, failure modes, evidence
requirements, workflow and artifact model. A test refuses to build a page that borrows a sibling's
vocabulary — a station has no timeline, and a diary entry is not a cued span of a media file.

## Running one

```bash
curl -O https://raw.githubusercontent.com/zistgah/tilasm/main/tilasm.py
python3 tilasm.py serve        # studio at http://127.0.0.1:8713/studio
```

Ports: matba 8710 · khwab 8711 · awaz 8712 · tilasm 8713 · pench 8714 · yadein 8715.

**Composing needs no server at all.** Each studio is a static page: it runs from
`https://zistgah.github.io/<name>/studio.html`, from a folder on your machine, or embedded in
someone else's page. The local server exists only for the parts that touch git and the DOI
registrar.

## The loop

Press 1 — the prompt goes to your clipboard. Paste it into whichever AI you use. Copy the answer.
Press 2 — it **reads your clipboard**, works out which step the answer belongs to from its shape,
files it, and copies the next prompt. You never choose a field.

A binary artefact — a model, a recording, a photograph — comes back through the **artefact inbox**
instead. Three mechanisms, because none works everywhere: the local server reading a folder, the
browser's own folder access, or the platform file picker. The panel says what is **newly visible**;
it never says who made it. Filesystem visibility is not provenance.

## Which AI

`config/ai.config.json` ships **with** links. Edit it, add to it, delete from it. The order is
alphabetical, not a ranking. Two keyless local shapes are included for a server on your own
machine, and answering every step by hand remains allowed. The cycler is not an AI provider and
must stay useful if every commercial service disappears.
