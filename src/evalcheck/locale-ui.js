/* Presentation only: canonical JSON, source code and raw records are unchanged. */
(()=>{
const catalog=__LOCALE_CATALOG__,initial=__INITIAL_LANG__,interactive=__INTERACTIVE__;
let lang=initial;
if(interactive){try{lang=localStorage.getItem('evalcheck.language')||((navigator.language||'en').startsWith('ko')?'ko':'en');}catch{lang=(navigator.language||'en').startsWith('ko')?'ko':'en';}}
if(!['en','ko'].includes(lang))lang='en';
const escape=s=>s.replace(/[.*+?^${}()|[\]\\]/g,'\\$&');
const patterns=Object.entries(catalog).filter(([k])=>k.includes('{')).sort((a,b)=>b[0].replace(/\{\w+\}/g,'').length-a[0].replace(/\{\w+\}/g,'').length).map(([k,v])=>{const keys=[...k.matchAll(/\{(\w+)\}/g)].map(m=>m[1]);return [new RegExp('^'+k.split(/\{\w+\}/).map(escape).join('(.+?)')+'$'),keys,v];});
function translate(text){if(lang==='en')return text;if(Object.hasOwn(catalog,text))return catalog[text];for(const [re,keys,value] of patterns){const m=text.match(re);if(m){let out=value;keys.forEach((key,i)=>out=out.replaceAll('{'+key+'}',m[i+1]));return out;}}return text;}
const originals=new WeakMap(),attributes=new WeakMap();
const excluded=n=>n.parentElement?.closest('script,style,pre,code,textarea,[data-raw],#filelist');
function apply(){document.documentElement.lang=lang;const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);let n;while(n=walker.nextNode()){if(excluded(n))continue;let state=originals.get(n);if(!state||n.nodeValue!==state.rendered)state={source:n.nodeValue};const source=state.source,trim=source.trim();state.rendered=trim?source.slice(0,source.indexOf(trim))+translate(trim)+source.slice(source.indexOf(trim)+trim.length):source;if(n.nodeValue!==state.rendered)n.nodeValue=state.rendered;originals.set(n,state);}
for(const el of document.querySelectorAll('[placeholder],[aria-label],[title]')){if(el.closest('[data-raw],pre,code,textarea'))continue;let attrs=attributes.get(el)||{};for(const key of ['placeholder','aria-label','title'])if(el.hasAttribute(key)){const value=el.getAttribute(key);let state=attrs[key];if(!state||value!==state.rendered)state={source:value};state.rendered=translate(state.source);if(value!==state.rendered)el.setAttribute(key,state.rendered);attrs[key]=state;}attributes.set(el,attrs);}}
window.evalcheckLocale={translate,apply,get language(){return lang},setLanguage(value){if(!['en','ko'].includes(value))throw Error('Unsupported language');lang=value;if(interactive)try{localStorage.setItem('evalcheck.language',lang);}catch{}apply();}};
if(interactive){const selector=document.getElementById('language');selector.value=lang;selector.onchange=()=>window.evalcheckLocale.setLanguage(selector.value);}
apply();if(typeof MutationObserver!=='undefined'){let queued=false;new MutationObserver(()=>{if(!queued){queued=true;queueMicrotask(()=>{queued=false;apply();});}}).observe(document.body,{childList:true,subtree:true,characterData:true});}
})();