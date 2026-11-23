const task = await taskSpace(1);
const page = task.page("p1");
await page.click("loc=href:/starlike2you/AXC_team5");
console.log(await page.snapshot({scope:"full_page"}));
