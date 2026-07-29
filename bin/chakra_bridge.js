#!/usr/bin/env node
/* mez → CHAKRA bridge.
 * © 1993–2026 Abhishek Choudhary. All rights reserved. AyeAI. GPL-3.0-or-later.
 *
 * Zero computation happens here. It loads CHAKRA's own UMD kernel from the
 * clone it is pointed at and prints moment() as JSON. If CHAKRA is wrong, this
 * is wrong in exactly the same way — which is the point.
 *
 *   node chakra_bridge.js /path/to/chakra '{"refDate":"2026-07-29","lat":17.38}'
 */
var path = require("path");
var repo = process.argv[2];
var init = JSON.parse(process.argv[3] || "{}");
if (!repo) { console.error("usage: chakra_bridge.js <chakra-repo> <init-json>"); process.exit(2); }
var kp = path.join(repo, "src", "chakra-kernel.js");
var K;
try { K = require(kp); }
catch (e) { console.error("cannot load " + kp + "\n" + e.message); process.exit(3); }
if (!K || typeof K.create !== "function") {
  console.error("chakra-kernel.js exposes no create() — its interface changed. Refusing to guess.");
  process.exit(4);
}
try { process.stdout.write(JSON.stringify(K.create(init).moment())); }
catch (e) { console.error("CHAKRA threw during moment():\n" + e.stack); process.exit(5); }
