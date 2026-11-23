const task = await taskSpace(1);
const page = task.page("p1");
console.log({url:await page.url(),info:await page.info()});
console.log(await page.evaluate(()=>document.body.innerText.slice(0,16000)));
