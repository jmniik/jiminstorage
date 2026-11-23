const task = await taskSpace(1);
const page = task.page("p1");
await page.waitForFunction(() => !document.body.innerText.includes("Loading repositories"));
console.log(await page.snapshot({ scope: "full_page" }));
