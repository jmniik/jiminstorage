const task = await taskSpace(1);
const page = task.page("p1");
const archiveUrl = await page.evaluate(()=>[...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='archive')?.href);
console.log({archiveUrl});
if (!archiveUrl) throw new Error('Archive link not found');
await page.goto(archiveUrl);
console.log(await page.evaluate(()=>({url:location.href,text:document.body.innerText,links:[...document.querySelectorAll('a')].map(a=>({text:a.innerText,href:a.href})).filter(a=>a.href.includes('/AXC_team5/')&&a.text)})));
