const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const {test}=require("node:test");
const ts=require("typescript");
const file=path.join(__dirname,"../lib/institutional-dictionary.ts");
const compiled=ts.transpileModule(fs.readFileSync(file,"utf8"),{compilerOptions:{module:ts.ModuleKind.CommonJS}}).outputText;
const entry={exports:{}};
new Function("module","exports",compiled)(entry,entry.exports);
const copy=entry.exports.institutionalDictionary;
const read=name=>fs.readFileSync(path.join(__dirname,"..",name),"utf8");
test("institutional editorial translations match across PT EN ES",()=>{
 const keys=Object.keys(copy.pt).sort();
 assert.ok(keys.length>=50);
 for(const lang of ["pt","en","es"]){
  assert.deepEqual(Object.keys(copy[lang]).sort(),keys);
  assert.ok(Object.values(copy[lang]).every(s=>typeof s==="string"&&s.trim().length>=4));
  assert.match(copy[lang].kaviHash,/SHA-256/);
  assert.match(copy[lang].kaviWarning,/reprod|playback/i);
 }
});
test("indexable language landing paths are distinct from client-only translations",()=>{
 const page=read("app/[lang]/page.tsx");
 assert.match(page,/generateStaticParams/);
 assert.match(page,/lang:"en"/);
 assert.match(page,/lang:"es"/);
 assert.match(page,/lang=\{lang\}/);
 assert.match(read("lib/seo.ts"),/mar-public-site\.vercel\.app/);
 assert.match(read("app/sitemap.ts"),/records\.map/);
 assert.ok(!read("app/sitemap.ts").includes("institutionalProfiles.map"));
});
test("all original routes and KAVI evidence gates remain in place",()=>{
 for(const file of ["app/page.tsx","app/instituicoes/page.tsx","app/instituicoes/kavi/page.tsx","app/acervo/page.tsx","app/metodologia/page.tsx"])assert.ok(read(file).length>100);
 assert.match(read("next.config.ts"),/output: "export"/);
 const data=JSON.parse(read("data/kavi-public.json"));
 assert.equal(data.records.length,200);
 assert.equal(data.approvedMetadataPublication,true);
 assert.equal(data.mediaPlaybackVerified,false);
 for(const file of ["app/[lang]/page.tsx","app/sitemap.ts","lib/seo.ts"]){
  const body=read(file);
  for(const forbidden of ["DATABASE_URL","<iframe","<video","fetch(","createClient(","neon("])assert.ok(!body.includes(forbidden));
 }
});
