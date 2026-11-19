const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const ts=require("typescript");
const {test}=require("node:test");

const root=path.join(__dirname,"..");
function transpile(modulePath,requireStub=()=>{throw Error("unexpected dependency")}){
 const filename=path.join(root,modulePath);
 const code=ts.transpileModule(fs.readFileSync(filename,"utf8"),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJS,target:ts.ScriptTarget.ES2020}
 }).outputText;
 const moduleRef={exports:{}};
 vm.runInNewContext(code,{module:moduleRef,exports:moduleRef.exports,require:requireStub,URL,Intl},{filename});
 return moduleRef.exports;
}
const seo=transpile("lib/seo.ts");
const i18n=transpile("components/institutional-i18n.tsx",(moduleName)=>{
 if(moduleName==="@/components/site-locale")return {useSiteLocale:()=>({locale:"pt"})};
 if(moduleName==="react/jsx-runtime")return {jsx:()=>({}),jsxs:()=>({}),Fragment:"fragment"};
 throw Error("unexpected module "+moduleName);
}).institutionalCopy;

test("institutional editorial keys match in PT EN ES",()=>{
 const expected=Object.keys(i18n.pt).sort();
 assert.ok(expected.length>=50);
 for(const lang of ["pt","en","es"]){
  assert.deepEqual(Object.keys(i18n[lang]).sort(),expected);
  assert.ok(Object.values(i18n[lang]).every(v=>typeof v==="string"&&v.trim().length>3));
  assert.match(i18n[lang].kaviNoticeBody,/metadata|metadatos|metadados/i);
  assert.match(i18n[lang].homePrinciple2,/rights|derechos|direitos/i);
  assert.match(i18n[lang].cloudFoot,/agregad|aggregate/i);
 }
});

test("SEO copy exists in three languages, but current canonical remains PT",()=>{
 const routes=Array.from(seo.STATIC_ROUTES);
 assert.equal(new Set(routes).size,routes.length);
 assert.ok(routes.length>=14);
 assert.equal(seo.SITE_ORIGIN,"https://mar-public-site.vercel.app");
 for(const lang of ["pt","en","es"]){
  assert.deepEqual(Object.keys(seo.localizedSeo[lang]).sort(),routes.slice().sort());
  for(const route of routes){
   assert.ok(seo.localizedSeo[lang][route].description.length>55);
   assert.ok(seo.localizedSeo[lang][route].title.length>10);
  }
 }
 for(const route of routes){
  const m=seo.pageSeo(route);
  assert.equal(m.alternates.canonical,route);
  assert.equal(m.description,seo.localizedSeo.pt[route].description);
  assert.ok(!m.alternates.languages,"no false hreflang to same URL");
 }
 assert.throws(()=>seo.canonicalPath("//other/"));
 assert.throws(()=>seo.canonicalPath("/acervo/?lang=en"));
 assert.equal(seo.canonicalPath("/acervo"),"/acervo/");
});

test("sitemap never reads forbidden corpora to publish item records",()=>{
 const sitemap=fs.readFileSync(path.join(root,"app/sitemap.ts"),"utf8");
 const kavi=JSON.parse(fs.readFileSync(path.join(root,"data/kavi-public.json"),"utf8"));
 assert.equal(kavi.records.length,200);
 assert.ok(kavi.approvedMetadataPublication);
 assert.equal(kavi.individualReview,false);
 assert.equal(kavi.mediaPlaybackVerified,false);
 assert.equal(kavi.mediaRightsVerified,false);
 assert.match(sitemap,/records\.map\(/);
 assert.match(sitemap,/SITE_ORIGIN\+canonicalPath/);
 for(const unsafe of ["api.finna.fi","fetch(","<video","<iframe","DATABASE_URL","readFileSync("])assert.ok(!sitemap.includes(unsafe));
});

test("institutional routes and historical observations keep exact source links",()=>{
 const pages=["app/page.tsx","app/instituicoes/page.tsx","app/instituicoes/kavi/page.tsx","app/pesquisa/[code]/page.tsx"];
 for(const name of pages){
  const content=fs.readFileSync(path.join(root,name),"utf8");
  assert.ok(content.includes("InstitutionalText"));
  assert.ok(!content.includes("dangerouslySetInnerHTML"));
  assert.ok(!content.includes("DATABASE_URL"));
 }
 const kavi=fs.readFileSync(path.join(root,"app/instituicoes/kavi/page.tsx"),"utf8");
 assert.match(kavi,/publicIndex\.catalogSha256/);
 assert.match(kavi,/publicIndex\.observedOn/);
 assert.match(kavi,/CatalogSearch items=\{records\}/);
 const record=fs.readFileSync(path.join(root,"app/acervo/kavi/[id]/page.tsx"),"utf8");
 assert.match(record,/record\.title/);
 assert.match(record,/recordSeo/);
});
