"""Build a single offline HTML file of the cartoon with the rendered clips embedded.

    python build_local.py            -> writes biscuit-vs-noir-voiced.html next to this script
"""
import base64, json, os, re

here = os.path.dirname(os.path.abspath(__file__))
html = open(os.path.join(here, "biscuit-vs-noir.html"), encoding="utf-8").read()
man = json.load(open(os.path.join(here, "voices", "manifest.json"), encoding="utf-8"))
data = {}
for cid, name in man["clips"].items():
    with open(os.path.join(here, "voices", name), "rb") as f:
        data[cid] = base64.b64encode(f.read()).decode("ascii")
payload = json.dumps({"note": man.get("note", ""), "data": data})
slot = '<script type="application/json" id="studioClips">{}</script>'
assert slot in html
page = html.replace(slot, '<script type="application/json" id="studioClips">' + payload + "</script>")
head = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover"><style>[hidden]{display:none!important}body{margin:0}</style></head><body>\n'
out = os.path.join(here, "biscuit-vs-noir-voiced.html")
open(out, "w", encoding="utf-8").write(head + page + "\n</body></html>\n")
print("wrote", out, f"{os.path.getsize(out)/1e6:.1f} MB,", len(data), "clips")
