import csv, re, sys, pathlib

d = pathlib.Path(sys.argv[1])
cols = ["파일명","종류","제목","기관","URL","자료기준일","열람일","수집자","태그","저작권","광고여부"]
keymap = {"기관":"기관","자료 이름":"제목","URL":"URL","자료 기준일":"자료기준일","열람일":"열람일","수집자":"수집자","종류":"종류","태그":"태그"}
date_re = re.compile(r"\d{4}(?:-\d{2}-\d{2})?")

def clean(v):
    v = re.sub(r"\s*\([^)]*\)", "", v).strip()
    return "" if v in ("?", "미표시", "미확인") else v

rows = []
files = sorted(d.glob("*.md"))
for f in files:
    lines = f.read_text(encoding="utf-8").splitlines()[:9]
    r = {c: "" for c in cols}
    r["파일명"] = f.name
    for ln in lines:
        k, _, v = ln.partition(":")
        k, v = k.strip(), v.strip()
        if k in keymap:
            r[keymap[k]] = clean(v)
        elif k == "저작권·광고":
            a, _, b = v.partition("/")
            r["저작권"] = clean(a)
            r["광고여부"] = clean(re.sub(r"^광고\s*여부\s*", "", b.strip()))
    for c in ("자료기준일", "열람일"):
        m = date_re.findall(r[c])
        r[c] = m[0] if m else r[c]
    r["태그"] = ";".join(t.strip() for t in re.split(r"[·,]", r["태그"]) if t.strip())
    rows.append(r)

out = d / "my-metadata.csv"
with out.open("w", encoding="utf-8-sig", newline="") as fp:
    w = csv.DictWriter(fp, fieldnames=cols)
    w.writeheader()
    w.writerows(rows)
print("md files:", len(files), "data rows:", len(rows))
