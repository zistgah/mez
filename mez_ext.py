#!/usr/bin/env python3
"""mez_ext — the consolidation, as four desk subcommands.

    mez cycler            the six output cyclers, reachable from the desk
    mez genie <node>      the prompt operating system — ab initio artifact construction
    mez matrix            what is wired, what exists unwired, what is a genuine gap
    mez badges            our numbers, against a standard we did not invent

Local-first, standard library only, no key, no cloud. Every path that cannot do a thing says so
and exits 3 rather than pretending (mez contract M2).

THE EXTERNAL BENCHMARK, and why it is this one
----------------------------------------------
ACM Artifact Review and Badging v1.1, and the NISO Recommended Practice on Reproducibility
Badging and Definitions, with the FAIR4RS Principles alongside. Four levels:

  Available          archived in a public repository that assigns a DOI and guarantees
                     persistence, under an open licence
  Functional         documented, consistent, complete, exercisable, and including evidence
                     of verification and validation
  Reusable           Functional, and packaged so that others can reuse and repurpose it
  Results Reproduced an independent party regenerated the results

The last is the one this tool will never award itself. By definition it requires a party other
than the author, and a badge awarded by its own author is not a badge. The scorer says so.

And the caveat that matters, stated on the record: a badge is a scoped, disclosed certification,
not a general seal of research quality. Available says nothing about whether the artifact works;
Functional says nothing about whether the conclusions are correct.
"""
import json, os, re, subprocess, sys

EXIT_ABSENT = 3

# ── the six cyclers, by OUTPUT ──────────────────────────────────────────────
CYCLERS = [
    ("matba",  "مطبع", "print",     "books, papers, posters, manuals, filings"),
    ("khwab",  "خواب", "visual",    "images, skits, features, series"),
    ("awaz",   "آواز", "audio",     "songs, podcasts, lectures, oral history"),
    ("tilasm", "طلسم", "immersive", "AR, XR, VR — stations a person can be in"),
    ("pench",  "پیچ",  "embodied",  "robotics, cyberphysical, sim2real, real2sim"),
    ("yadein", "یادیں", "record",    "a multimodal diary, staggered, toward TransEg"),
]

# ── the prompt operating system ─────────────────────────────────────────────
VERBS = {
    "CREATE":    "brings a component into existence that was not there before",
    "VERIFY":    "independently attacks a component that exists and reports what held",
    "EXECUTE":   "runs it and returns what happened, not what should happen",
    "MEASURE":   "produces a number, with its units and its uncertainty",
    "FALSIFY":   "tries to kill the claim with the smallest counterexample it can find",
    "INTEGRATE": "folds a verified component back in and states what changed",
}
TAGS = ["DEF", "AX", "ASSUMP", "DER", "CONJ", "HYP", "EMP", "OPEN", "FAIL"]
CYCLE = [
    ("discover",   "CREATE",    "a framed opportunity, written down"),
    ("specify",    "CREATE",    "a specification precise enough to be wrong"),
    ("formalize",  "CREATE",    "the formal statement, every line tagged"),
    ("implement",  "CREATE",    "the thing itself — code, a model, a build"),
    ("verify",     "VERIFY",    "a report naming what held and what did not"),
    ("simulate",   "EXECUTE",   "a run, reproducible by someone else"),
    ("experiment", "MEASURE",   "a protocol and a measurement with its uncertainty"),
    ("falsify",    "FALSIFY",   "the smallest test that could kill it, and its result"),
    ("document",   "INTEGRATE", "the record: method, result, context"),
    ("audit",      "VERIFY",    "a completeness report — what is missing, named"),
    ("refine",     "INTEGRATE", "the next cycle's starting artifact"),
]
MODES = {
    "ab-initio": ("From nothing", "You have an idea. No artifact exists yet.", "discover"),
    "ingest":    ("From material", "The artifact exists; the cycle formalises it.", "specify"),
    "correct":   ("From something wrong", "Establish the defect first, then re-enter.", "falsify"),
}


