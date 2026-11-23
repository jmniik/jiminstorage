const task = await taskSpace(1);
const page = task.page("p1");
const r = await page.fetch('https://github.com/starlike2you/AXC_team5/raw/refs/heads/main/archive/metadata.csv');
if(r.status!==200)throw new Error('CSV read failed');
function csv(s){const rows=[];let row=[],v='',q=false;for(let i=0;i<s.length;i++){const c=s[i];if(c==='"'){if(q&&s[i+1]==='"'){v+='"';i++;}else q=!q;}else if(c===','&&!q){row.push(v);v='';}else if(c==='\n'&&!q){row.push(v.replace(/\r$/,''));rows.push(row);row=[];v='';}else v+=c;}if(v||row.length){row.push(v);rows.push(row);}return rows;}
const [headers,...rows]=csv(r.body);
const data=rows.filter(r=>r.some(Boolean)).map(row=>Object.fromEntries(headers.map((k,i)=>[k,row[i]??''])));
const countBy=k=>data.reduce((a,r)=>(a[r[k]]=(a[r[k]]??0)+1,a),{});
console.log(JSON.stringify({rows:data.length,types:countBy('종류'),collectors:countBy('수집자'),photoRights:data.filter(r=>r['종류']==='사진').reduce((a,r)=>(a[r['저작권']]=(a[r['저작권']]??0)+1,a),{}),remainingRows:data.slice(-7),incomplete:{unknownTitles:data.filter(r=>r['제목']==='미확인').length,unknownAd:data.filter(r=>!r['광고여부']||r['광고여부']==='?').length},oldImpulseTags:data.filter(r=>r['태그'].split(';').includes('충동')).map(r=>r['파일명'])},null,2));
