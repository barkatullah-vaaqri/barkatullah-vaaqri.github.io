#!/usr/bin/env python3
"""Build the static, hostable VAAQRI site from the Claude Design boards.

Usage:  python3 build.py [--site-url https://www.example.com] [--form-endpoint https://...]

Reads  project/*.dc.html  →  writes  ../vaaqri-site/*.html + assets.
The hero console prototype keeps the board's template (sc-for / sc-if / {{ }})
and its renderVals() logic; a 2 KB runtime below renders it in plain JS.
"""
import argparse, json, pathlib, re, html

ROOT = pathlib.Path(__file__).resolve().parent
SRC = ROOT / "project"
OUT = ROOT.parent / "vaaqri-site"

PAGES = {  # board → output file, <title>, meta description
    "Main": ("index.html",
             "VAAQRI — Restaurant operations software for UK independents and small groups",
             "Connect QR ordering, kitchen display, stock and food-safety records in one console. Built in England. Book a demo."),
    "Hub": ("hub.html",
            "Intelligence hub — VAAQRI",
            "Guides, articles and definitions on running a UK restaurant: ordering, kitchen, inventory, food safety and multi-site operations."),
    "Topic": ("topic.html",
              "Inventory management for restaurants — VAAQRI Intelligence hub",
              "What restaurant inventory management is, how stock counts, par levels and waste tracking work, and what to look for in software."),
    "Article": ("article.html",
                "Restaurant inventory management explained — VAAQRI",
                "A plain-English guide to restaurant inventory management for UK independents: counts, par levels, waste and how software helps."),
    "Glossary": ("glossary.html",
                 "Restaurant operations glossary — VAAQRI",
                 "Definitions of the terms used in restaurant operations software: KDS, par level, bump, allergen matrix, HACCP and more."),
}
LINKMAP = {f"{b}.dc.html": PAGES[b][0] for b in PAGES}


def jsonld(board, site_url):
    base = (site_url.rstrip("/") + "/") if site_url else ""
    org = {"@type": "Organization", "name": "VAAQRI", "url": base or None,
           "logo": (base + "favicon.svg") if base else None,
           "sameAs": ["https://www.linkedin.com/company/vaaqri-ltd", "https://www.instagram.com/vaaqri/"],
           "address": {"@type": "PostalAddress", "addressCountry": "GB"}}
    org = {k: v for k, v in org.items() if v}
    graph = [org]
    if board == "Main":
        graph.append({"@type": "WebSite", "name": "VAAQRI", "url": base or None, "publisher": {"@type": "Organization", "name": "VAAQRI"}})
        graph.append({"@type": "SoftwareApplication", "name": "VAAQRI", "applicationCategory": "BusinessApplication",
                      "operatingSystem": "Web", "description": PAGES["Main"][2],
                      "publisher": {"@type": "Organization", "name": "VAAQRI"}})
    elif board == "Article":
        graph.append({"@type": "Article", "headline": "Restaurant inventory management explained",
                      "author": {"@type": "Organization", "name": "VAAQRI"}, "publisher": {"@type": "Organization", "name": "VAAQRI"}})
    elif board == "Glossary":
        graph.append({"@type": "DefinedTermSet", "name": "Restaurant operations glossary"})
    else:
        graph.append({"@type": "CollectionPage", "name": PAGES[board][1]})
    graph = [{k: v for k, v in g.items() if v is not None} for g in graph]
    return '<script type="application/ld+json">' + json.dumps({"@context": "https://schema.org", "@graph": graph}, ensure_ascii=False) + "</script>"


