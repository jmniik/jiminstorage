const task = await taskSpace(1);
const page = task.page("p1");
await page.goto("https://github.com/starlike2you/AXC_team5/blob/main/archive/summary.md");
console.log(await page.evaluate(()=>({url:location.href,text:document.body.innerText,links:[...document.querySelectorAll('a')].map(a=>({text:a.innerText,href:a.href})).filter(a=>a.text==='Raw'||a.href.includes('raw'))})));
