#!/usr/bin/env node
"use strict";
/* MAR: fail-closed integrity gate inside the actual Next.js/Vercel build.
 * Source admission and publication rights remain separate scientific reviews.
 * A new/mutated scientific panel cannot bypass the historical frozen manifest.
 */
const fs = require("node:fs");
const path = require("node:path");
const crypto = require("node:crypto");
const data = path.resolve(__dirname,"..","data");
const lockFile = path.join(data,"scientific-snapshot-lock.json");
const releaseFile = path.join(data,"scientific-release-manifest.json");
function fail(reason) { throw new Error("MAR STATIC BUILD HOLD: " + reason); }
function json(file) {
  try { return JSON.parse(fs.readFileSync(file,"utf8")); }
  catch { return fail("Missing/malformed " + path.basename(file)); }
}
function hash(bytes, algorithm) { return crypto.createHash(algorithm).update(bytes).digest("hex"); }
function gitBlob(bytes) {
  const header = Buffer.from("blob " + bytes.length + "\0");
  return hash(Buffer.concat([header,bytes]),"sha1");
}
function fileFor(rel) {
  if (!/^site\/data\/[a-z0-9-]+\.json$/.test(rel)) fail("Unsafe path " + rel);
  const p = path.join(data,rel.slice("site/data/".length));
  if (!fs.existsSync(p) || !fs.statSync(p).isFile()) fail("Missing " + rel);
  return p;
}
function checkPolicy() {
  const inventory=json(path.join(data,"public-access-observatory.json"));
  const kavi=json(path.join(data,"kavi-public.json"));
  const cases=json(path.join(data,"documented-cases.json"));
  const cloud=json(path.join(data,"title-wordcloud.json"));
  if (inventory.publicAccessIsNotLicense !== true ||
      inventory.publicationOfIndividualRecordsNotAuthorizedByThisFile !== true ||
      !Array.isArray(inventory.corpora) ||
      inventory.corpora.some(x=>x.recordDisplay!=="not_authorized_for_new_site")) {
    fail("Human inventory cannot authorize individual publication");
  }
  if (cases.publicationAuthorized !== false || kavi.approvedMetadataPublication !== true ||
      kavi.mediaPlaybackVerified !== false || kavi.total!==200 ||
      !Array.isArray(kavi.records) || kavi.records.length!==200) {
    fail("Individual KAVI or documentary permission boundary changed");
  }
  if (cloud.rawTitlesPublished!==false || cloud.individualRecordsPublished!==false ||
      !Array.isArray(cloud.words) || cloud.words.length<18 ||
      !Array.isArray(cloud.sourceProvenance) || cloud.sourceProvenance.length<60) {
    fail("Title cloud is not an approved aggregate");
  }
}
function scientificOutputRoster() {
  return fs.readdirSync(data).filter(x=>x.endsWith(".json") &&
    !["scientific-snapshot-lock.json","scientific-release-manifest.json","world-110m-geometry.json","title-wordcloud.json"].includes(x))
    .map(x=>"site/data/"+x).sort();
}
function verifyFrozen() {
  const lock=json(lockFile);
  if (lock.schema!=="mar-scientific-snapshot-lock-v1" ||
      lock.status!=="historical_baseline_only_not_a_regeneration_or_publication_approval" ||
      lock.policy!=="fail_closed_until_full_reproducible_aggregate_bundle_and_scientific_approval" ||
      !lock.outputs || Object.keys(lock.outputs).length!==33) {
    fail("Historical snapshot lock is invalid");
  }
  const actual=scientificOutputRoster();
  const expected=Object.keys(lock.outputs).sort();
  if (JSON.stringify(actual)!==JSON.stringify(expected)) fail("Partial or new static bundle");
  for (const rel of expected) {
    if (gitBlob(fs.readFileSync(fileFor(rel)))!==lock.outputs[rel]) {
      fail("Scientific site projection changed without atomic review: "+rel);
    }
  }
  return "FROZEN_HISTORICAL";
}
function canonicalSHA256(inputs,outputs) {
  // Canonical equal to Python: sorted keys and compact JSON.
  const ordered=(o)=>Object.fromEntries(Object.entries(o).sort(([a],[b])=>a<b?-1:a>b?1:0));
  const payload=JSON.stringify({inputs:ordered(inputs),outputs:ordered(outputs)});
  return hash(Buffer.from(payload,"utf8"),"sha256");
}
function verifyRelease() {
  const m=json(releaseFile);
  if(m.schema!=="mar-scientific-release-v1" || m.status!=="APPROVED_FOR_PROTECTED_BUILD" ||
     m.publicAccessAuthorized!==false || m.publicationOfNewIndividualItemsAuthorized!==false ||
     !m.review || !m.review.scientificAdmissionReference ||
     !m.review.curatorialAccessReference || !m.review.approvedCommit ||
     !m.epochSha256 || !/^[a-f0-9]{64}$/.test(m.epochSha256)) {
    fail("Release review is absent or incomplete");
  }
  const actual=scientificOutputRoster().concat(["site/data/title-wordcloud.json"]).sort();
  if (!m.outputSha256 || JSON.stringify(actual)!==JSON.stringify(Object.keys(m.outputSha256).sort()))
    fail("Release manifest does not list every projection");
  for(const rel of actual) {
    if(hash(fs.readFileSync(fileFor(rel)),"sha256")!==m.outputSha256[rel])
      fail("SHA-256 mismatch in atomic projection "+rel);
  }
  if(!m.scientificSourceSha256 || !Object.keys(m.scientificSourceSha256).length ||
     Object.values(m.scientificSourceSha256).some(v=>typeof v!=="string" || !/^[a-f0-9]{64}$/.test(v)))
    fail("Scientific input digests are missing");
  if(canonicalSHA256(m.scientificSourceSha256,m.outputSha256)!==m.epochSha256)
    fail("Scientific epoch SHA-256 mismatch");
  return "REVIEWED_ATOMIC_BUNDLE";
}
function main() {
  checkPolicy();
  const mode=fs.existsSync(releaseFile)?verifyRelease():verifyFrozen();
  console.log("MAR static build gate PASS: "+mode+" (SSO and publication rights unchanged)");
}
if(require.main===module) {
  try{main()}catch(e){console.error(e.message);process.exit(1)}
}
module.exports={main,verifyFrozen,verifyRelease};