RUNTIME = r"""
<script>
(function(){
'use strict';
/* ---- minimal DCLogic shim: state + setState → re-render ---- */
function DCLogic(p){this.props=p||{};this.state={};}
DCLogic.prototype.setState=function(o){Object.assign(this.state,o);if(this._render)this._render();};
__COMPONENT__
var root=document.getElementById('hp');
if(root){
 var tpl=document.createElement('template');tpl.innerHTML=root.innerHTML;root.innerHTML='';
 var comp=new Component({cta:'Book a demo'});
 function get(path,scopes){var parts=path.trim().split('.');for(var s=scopes.length-1;s>=0;s--){var sc=scopes[s];if(sc&&Object.prototype.hasOwnProperty.call(sc,parts[0])){var v=sc;for(var i=0;i<parts.length;i++){if(v==null)return undefined;v=v[parts[i]];}return v;}}return undefined;}
 var RX=/\{\{\s*([^}]+?)\s*\}\}/g;
 function interp(str,scopes){return str.replace(RX,function(m,p){var v=get(p,scopes);return v==null?'':String(v);});}
 function renderNodes(src,dst,scopes){
  for(var n=src.firstChild;n;n=n.nextSibling){
   if(n.nodeType===3){dst.appendChild(document.createTextNode(interp(n.nodeValue,scopes)));continue;}
   if(n.nodeType!==1)continue;
   var tag=n.tagName.toLowerCase();
   if(tag==='sc-if'){var m=RX.exec(n.getAttribute('value')||'');RX.lastIndex=0;if(m&&get(m[1],scopes))renderNodes(n,dst,scopes);continue;}
   if(tag==='sc-for'){var lm=RX.exec(n.getAttribute('list')||'');RX.lastIndex=0;var list=lm?get(lm[1],scopes):null;var as=n.getAttribute('as')||'item';if(list&&list.length){for(var i=0;i<list.length;i++){var sc={};sc[as]=list[i];renderNodes(n,dst,scopes.concat([sc]));}}continue;}
   var el=document.createElement(tag);
   for(var a=0;a<n.attributes.length;a++){var at=n.attributes[a],name=at.name;if(name.indexOf('hint-')===0)continue;
    if(name==='onclick'){var fm=RX.exec(at.value);RX.lastIndex=0;var fn=fm?get(fm[1],scopes):null;if(typeof fn==='function')el.addEventListener('click',fn);if(el.tagName==='BUTTON')el.type='button';continue;}
    el.setAttribute(name,interp(at.value,scopes));}
   renderNodes(n,el,scopes);dst.appendChild(el);
  }
 }
 comp._render=function(){var vals=comp.renderVals();var frag=document.createDocumentFragment();renderNodes(tpl.content,frag,[vals]);root.replaceChildren(frag);document.querySelectorAll('[data-bind]').forEach(function(b){b.textContent=vals[b.getAttribute('data-bind')]||'';});};
 comp._render();
 if(comp.componentDidMount)comp.componentDidMount();
}else if(typeof Component!=='undefined'){var c=new Component({});if(c.componentDidMount)c.componentDidMount();}

/* ---- demo form: native validation, honeypot + timing, POST to endpoint, states ---- */
var form=document.querySelector('form[aria-label="Book a demo"]');
if(form){
 var endpoint=form.getAttribute('data-endpoint')||'';
 var btn=form.querySelector('.submit'),status=form.querySelector('.status'),err=form.querySelector('.form-err');
 var opened=Date.now();
 function setErr(msg){if(err){err.textContent=msg||'';err.hidden=!msg;}}
 form.querySelectorAll('.input').forEach(function(f){f.addEventListener('input',function(){f.removeAttribute('aria-invalid');var m=form.querySelector('#'+f.id+'-msg');if(m)m.hidden=true;setErr('');});});
 form.addEventListener('submit',function(ev){
  ev.preventDefault();setErr('');
  if(form.querySelector('[name="website"]').value)return; /* honeypot filled: do nothing */
  if(Date.now()-opened<2500){setErr('Please take a moment to check your details, then send again.');return;}
  var bad=null;form.querySelectorAll('.input[required]').forEach(function(f){if(!f.checkValidity()){f.setAttribute('aria-invalid','true');var m=form.querySelector('#'+f.id+'-msg');if(m){m.textContent=f.validationMessage;m.hidden=false;}if(!bad)bad=f;}});
  if(bad){bad.focus();setErr('Please check the highlighted fields.');return;}
  if(!endpoint){setErr('We could not send your request just now. Please try again shortly, or get in touch on LinkedIn.');return;}
  var data={};new FormData(form).forEach(function(v,k){if(k!=='website')data[k]=v;});data.page=location.href;
  btn.setAttribute('aria-busy','true');btn.disabled=true;
  var ctrl=('AbortController' in window)?new AbortController():null;var t=setTimeout(function(){if(ctrl)ctrl.abort();},15000);
  fetch(endpoint,{method:'POST',headers:{'Content-Type':'application/json','Accept':'application/json'},body:JSON.stringify(data),signal:ctrl?ctrl.signal:undefined})
   .then(function(r){if(!r.ok)throw new Error('HTTP '+r.status);btn.setAttribute('aria-busy','false');btn.setAttribute('data-done','true');status.setAttribute('data-shown','true');form.querySelectorAll('.input').forEach(function(f){f.value='';f.disabled=true;});status.focus&&status.focus();})
   .catch(function(){btn.setAttribute('aria-busy','false');btn.disabled=false;setErr('We could not send your request. Please check your connection and try again.');})
   .then(function(){clearTimeout(t);});
 });
}
})();
</script>
"""

