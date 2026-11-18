const assert = require("node:assert/strict");
const fs = require("node:fs");
const path = require("node:path");
const vm = require("node:vm");
const {test} = require("node:test");
const ts = require("typescript");

// Exercise the real TS helper in Node while mocking only the source allowlists.
const filename = path.join(__dirname, "../lib/research-permalink.ts");
const compiled = ts.transpileModule(fs.readFileSync(filename, "utf8"), {
  compilerOptions: {module: ts.ModuleKind.CommonJS, target: ts.ScriptTarget.ES2020},
}).outputText;
const moduleRef = {exports: {}};
const sourceCodes = ["ape", "eye", "europeana", "kavi"];
const metrics = ["video_links_total", "institutions", "institutions_with_video_links",
  "videos_in_curatorial_catalog", "countries_with_videos"];
vm.runInNewContext(compiled, {
  module: moduleRef,
  exports: moduleRef.exports,
  URLSearchParams,
  require(specifier) {
    if (specifier === "@/lib/corpus-comparison") return {
      comparisonSources: sourceCodes, comparisonMetrics: metrics,
    };
    throw new Error("Unexpected dependency: " + specifier);
  },
}, {filename});
const {decodeResearchSlice, encodeResearchSlice} = moduleRef.exports;

test("round-trip: same URL restores selected sources, filters, chart and language", () => {
  const slice = {
    sources: ["eye", "ape", "europeana"],
    view: "timeline", dimension: "country", metric: "institutions",
    query: "cinéma européen", sharedOnly: true, locale: "es",
  };
  const url = encodeResearchSlice(slice);
  assert.equal(url.get("a"), "eye");
  assert.equal(url.get("b"), "ape");
  assert.equal(url.get("c"), "europeana");
  assert.equal(url.get("lang"), "es");
  assert.deepEqual(JSON.parse(JSON.stringify(decodeResearchSlice(new URLSearchParams(url.toString())))), slice);
  assert.equal(encodeResearchSlice(decodeResearchSlice(url)).toString(), url.toString());
});

test("reject unknown corpora and duplicate selections without accepting identifiers", () => {
  const decoded = decodeResearchSlice(new URLSearchParams(
    "a=ape&b=ape&c=../../secret&metric=window.location&dimension=sql&view=DELETE&lang=xx&shared=true"));
  assert.equal(decoded.sources[0], "ape");
  assert.equal(new Set(decoded.sources.filter(Boolean)).size, 2);
  assert.ok(decoded.sources.every(source => !source || sourceCodes.includes(source)));
  assert.equal(decoded.metric, "video_links_total");
  assert.equal(decoded.dimension, "theme");
  assert.equal(decoded.view, "distributions");
  assert.equal(decoded.locale, "pt");
  assert.equal(decoded.sharedOnly, false);
});

test("strip control characters and limit the search term to 96 characters", () => {
  const parsed = decodeResearchSlice(new URLSearchParams({q: "\u0000abc\u001F" + "x".repeat(300)}));
  assert.ok(parsed.query.startsWith("abc"));
  assert.equal(parsed.query.length, 96);
  assert.ok(!parsed.query.includes("\u0000"));
});

test("two-source selection remains valid without optional third source", () => {
  const params = new URLSearchParams("a=ape&b=eye&lang=en");
  const s = decodeResearchSlice(params);
  assert.deepEqual(Array.from(s.sources), ["ape","eye",""]);
  const regenerated = encodeResearchSlice(s);
  assert.equal(regenerated.get("c"), null);
  assert.equal(regenerated.get("lang"), "en");
});