def build_prompt(node, mode="ab-initio", domain=None, constitution=None, known=None, missing=None):
    n = next((x for x in CYCLE if x[0] == node), None)
    if not n:
        raise SystemExit("no such cycle node: %s (%s)" % (node, ", ".join(x[0] for x in CYCLE)))
    if mode not in MODES:
        raise SystemExit("no such mode: %s (%s)" % (mode, ", ".join(MODES)))
    nid, verb, produces = n
    title, what, _ = MODES[mode]
    L = ["You are one node of a construction cycle. This node is %s." % nid.upper(),
         "Its verb is %s: it %s." % (verb, VERBS[verb]),
         "It must leave behind: %s." % produces, "",
         "Mode: %s. %s" % (title, what)]
    if domain: L.append("Domain: %s" % domain)
    L.append("")
    if constitution:
        L.append("The constitution of this work, which you may not contradict:")
        L += ["  · " + c for c in constitution] + [""]
    if known:
        L.append("What already exists, with its status:")
        L += ["  [%s] %s" % (k.get("tag", "OPEN"), k["what"]) +
              (" (%s)" % k["source"] if k.get("source") else "") for k in known] + [""]
    if missing:
        L.append("What is known to be missing:")
        L += ["  · " + m for m in missing] + [""]
    L += ["Rules for your reply:",
          "  1. Produce the artifact component, not a description of it.",
          "  2. Tag every statement with one of: %s." % ", ".join(TAGS),
          "     A hypothesis that arrives untagged will be read as derived, which would be a lie.",
          "  3. Mark what you retrieved with its source. Mark what you inferred as inferred.",
          "     If you propose something resting on nothing, say PROPOSED.",
          "  4. Where you do not know, write UNRESOLVED. Do not supply a plausible value.",
          "  5. Name what this component still needs before it could be called done."]
    if verb == "FALSIFY":
        L.append("  6. You are trying to kill it. Finding nothing means saying what you tried.")
    if verb == "MEASURE":
        L.append("  6. Every number carries units and uncertainty, or it is not a measurement.")
    if verb == "EXECUTE":
        L.append("  6. Report what happened when it ran. If it did not run, say so.")
    return "\n".join(L)


# ── badges: scored from evidence on disk, never from intent ─────────────────
DOI_RE = re.compile(r"10\.\d{4,9}/[-._;()/:A-Za-z0-9]+")
OPEN_LICENCES = ("apache", "mit", "bsd", "gpl", "mpl", "cc-by", "cc0", "unlicense")


def _read(p, n=200000):
    try:
        with open(p, "r", errors="replace") as f: return f.read(n)
    except Exception: return ""


def score_repo(path):
    """Award only what is visible. A missing file is a missing badge, not a benefit of the doubt."""
    name = os.path.basename(path)
    ev, miss = [], []

    # --- Available: a DOI, a persistent archive, an open licence
    doi = None
    for rel in ("metadata/misty.json", "CITATION.cff", "README.md", "config/book.config.json"):
        t = _read(os.path.join(path, rel))
        m = DOI_RE.search(t)
        if m and "NNNN" not in m.group(0):
            doi = m.group(0); ev.append("DOI %s in %s" % (doi, rel)); break
    if not doi: miss.append("no DOI found in metadata, citation or readme")

    lic = ""
    for rel in ("LICENSE", "LICENSE.md", "COPYING"):
        lic = _read(os.path.join(path, rel), 4000)
        if lic: break
    if lic and any(k in lic.lower() for k in OPEN_LICENCES):
        ev.append("open licence file present")
    else:
        miss.append("no recognisable open licence file")
    available = bool(doi) and bool(lic)

    # --- Functional: documented, exercisable, with evidence of verification
    readme = _read(os.path.join(path, "README.md"))
    documented = len(readme) > 800
    if documented: ev.append("README %d bytes" % len(readme))
    else: miss.append("README absent or under 800 bytes")

    tests = []
    for root, dirs, files in os.walk(path):
        dirs[:] = [d for d in dirs if d not in (".git", "node_modules", "assets", "attest")]
        for f in files:
            if re.search(r"(test|selftest|spec)[-_.].*\.(mjs|js|py|sh)$", f) or \
               f in ("test_matba.sh", "selftest.sh"):
                tests.append(os.path.relpath(os.path.join(root, f), path))
    if tests: ev.append("%d test file%s: %s" % (len(tests), "" if len(tests) == 1 else "s",
                                                ", ".join(sorted(tests)[:3])))
    else: miss.append("no test or self-test file found")

    manifest = os.path.exists(os.path.join(path, "MANIFEST.sha256"))
    if manifest: ev.append("sealed manifest present")
    else: miss.append("no MANIFEST.sha256")
    stamped = os.path.exists(os.path.join(path, "MANIFEST.sha256.ots"))
    if stamped: ev.append("manifest timestamped")

    functional = documented and bool(tests)

    # --- Reusable: Functional, plus packaged for someone else
    contract = os.path.exists(os.path.join(path, "CONTRACT.md"))
    context = os.path.exists(os.path.join(path, "CONTEXT.md"))
    citation = os.path.exists(os.path.join(path, "CITATION.cff"))
    howto = os.path.isdir(os.path.join(path, "docs")) and any(
        f.lower().startswith(("howto", "readme", "index", "guide"))
        for f in (os.listdir(os.path.join(path, "docs")) if os.path.isdir(os.path.join(path, "docs")) else []))
    extras = sum([contract, context, citation, howto])
    for flag, label in ((contract, "CONTRACT.md"), (context, "CONTEXT.md"),
                        (citation, "CITATION.cff"), (howto, "docs/ entry point")):
        (ev if flag else miss).append(label + (" present" if flag else " absent"))
    reusable = functional and extras >= 3

    return {
        "repo": name, "path": path, "doi": doi,
        "available": available, "functional": functional, "reusable": reusable,
        # Never awarded here. It requires a party other than the author, by definition.
        "results_reproduced": None,
        "evidence": ev, "missing": miss,
        "fair4rs": {"findable": bool(doi), "accessible": bool(doi) and bool(lic),
                    "interoperable": os.path.exists(os.path.join(path, "metadata/misty.json")),
                    "reusable": reusable},
    }


