/* Real Chromium checks. Optional dev dependency: npm install --no-save playwright@1.62.1
   Then: npx playwright install chromium && node tests/browser_smoke.cjs
   Screenshots, if requested via EVALCHECK_SCREENSHOTS_DIR, are QA intermediates. */
const assert=require('node:assert/strict'),fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {pathToFileURL}=require('node:url');
const {chromium}=require(process.env.EVALCHECK_PLAYWRIGHT_MODULE||'playwright');
const root=path.resolve(__dirname,'..');
const report=path.join(root,'examples/uci_sentiment/results/row-random/report.html');
const data=JSON.parse(fs.readFileSync(path.join(path.dirname(report),'audit.json'),'utf8'));
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'evalcheck-browser-'));
(async()=>{
 const options={headless:true};
 if(process.env.EVALCHECK_BROWSER_EXECUTABLE){options.executablePath=process.env.EVALCHECK_BROWSER_EXECUTABLE;options.args=['--no-sandbox','--single-process','--disable-dev-shm-usage','--disable-gpu','--no-zygote'];}
 const browser=await chromium.launch(options);
 const errors=[],requests=[];
 try{
  const page=await browser.newPage({viewport:{width:1440,height:1050},acceptDownloads:true});
  page.on('pageerror',e=>errors.push(e.message));
  page.on('request',r=>{if(/^https?:/.test(r.url()))requests.push(r.url())});
  await page.goto(pathToFileURL(report).href);
  assert.equal(await page.locator('.finding').count(),14);
  assert.match(await page.locator('#case-context').innerText(),/Row-random/);
  assert.equal(await page.locator('#case-context a').getAttribute('href'),'https://archive.ics.uci.edu/dataset/331/sentiment+labelled+sentences');
  assert.ok(await page.locator('.record-source').count()>0);
  await page.selectOption('#kind','near_overlap');assert.equal(await page.locator('.finding').count(),7);
  await page.selectOption('#severity','error');assert.equal(await page.locator('.finding').count(),0);
  assert.match(await page.locator('.empty').innerText(),/No findings/);
  await page.selectOption('#kind','all');assert.equal(await page.locator('.finding').count(),7);
  await page.selectOption('#severity','all');
  const firstId=data.findings[0].records[0].source_id;
  await page.fill('#search',firstId);assert.ok(await page.locator('.finding').count()>=1);
  await page.fill('#search','');
  await page.locator('.finding summary').first().click();
  assert.equal(await page.locator('.finding').first().getAttribute('open'),'');
  await page.locator('#search').focus();assert.equal(await page.locator('#search').evaluate(n=>n===document.activeElement),true);
  const downloadPromise=page.waitForEvent('download');await page.click('#download');
  const download=await downloadPromise;await download.saveAs(path.join(temp,'audit.json'));
  const exported=JSON.parse(fs.readFileSync(path.join(temp,'audit.json'),'utf8'));
  assert.equal(exported.fingerprint,data.fingerprint);assert.equal(exported.findings.length,14);
  if(process.env.EVALCHECK_SCREENSHOTS_DIR){fs.mkdirSync(process.env.EVALCHECK_SCREENSHOTS_DIR,{recursive:true});await page.screenshot({path:path.join(process.env.EVALCHECK_SCREENSHOTS_DIR,'desktop.png'),fullPage:true});}
  await page.setViewportSize({width:390,height:844});
  assert.equal(await page.evaluate(()=>document.documentElement.scrollWidth<=innerWidth),true,'mobile horizontal overflow');
  if(process.env.EVALCHECK_SCREENSHOTS_DIR)await page.screenshot({path:path.join(process.env.EVALCHECK_SCREENSHOTS_DIR,'mobile.png'),fullPage:true});
  const template=fs.readFileSync(path.join(root,'src/evalcheck/report.html'),'utf8');
  const many=structuredClone(data);many.findings=Array.from({length:61},(_,i)=>({...data.findings[0],id:`F${i}`}));
  const safe=d=>JSON.stringify(d).replace(/</g,'\\u003c').replace(/>/g,'\\u003e').replace(/&/g,'\\u0026');
  const pageFile=path.join(temp,'pagination.html');fs.writeFileSync(pageFile,template.replace('__AUDIT_DATA__',safe(many)));
  await page.goto(pathToFileURL(pageFile).href);assert.equal(await page.locator('.finding').count(),25);
  await page.click('#next');assert.equal(await page.locator('#page').innerText(),'Page 2 / 3');
  await page.click('#next');assert.equal(await page.locator('.finding').count(),11);assert.equal(await page.locator('#next').isDisabled(),true);
  const attack='</script><img src=x onerror="window.EVALCHECK_PWNED=1"><script>window.EVALCHECK_PWNED=1</script>';
  const malicious=structuredClone(data);malicious.findings=[structuredClone(data.findings[0])];malicious.findings[0].records[0].text=attack;
  malicious.report_context={title:attack,source_name:'UCI',source_url:'https://archive.ics.uci.edu/dataset/331'};
  const attackFile=path.join(temp,'injection.html');fs.writeFileSync(attackFile,template.replace('__AUDIT_DATA__',safe(malicious)));
  await page.goto(pathToFileURL(attackFile).href);
  assert.equal(await page.evaluate(()=>window.EVALCHECK_PWNED),undefined);
  assert.equal(await page.locator('img').count(),0);
  assert.equal(await page.locator('.record p').first().textContent(),attack);
  assert.deepEqual(errors,[]);assert.deepEqual(requests,[]);
  console.log(JSON.stringify({browser:browser.version(),passed:['real report render','source context/link','source row identifiers','type filter','severity and empty state','source-id search','evidence expansion','keyboard focus','JSON download','390px overflow','61-finding pagination','script/HTML injection isolation','no external requests','no page errors']},null,2));
 }finally{await browser.close();fs.rmSync(temp,{recursive:true,force:true});}
})().catch(e=>{console.error(e);process.exitCode=1});
