const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const {test}=require("node:test");
const ts=require("typescript");
const React=require("react");
const {renderToStaticMarkup}=require("react-dom/server");

const root=path.resolve(__dirname,"..");
const kavi=JSON.parse(fs.readFileSync(path.join(root,"data/kavi-public.json"),"utf8"));
const file=path.join(root,"components/kavi-record-detail.tsx");
const code=ts.transpileModule(fs.readFileSync(file,"utf8"),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}
}).outputText;
const dictionaryCode=ts.transpileModule(
  fs.readFileSync(path.join(root,"components/scientific-i18n.tsx"),"utf8"),
  {compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}}
).outputText;
let locale="pt";
const dictModule={exports:{}};
vm.runInNewContext(dictionaryCode,{
  module:dictModule,exports:dictModule.exports,Intl,
  require(name){
    if(name==="react/jsx-runtime")return require("react/jsx-runtime");
    if(name==="@/components/site-locale")return {useSiteLocale:()=>({locale})};
    throw Error("Unexpected dictionary import "+name);
  }
});
const componentModule={exports:{}};
vm.runInNewContext(code,{
  module:componentModule,exports:componentModule.exports,Intl,
  require(name){
    if(name==="react/jsx-runtime")return require("react/jsx-runtime");
    if(name==="next/link")return {__esModule:true,default:({href,children,...props})=>React.createElement("a",{href,...props},children)};
    if(name==="@/components/scientific-i18n")return {useScientificCopy:()=>dictModule.exports.scientificCopy[locale]};
    if(name==="@/components/site-locale")return {useSiteLocale:()=>({locale})};
    throw Error("Unexpected component import "+name);
  }
});
const KaviRecordDetail=componentModule.exports.KaviRecordDetail;
const props={
  record:kavi.records[0],catalogCount:kavi.total,
  observedOn:kavi.observedOn,approvedCatalogSha256:kavi.sourceCatalogSha256,
};
function render(language,record=props.record){
  locale=language;
  return renderToStaticMarkup(React.createElement(KaviRecordDetail,{...props,record}));
}

test("all three languages change editorial labels without modifying source fields",()=>{
  for(const language of ["pt","en","es"]){
    const html=render(language);
    const copy=dictModule.exports.scientificCopy[language];
    for(const field of [props.record.title,props.record.id,props.record.genres,
      props.record.subjects,props.record.institution,props.record.country,
      props.record.source,props.record.languages,props.record.year,
      props.record.sourceUrl,kavi.sourceCatalogSha256,kavi.observedOn]){
      assert.ok(html.includes(field),"Original value lost in "+language+": "+field);
    }
    for(const label of ["kaviDetailsHeading","kaviProvenanceHeading","kaviReviewStatus",
      "kaviPlaybackStatus","kaviMediaRightsStatus","kaviApprovedHash",
      "kaviOriginalMetadataNote","kaviOpenSource"]){
      assert.ok(html.includes(copy[label]),"Missing "+language+" "+label);
    }
    assert.ok(html.includes('href="/acervo/"'));
    assert.ok(html.includes('href="/instituicoes/kavi/"'));
    assert.ok(html.includes("200"));
    assert.ok(!html.includes("<iframe"));
    assert.ok(!html.includes("<video"));
    assert.ok(!html.includes("<img"));
  }
});

test("missing values are translated as absence, not silently synthesized",()=>{
  const sparse=kavi.records.find(x=>!x.subjects&&!x.languages);
  assert.ok(sparse,"Test needs a genuine sparse approved KAVI record");
  for(const language of ["pt","en","es"]){
    const html=render(language,sparse);
    const copy=dictModule.exports.scientificCopy[language];
    assert.ok(html.includes(copy.kaviSubjectsUnknown));
    assert.ok(html.includes(copy.kaviUnknown));
    assert.ok(html.includes(sparse.title));
    assert.ok(html.includes(sparse.id));
  }
});

test("scientific status remains unverified for every language",()=>{
  const all=["pt","en","es"].map(lang=>{
    const copy=dictModule.exports.scientificCopy[lang];
    return [copy.kaviReviewStatus,copy.kaviPlaybackStatus,copy.kaviMediaRightsStatus];
  });
  assert.equal(new Set(all.map(a=>a.join("|"))).size,3);
  for(const [language,i] of ["pt","en","es"].map((lang,i)=>[lang,i])){
    assert.ok(all[i].every(text=>text.length>=11),"Missing status "+language);
  }
});
