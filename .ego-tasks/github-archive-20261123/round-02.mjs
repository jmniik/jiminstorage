const task = await taskSpace(1);
const page = task.page("p1");
await page.click("loc=href:https://github.com/repos");
console.log(await page.snapshot({ scope: "full_page" }));