FORM_EXTRAS = (
    '<div style="position:absolute;left:-10000px;top:auto;width:1px;height:1px;overflow:hidden" aria-hidden="true">'
    '<label for="f-website">Website</label><input id="f-website" name="website" type="text" tabindex="-1" autocomplete="off"></div>'
)
FORM_CSS = (
    "<style>.form-err{margin:0;padding:12px 14px;border-radius:12px;background:#FBE4DF;color:#8F2A16;font-size:14px;line-height:1.5}"
    ".fmsg{margin:6px 0 0;font-size:13px;color:#B03419}.status:focus{outline:3px solid #2E7029;outline-offset:3px}"
    "form .input:disabled{background:#F6F0E7;color:#8A7F7A}"
    "</style>"
)


def build_page(board, site_url, form_endpoint):
    out_name, title, desc = PAGES[board]
    s = (SRC / f"{board}.dc.html").read_text(encoding="utf-8")

    # 1. unwrap the Claude Design envelope
    s = re.sub(r"<head>.*?</head>", "", s, count=1, flags=re.S)
    s = s.replace("<x-dc>", "").replace("</x-dc>", "")
    s = s.replace("<helmet>", "<head>").replace("</helmet>", "</head>")
    s = s.replace("<html lang=\"en\">", "<html lang=\"en-GB\">")
    s = re.sub(r'<meta name="page-type"[^>]*><meta name="site-kind"[^>]*>', "", s)

    # 2. component script → runtime
    m = re.search(r'<script type="text/x-dc" data-dc-script[^>]*>(.*?)</script>', s, flags=re.S)
    comp = m.group(1) if m else ""
    s = s[:m.start()] + s[m.end():] if m else s
    comp = comp.replace("this.props.cta ?? 'Book a demo'", "(this.props.cta||'Book a demo')")
    s = s.replace("{{cta}}", "Book a demo")
    s = s.replace('<div class="app hp"', '<div class="app hp" id="hp"', 1)
    s = s.replace("{{viewName}}", '<span data-bind="viewName"></span>')

    # 3. links between boards
    for k, v in LINKMAP.items():
        s = s.replace(f'href="{k}', f'href="{v}')
    s = s.replace('href="#privacy"', 'href="privacy.html"').replace('href="#terms"', 'href="privacy.html#terms"')
    s = s.replace('<a href="#demo" class="mlink">Log in</a>', "")  # no login product yet: don't advertise one

    # 4. head: title, meta, fonts, structured data
    canon = (site_url.rstrip("/") + "/" + ("" if out_name == "index.html" else out_name)) if site_url else out_name
    head_extra = (
        f'<meta charset="utf-8">\n<meta name="viewport" content="width=device-width,initial-scale=1">\n'
        f"<title>{html.escape(title)}</title>\n"
        f'<meta name="description" content="{html.escape(desc)}">\n'
        f'<meta name="theme-color" content="#7B1450">\n<meta name="robots" content="index,follow">\n'
        f'<link rel="icon" href="favicon.svg" type="image/svg+xml">\n<link rel="canonical" href="{html.escape(canon)}">\n'
        f'<meta property="og:type" content="website"><meta property="og:site_name" content="VAAQRI"><meta property="og:locale" content="en_GB">'
        f'<meta property="og:title" content="{html.escape(title)}"><meta property="og:description" content="{html.escape(desc)}">'
        + (f'<meta property="og:url" content="{html.escape(canon)}">' if site_url else "")
        + '<meta name="twitter:card" content="summary">\n'
        '<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>\n'
        + jsonld(board, site_url) + "\n" + FORM_CSS + "\n"
    )
    s = s.replace("<head>", "<head>\n" + head_extra, 1)
    s = re.sub(r'<meta name="description" content="[^"]*">\n(?=<link rel="preconnect" href="https://fonts.googleapis.com">)', "", s)  # drop board's own description (replaced above)

    # 5. form hardening
    s = s.replace('<form action="#demo" method="post"', f'<form action="{html.escape(form_endpoint or "#demo")}" method="post" data-endpoint="{html.escape(form_endpoint)}"', 1)
    s = s.replace('<p id="form-note" class="small" style="margin:0;font-size:13px">All fields are required.</p>',
                  '<p id="form-note" class="small" style="margin:0;font-size:13px">All fields are required.</p>' + FORM_EXTRAS)
    for fid in ("f-name", "f-role", "f-company"):
        s = re.sub(rf'(<input class="input" id="{fid}"[^>]*?)( required>)', rf'\1 aria-describedby="{fid}-msg"\2<p id="{fid}-msg" class="fmsg" hidden></p>', s)
    s = s.replace('required aria-describedby="f-email-err">', 'required aria-describedby="f-email-err f-email-msg"><p id="f-email-msg" class="fmsg" hidden></p>')
    s = s.replace('<div class="status" role="status" aria-live="polite" data-shown="false">',
                  '<p class="form-err" role="alert" hidden></p><div class="status" role="status" aria-live="polite" tabindex="-1" data-shown="false">')

    # 6. runtime
    s = s.replace("</body>", RUNTIME.replace("__COMPONENT__", comp) + "\n</body>")
    s = re.sub(r"\n{3,}", "\n\n", s)
    (OUT / out_name).write_text(s, encoding="utf-8")
    return out_name