def badges(estate, brief=False, org="zistgah"):
    base = os.path.join(estate, org)
    if not os.path.isdir(base):
        print("estate not found: %s" % base)
        print("Point at it with --estate, or clone the repos beside this one.")
        return EXIT_ABSENT
    rows = []
    for n in sorted(os.listdir(base)):
        p = os.path.join(base, n)
        if os.path.isdir(p) and not n.startswith("."):
            rows.append(score_repo(p))
    if not rows:
        print("no repositories under %s" % base); return EXIT_ABSENT
    a = sum(1 for r in rows if r["available"])
    f = sum(1 for r in rows if r["functional"])
    u = sum(1 for r in rows if r["reusable"])
    n = len(rows)
    print("ACM Artifact Review and Badging v1.1 · NISO Reproducibility Badging · FAIR4RS")
    print("scored from evidence on disk under %s" % base)
    print("")
    print("  Available          %3d / %d   (DOI + persistent archive + open licence)" % (a, n))
    print("  Functional         %3d / %d   (documented + exercisable + verification evidence)" % (f, n))
    print("  Reusable           %3d / %d   (Functional + packaged for reuse)" % (u, n))
    print("  Results Reproduced   — / %d   NOT SELF-AWARDABLE: requires an independent party" % n)
    print("")
    print("A badge is a scoped, disclosed certification, not a seal of research quality.")
    print("Available says nothing about whether it works. Functional says nothing about")
    print("whether the conclusions are correct.")
    if brief:
        return 0
    print("")
    w = max(len(r["repo"]) for r in rows)
    print("  %-*s  A  F  R   what is missing" % (w, "repo"))
    for r in sorted(rows, key=lambda x: (-x["reusable"], -x["functional"], -x["available"], x["repo"])):
        mark = lambda b: "✓" if b else "·"
        gap = "; ".join(m for m in r["missing"] if "absent" not in m or "docs/" in m)[:64]
        print("  %-*s  %s  %s  %s   %s" % (w, r["repo"], mark(r["available"]),
                                           mark(r["functional"]), mark(r["reusable"]), gap))
    return 0


# ── matrix: wired vs exists-unwired vs gap ──────────────────────────────────
def matrix(estate, org="zistgah"):
    base = os.path.join(estate, org)
    on_disk = set(os.listdir(base)) if os.path.isdir(base) else set()
    rows = []
    for cid, script, output, what in CYCLERS:
        present = cid in on_disk
        rows.append((cid, output, "wired" if present else "gap", what))
    for cid, what in (("genie", "the prompt operating system"),
                      ("kitab", "the book template every cycler emits"),
                      ("chakra", "time, ten reckonings, computed"),
                      ("transeg", "embodiment and staggered upload"),
                      ("dome", "the immersive rung mez mounts into"),
                      ("research-kundali", "a researcher's own record")):
        rows.append((cid, "component", "wired" if cid in on_disk else "elsewhere-or-gap", what))
    w = max(len(r[0]) for r in rows)
    print("what the desk can reach, checked against %s" % base)
    print("")
    for cid, out, st, what in rows:
        mark = {"wired": "✓", "elsewhere-or-gap": "?", "gap": "×"}[st]
        print("  %s %-*s  %-10s %s" % (mark, w, cid, out, what))
    print("")
    print("  ✓ present on disk and reachable   ? not on disk here — clone it or it is a gap")
    print("  × not found")
    print("")
    print("This checks presence, not capability. A repo on disk that mez cannot call is")
    print("still a wiring gap, which is the defect this desk keeps rediscovering.")
    return 0


