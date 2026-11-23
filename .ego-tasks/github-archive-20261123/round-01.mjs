const task = await taskSpace("Read team GitHub archive");
const page = task.page("p1");
console.log({ taskSpaceId: task.spaceId });
await page.goto("https://github.com/");
console.log(await page.snapshot());
