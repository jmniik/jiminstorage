const task = await taskSpace(1);
const page = task.page("p1");
for (const name of ['metadata.csv','team-tags.csv']) {
 const url = 'https://github.com/starlike2you/AXC_team5/raw/refs/heads/main/archive/' + name;
 const result = await page.fetch(url);
 console.log({file:name,status:result.status,body:result.body});
}
