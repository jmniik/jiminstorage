const task = await taskSpace(1);
const page = task.page("p1");
await page.waitForSelector('a[href*="/tree/"]');
console.log(await page.evaluate(() => ({url:location.href,text:document.querySelector('main')?.innerText,links:[...document.querySelectorAll('main a')].map(a=>({text:a.innerText,href:a.href})).filter(a=>a.text)})));