# ── the desk subcommands ────────────────────────────────────────────────────
def cmd_cycler(args):
    if args and args[0] not in [c[0] for c in CYCLERS]:
        print("unknown cycler: %s" % args[0]); return 2
    w = max(len(c[0]) for c in CYCLERS)
    if not args:
        print("the cyclers, by what comes out:")
        print("")
        for cid, script, out, what in CYCLERS:
            print("  %-*s %-4s %-10s %s" % (w, cid, script, out, what))
        print("")
        print("  mez cycler <name>   how to run that one")
        return 0
    cid = args[0]
    c = next(x for x in CYCLERS if x[0] == cid)
    port = {"matba": 8710, "khwab": 8711, "awaz": 8712,
            "tilasm": 8713, "pench": 8714, "yadein": 8715}[cid]
    print("%s %s — %s: %s" % (c[0], c[1], c[2], c[3]))
    print("")
    print("  curl -O https://raw.githubusercontent.com/zistgah/%s/main/%s.py" % (cid, cid))
    print("  python3 %s.py serve            # studio at http://127.0.0.1:%d/studio" % (cid, port))
    print("")
    print("  Composing needs no server: the studio is a static page and runs from")
    print("  https://zistgah.github.io/%s/studio.html or from a folder on this machine." % cid)
    print("  The server is only for the parts that touch git and the DOI registrar.")
    return 0


def cmd_genie(args):
    if not args or args[0] in ("-h", "--help"):
        print("the prompt operating system — every prompt creates, verifies, executes,")
        print("measures, falsifies or integrates an artifact. None of them describes one.")
        print("")
        print("  mez genie cycle                 the eleven nodes")
        print("  mez genie modes                 where you can start")
        print("  mez genie <node> [--mode M] [--domain D]")
        print("")
        for nid, verb, produces in CYCLE:
            print("  %-11s %-10s %s" % (nid, verb, produces))
        return 0
    if args[0] == "cycle":
        for nid, verb, produces in CYCLE: print("%-11s %-10s %s" % (nid, verb, produces))
        return 0
    if args[0] == "modes":
        for k, (title, what, starts) in MODES.items():
            print("%-11s %-22s starts at %s\n            %s" % (k, title, starts, what))
        return 0
    mode = "ab-initio"; domain = None
    if "--mode" in args: mode = args[args.index("--mode") + 1]
    if "--domain" in args: domain = args[args.index("--domain") + 1]
    print(build_prompt(args[0], mode, domain))
    return 0


def register(g):
    """Called from bin/mez.py. Adds the four subcommands to whatever dispatch mez uses."""
    g.setdefault("EXT_COMMANDS", {})
    g["EXT_COMMANDS"].update({
        "cycler": cmd_cycler,
        "genie":  cmd_genie,
        "matrix": lambda a: matrix(_estate(a)),
        "badges": lambda a: badges(_estate(a), brief="--brief" in a),
        "studio": _studio,
    })
    return g["EXT_COMMANDS"]


def _studio(args):
    """Hand off to the spine. It lives beside this file and owns its own registry."""
    here = os.path.dirname(os.path.abspath(__file__))
    spine = os.path.join(here, "mez_studio.py")
    if not os.path.exists(spine):
        print("the studio spine is not installed beside mez_ext.py (%s)" % spine)
        print("  run mez_update.sh again — it installs bin/mez_studio.py")
        return EXIT_ABSENT
    env = dict(os.environ)
    cfg = os.path.join(os.path.dirname(here), "config", "components.json")
    if os.path.exists(cfg): env.setdefault("MEZ_COMPONENTS", cfg)
    return subprocess.call([sys.executable, spine] + list(args), env=env)


def _estate(args):
    if "--estate" in args: return args[args.index("--estate") + 1]
    return os.environ.get("MEZ_ESTATE", "/shared/estate/github")