PRIVACY = """<!doctype html>
<html lang="en-GB"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Privacy notice — VAAQRI</title><meta name="description" content="How VAAQRI uses the details you give us when you book a demo.">
<meta name="robots" content="noindex,follow"><link rel="icon" href="favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Anton&family=Schibsted+Grotesk:wght@400;500&family=Hanken+Grotesk:wght@400;500&display=swap" rel="stylesheet">
<style>body{margin:0;background:#FFF3E2;color:#141212;font-family:"Hanken Grotesk",system-ui,sans-serif;font-size:17px;line-height:1.6}
.wrap{width:min(100% - 48px,720px);margin:0 auto;padding:48px 0 96px}h1,h2{font-family:"Schibsted Grotesk",sans-serif;font-weight:500;letter-spacing:-.02em;line-height:1.1}
h1{font-size:40px;margin:24px 0 8px}h2{font-size:24px;margin:40px 0 8px}a{color:#7B1450}.brand{font-family:Anton,Impact,sans-serif;font-size:24px;color:#7B1450;text-decoration:none}
.note{background:#FFE0EC;border-radius:12px;padding:14px 16px;font-size:15px}</style></head>
<body><main class="wrap"><a class="brand" href="index.html">VAAQRI</a>
<h1>Privacy notice</h1>
<p class="note">Draft for review by VAAQRI Ltd before launch. The wording below describes what the website does today; it is not legal advice.</p>
<h2>What we collect</h2><p>When you book a demo we ask for your name, role, work email, restaurant or company name, number of locations and main area of interest. The site sets no analytics or advertising cookies.</p>
<h2>What we use it for</h2><p>Only to arrange and prepare your demo, and to reply to you about it. We do not add you to a newsletter and we do not share or sell your details.</p>
<h2>How long we keep it</h2><p>For as long as the conversation about a demo is live, and then for our records of that conversation. Email us and we will delete it.</p>
<h2>Your rights</h2><p>Under UK GDPR you can ask what we hold about you, ask us to correct or delete it, or object to how we use it. Contact VAAQRI Ltd through <a href="https://www.linkedin.com/company/vaaqri-ltd">LinkedIn</a>, or at the address published here before launch.</p>
<h2 id="terms">Terms</h2><p>Terms of service for the VAAQRI platform will be published here before the platform is offered commercially.</p>
<p style="margin-top:48px;font-size:14px;color:#57504D">VAAQRI Ltd, registered in England. <a href="index.html">Back to the site</a></p>
</main></body></html>
"""

