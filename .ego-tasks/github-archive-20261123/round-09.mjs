const task = await taskSpace(1);
const page = task.page("p1");
await page.goto("https://github.com/starlike2you/AXC_team5/blob/main/archive/metadata.csv");
console.log(await page.evaluate(()=>({url:location.href,text:document.body.innerText,raw:[...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='Raw')?.href})));
await page.goto("https://github.com/starlike2you/AXC_team5/blob/main/archive/team-tags.csv");
console.log(await page.evaluate(()=>({url:location.href,text:document.body.innerText,raw:[...document.querySelectorAll('a')].find(a=>a.textContent.trim()==='Raw')?.href})));