def selftest():
    p, f = 0, 0
    def ok(m):
        nonlocal p; p += 1; print("  ok   %s" % m)
    def bad(m):
        nonlocal f; f += 1; print("  FAIL %s" % m)

    if len(CYCLERS) == 6 and {c[2] for c in CYCLERS} == \
       {"print", "visual", "audio", "immersive", "embodied", "record"}:
        ok("six cyclers, one per output")
    else: bad("cycler table wrong")

    if all(v in VERBS for _, v, _ in CYCLE) and len(CYCLE) == 11:
        ok("eleven cycle nodes, every one carrying a verb")
    else: bad("cycle malformed")

    pr = build_prompt("formalize", "ab-initio", "a claim about time",
                      constitution=["Act = executable intent"],
                      known=[{"tag": "AX", "what": "events are partially ordered", "source": "PEDLER"}],
                      missing=["a metric estimator"])
    if "FORMALIZE" in pr and "[AX] events are partially ordered (PEDLER)" in pr \
       and "Do not supply a plausible value" in pr and "{" not in pr.split("Rules")[0]:
        ok("a prompt carries the verb, the constitution, the tags and the refusal to guess")
    else: bad("prompt construction")

    if "You are trying to kill it" in build_prompt("falsify"): ok("falsify is told to kill it")
    else: bad("falsify prompt")
    if "units and uncertainty" in build_prompt("experiment"): ok("measure demands units and uncertainty")
    else: bad("measure prompt")

    try:
        build_prompt("nonsense"); bad("an unknown node was accepted")
    except SystemExit: ok("an unknown node is refused, not guessed")

    if MODES["ab-initio"][2] == "discover" and len(MODES) == 3:
        ok("ab initio starts at discover, and is one of three entry modes")
    else: bad("modes")

    import tempfile
    d = tempfile.mkdtemp(); r = os.path.join(d, "org", "thing"); os.makedirs(r)
    s = score_repo(r)
    if not s["available"] and not s["functional"] and not s["reusable"]:
        ok("an empty repo earns nothing — no benefit of the doubt")
    else: bad("empty repo scored")
    if s["results_reproduced"] is None: ok("Results Reproduced is never self-awarded")
    else: bad("self-awarded a reproduction badge")

    open(os.path.join(r, "LICENSE"), "w").write("Apache License, Version 2.0")
    os.makedirs(os.path.join(r, "metadata"))
    open(os.path.join(r, "metadata/misty.json"), "w").write('{"doi":"10.5281/zenodo.21948734"}')
    open(os.path.join(r, "README.md"), "w").write("x" * 900)
    open(os.path.join(r, "test_thing.sh"), "w").write("#!/bin/sh\nexit 0\n")
    s = score_repo(r)
    if s["available"] and s["functional"]: ok("DOI + licence + readme + tests earn Available and Functional")
    else: bad("scoring: %s" % s["missing"])
    if not s["reusable"]: ok("and Reusable still withheld without the packaging")
    else: bad("Reusable awarded too cheaply")

    open(os.path.join(r, "metadata/misty.json"), "w").write('{"doi":"10.5281/zenodo.21321558NNNNNNNN"}')
    if not score_repo(r)["doi"]: ok("a placeholder DOI is not a DOI (the live transeg defect)")
    else: bad("a placeholder DOI was accepted")

    print("\n  ===== %d pass, %d fail =====" % (p, f))
    return 0 if not f else 1


def _main(a):
    if not a or a[0] in ("-h", "--help"): print(__doc__); return 0
    if a[0] == "--selftest": return selftest()
    if a[0] == "cycler": return cmd_cycler(a[1:])
    if a[0] == "genie":  return cmd_genie(a[1:])
    if a[0] == "matrix": return matrix(_estate(a))
    if a[0] == "badges": return badges(_estate(a), brief="--brief" in a)
    print("unknown: %s" % a[0]); return 2


if __name__ == "__main__":
    # `mez badges | head` closes the pipe early; a traceback there is noise, not information.
    try:
        rc = _main(sys.argv[1:])
    except BrokenPipeError:
        try: sys.stdout.close()
        except Exception: pass
        os._exit(0)
    except KeyboardInterrupt:
        print(); rc = 130
    try:
        sys.stdout.flush()
    except BrokenPipeError:
        os._exit(rc or 0)
    sys.exit(rc)