README = """# VAAQRI website — static build (V4)

Generated from the Claude Design boards by `build.py` (in the design project). Six static pages, no build step, no dependencies beyond Google Fonts.

- `index.html` — landing page. The hero console prototype is plain JS (template + sample data live inside the page).
- `hub.html`, `topic.html`, `article.html`, `glossary.html` — Intelligence hub pages.
- `privacy.html` — draft privacy notice (review before launch; `#terms` placeholder).
- `favicon.svg`, `robots.txt`, `sitemap.xml`.

## Host it
Upload the folder as-is to any static host (Netlify, Vercel, Cloudflare Pages, GitHub Pages, S3). `index.html` is the entry.

## Before go-live
1. Rebuild with your domain so canonical URLs, Open Graph and the sitemap are absolute:
   `python3 build.py --site-url https://www.yourdomain.co.uk`
2. Wire the demo form. Pass `--form-endpoint https://...` (a Formspree / Basin / Netlify Function / your own API URL that accepts a JSON POST and returns 2xx on success).
   The page only shows "Request sent" when the endpoint answers 2xx; without an endpoint it shows an honest error. Fields: name, role, email, company, locations, interest, page. A honeypot field (`website`) and a 2.5 s timing check are applied client-side; keep server-side validation too.
3. Review `privacy.html` and add a contact address.
4. Add an `og:image` (1200×630) if you want rich link previews.

## Notes
- All motion respects `prefers-reduced-motion`. Section highlights use IntersectionObserver (every modern browser).
- Sample data in the prototype and the capability screens is labelled as sample data in the UI.
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--site-url", default="")
    ap.add_argument("--form-endpoint", default="")
    a = ap.parse_args()
    OUT.mkdir(exist_ok=True)
    names = [build_page(b, a.site_url, a.form_endpoint) for b in PAGES]
    (OUT / "privacy.html").write_text(PRIVACY, encoding="utf-8")
    (OUT / "README.md").write_text(README, encoding="utf-8")
    base = (a.site_url.rstrip("/") + "/") if a.site_url else "/"
    (OUT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "".join(f"  <url><loc>{base}{'' if n == 'index.html' else n}</loc></url>\n" for n in names) + "</urlset>\n", encoding="utf-8")
    (OUT / "robots.txt").write_text(f"User-agent: *\nAllow: /\nSitemap: {base}sitemap.xml\n", encoding="utf-8")
    (OUT / "favicon.svg").write_text('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 32 32"><rect width="32" height="32" rx="7" fill="#7B1450"/><path d="M8 9l8 15 8-15" fill="none" stroke="#FF9CC2" stroke-width="3.5" stroke-linejoin="round"/></svg>', encoding="utf-8")
    import shutil
    src_assets = SRC / "assets"
    if src_assets.exists():
        shutil.copytree(src_assets, OUT / "assets", dirs_exist_ok=True)
    (OUT / "favicon.ico").write_bytes((ROOT / "favicon.ico").read_bytes())
    print("built:", ", ".join(names + ["privacy.html"]))


if __name__ == "__main__":
    main()
