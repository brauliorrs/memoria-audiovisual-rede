"use strict";
/* Test real build guard with synthetic corruptions only, never mutate site/data. */
const test = require("node:test");
const assert = require("node:assert/strict");
const fs = require("node:fs");
const os = require("node:os");
const path = require("node:path");
const cp = require("node:child_process");

const live = path.resolve(__dirname,"..");
const guard = path.join(live,"scripts/verify-scientific-snapshot.cjs");
function setup(t) {
  const tmp = fs.mkdtempSync(path.join(os.tmpdir(),"mar-build-gate-"));
  t.after(()=>fs.rmSync(tmp,{force:true,recursive:true}));
  fs.mkdirSync(path.join(tmp,"scripts"));
  fs.mkdirSync(path.join(tmp,"data"));
  fs.copyFileSync(guard,path.join(tmp,"scripts/verify-scientific-snapshot.cjs"));
  for(const name of fs.readdirSync(path.join(live,"data")).filter(n=>n.endsWith(".json"))) {
    fs.copyFileSync(path.join(live,"data",name),path.join(tmp,"data",name));
  }
  return tmp;
}
function exec(root) {
  return cp.spawnSync(process.execPath,[path.join(root,"scripts/verify-scientific-snapshot.cjs")],{
    cwd:root,encoding:"utf8",timeout:30000
  });
}
test("Approved frozen site baseline builds without reading scientific credentials",t=>{
  const root=setup(t);
  const x=exec(root);
  assert.equal(x.status,0,x.stderr);
  assert.match(x.stdout,/FROZEN_HISTORICAL/);
});
test("Changing only one static report must fail during the actual build",t=>{
  const root=setup(t);
  const p=path.join(root,"data/analytics-0.json");
  fs.appendFileSync(p," ");
  const x=exec(root);
  assert.notEqual(x.status,0);
  assert.match(x.stderr,/Scientific site projection changed/);
});
test("Editing only the title word cloud must fail atomic build",t=>{
  const root=setup(t);
  fs.appendFileSync(path.join(root,"data/title-wordcloud.json")," ");
  const x=exec(root);
  assert.notEqual(x.status,0);
  assert.match(x.stderr,/Standalone title-cloud refresh/);
});
test("Adding unreviewed corpus projection fails closed",t=>{
  const root=setup(t);
  fs.writeFileSync(path.join(root,"data/analytics-99.json"),"[]\n");
  const x=exec(root);
  assert.notEqual(x.status,0);
  assert.match(x.stderr,/Partial or new static bundle/);
});
test("Corrupted publication permission blocks build independently of lock",t=>{
  const root=setup(t);
  const p=path.join(root,"data/public-access-observatory.json");
  const j=JSON.parse(fs.readFileSync(p,"utf8"));
  j.publicationOfIndividualRecordsNotAuthorizedByThisFile=false;
  fs.writeFileSync(p,JSON.stringify(j));
  const x=exec(root);
  assert.notEqual(x.status,0);
  assert.match(x.stderr,/Human inventory cannot authorize/);
});
test("Unreviewed release-manifest override cannot bypass frozen hash checks",t=>{
  const root=setup(t);
  fs.writeFileSync(path.join(root,"data/scientific-release-manifest.json"),
    JSON.stringify({schema:"mar-scientific-release-v1",status:"APPROVED_FOR_PROTECTED_BUILD"}));
  const x=exec(root);
  assert.notEqual(x.status,0);
  assert.match(x.stderr,/Release review is absent/);
});
