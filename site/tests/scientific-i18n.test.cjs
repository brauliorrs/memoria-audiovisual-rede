const assert=require("node:assert/strict");
const fs=require("node:fs");
const path=require("node:path");
const vm=require("node:vm");
const {test}=require("node:test");
const ts=require("typescript");

const filename=path.join(__dirname,"../components/scientific-i18n.tsx");
const code=ts.transpileModule(fs.readFileSync(filename,"utf8"),{
  compilerOptions:{module:ts.ModuleKind.CommonJS,jsx:ts.JsxEmit.ReactJSX,target:ts.ScriptTarget.ES2020}
}).outputText;
const moduleRef={exports:{}};
let currentLocale="pt";
const jsx=(type,props)=>({type,props});
vm.runInNewContext(code,{
  module:moduleRef,exports:moduleRef.exports,
  Intl,
  require(name){
    if(name==="react/jsx-runtime")return{jsx,jsxs:jsx,Fragment:"fragment"};
    if(name==="@/components/site-locale")return{useSiteLocale:()=>({locale:currentLocale})};
    throw new Error("unexpected dependency: "+name);
  }
},{filename});
const {scientificCopy,ScientificText,ScientificNumber,ScientificPercent,ScientificTerritory}=moduleRef.exports;

test("PT EN ES have exactly the same editorial keys",()=>{
  const ptKeys=Object.keys(scientificCopy.pt).sort();
  assert.ok(ptKeys.length>=130);
  for(const lang of ["pt","en","es"]){
    assert.deepEqual(Object.keys(scientificCopy[lang]).sort(),ptKeys);
    assert.ok(Object.values(scientificCopy[lang]).every(text=>typeof text==="string"&&text.trim().length>2));
  }
});

test("institutional restrictions and provenance remain explicit in all languages",()=>{
  for(const locale of ["pt","en","es"]){
    const c=scientificCopy[locale];
    assert.match(c.obDisclaimer,/2026/);
    assert.match(c.obCatalogAfter,/200/);
    assert.match(c.metDesc1,/SHA-256/);
    assert.match(c.profFootnote,/2026/);
    assert.match(c.profNotReleased, /fichas|records/i);
    assert.ok(c.anNoSum.length>=35);
    assert.ok(c.casesWarning.length>=100);
    assert.ok(c.profSourceText.length>=35);
  }
});

test("switching language changes scientific labels and regional numbers",()=>{
  currentLocale="pt";
  assert.equal(ScientificText({id:"obTitle"}).props.children,scientificCopy.pt.obTitle);
  assert.equal(ScientificNumber({value:194057}).props.children,"194.057");
  currentLocale="en";
  assert.equal(ScientificText({id:"obTitle"}).props.children,scientificCopy.en.obTitle);
  assert.equal(ScientificNumber({value:194057}).props.children,"194,057");
  assert.equal(ScientificPercent({part:1,total:4}).props.children,"25.0%");
  currentLocale="es";
  assert.equal(ScientificText({id:"obTitle"}).props.children,scientificCopy.es.obTitle);
  assert.equal(ScientificNumber({value:194057}).props.children,"194.057");
  assert.equal(ScientificTerritory({value:"Europe"}).props.children,"Europa");
});

test("catalog and access-index labels change language but keep legal boundary",()=>{
  const locales=["pt","en","es"];
  const catalogTerms=[];
  const indexTerms=[];
  for(const loc of locales){
    currentLocale=loc;
    const copy=scientificCopy[loc];
    assert.equal(ScientificText({id:"catalogSearchLabel"}).props.children,copy.catalogSearchLabel);
    assert.equal(ScientificText({id:"accessTitle"}).props.children,copy.accessTitle);
    assert.ok(copy.catalogSearchLabel.length>20);
    assert.ok(copy.catalogMetadataNotice.length>15);
    assert.ok(copy.catalogMoreRecords.length>8);
    assert.ok(copy.accessPublicationHold.length>35);
    assert.ok(copy.accessOriginalNote.length>65);
    assert.ok(copy.accessFootnoteAfter.length>180);
    assert.ok(copy.accessFallbackPublic.length>80);
    assert.ok(copy.accessFallbackUnquantified.length>80);
    catalogTerms.push(copy.catalogSearchLabel);
    indexTerms.push(copy.accessPublicationHold);
  }
  assert.equal(new Set(catalogTerms).size,3);
  assert.equal(new Set(indexTerms).size,3);
});
