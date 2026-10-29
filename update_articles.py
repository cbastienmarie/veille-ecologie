#!/usr/bin/env python3
"""Actualise data/articles.json depuis OpenAlex."""

import json, os, re
from datetime import datetime, timedelta, timezone
from pathlib import Path
import requests

MAILTO = os.getenv("OPENALEX_MAILTO", "contact@example.org")
DATA_FILE = Path("data/articles.json")
LOOKBACK_DAYS = 90
MAX_PER_SOURCE = 25

SOURCES = {
    "Nature Climate Change": "S4306420063",
    "Global Change Biology": "S98371566",
    "Frontiers in Ecology and the Environment": "S4210174581",
    "Trends in Ecology & Evolution": "S4210142787",
    "Ecology": "S4210166799",
    "Journal of Ecology": "S4210166561",
    "Journal of Applied Ecology": "S4210166797",
    "Oecologia": "S4210166793",
    "Landscape Ecology": "S4210175175",
    "Ecography": "S4210174273",
}

RULES = [
    ("Fragmentation / destruction des habitats", ["habitat loss","habitat fragmentation","deforestation","forest loss","land-use change","connectivity","corridor"]),
    ("Changement climatique", ["climate change","warming","climate warming","heatwave","drought","wildfire","extreme weather"]),
    ("Pollutions dont pesticides", ["pesticide","insecticide","neonicotinoid","pollution","microplastic","heavy metal","light pollution","contaminant"]),
    ("Espèces invasives", ["invasive species","alien species","non-native species","invasive alien","biological invasion"]),
    ("Chasse et pêche", ["hunting","overfishing","fisheries","poaching","bushmeat","bycatch","fishing pressure"]),
    ("Impact des activités humaines", ["anthropogenic","human activity","urbanization","agriculture","land use","disturbance","infrastructure"]),
]

FOCUS_MAP = {
    "Fragmentation / destruction des habitats": "Fragmentation et destruction des habitats",
    "Changement climatique": "Changement climatique",
    "Pollutions dont pesticides": "Pollutions dont pesticides",
    "Espèces invasives": "Espèces invasives",
    "Chasse et pêche": "Chasse et pêche",
    "Impact des activités humaines": "Impact des activités humaines",
}

def classify(text):
    text = text.lower(); themes=[]; scores={}
    for theme, kws in RULES:
        hits=[k for k in kws if k in text]
        if hits: themes.append(theme); scores[theme]=len(hits)
    if not themes: return "Impact des activités humaines", ["Écologie générale"]
    return max(scores, key=scores.get), themes

def abstract_from_inverted(idx):
    if not idx: return ""
    pairs=[(i,w) for w,ix in idx.items() for i in ix]
    return " ".join(w for _,w in sorted(pairs))

def shorten(t, limit=620):
    t=re.sub(r"\s+"," ",t).strip()
    return t if len(t)<=limit else t[:limit].rsplit(" ",1)[0]+"…"

def fetch(source_id, since):
    params={"filter":f"primary_location.source.id:{source_id},from_publication_date:{since},type:article","sort":"publication_date:desc","per-page":MAX_PER_SOURCE,"mailto":MAILTO}
    r=requests.get("https://api.openalex.org/works",params=params,timeout=45)
    r.raise_for_status()
    return r.json().get("results",[])

def to_record(w):
    doi=(w.get("doi") or "").replace("https://doi.org/","")
    title=w.get("title") or ""
    if not doi or not title: return None
    abstract=abstract_from_inverted(w.get("abstract_inverted_index"))
    searchable=" ".join([title,abstract," ".join(w.get("keywords") or [])])
    pressure,themes=classify(searchable)
    authors=[a.get("author",{}).get("display_name","") for a in w.get("authorships",[])[:4] if a.get("author")]
    label=", ".join(a for a in authors if a)
    if len(w.get("authorships",[]))>4: label+=" et al."
    return {"titre":title,"auteurs":label or "Auteurs non renseignés","revue":(w.get("primary_location") or {}).get("source",{}).get("display_name",""),"annee":w.get("publication_year"),"doi":doi,"url":f"https://doi.org/{doi}","taxon":["À qualifier"],"zone":["Monde"],"themes":themes,"pression":pressure,"focus":FOCUS_MAP[pressure],"resume":shorten(abstract) or "Résumé à compléter par la rédaction.","openalex_id":w.get("id",""),"publication_date":w.get("publication_date",""),"cited_by_count":w.get("cited_by_count",0),"open_access":bool((w.get("open_access") or {}).get("is_oa"))}

def main():
    since=(datetime.now(timezone.utc)-timedelta(days=LOOKBACK_DAYS)).date().isoformat()
    records={}
    for name,sid in SOURCES.items():
        try: works=fetch(sid,since)
        except Exception as e:
            print(f"Échec {name}: {e}"); continue
        for w in works:
            r=to_record(w)
            if r: records[r["doi"]]=r
    existing=[]
    if DATA_FILE.exists():
        try: existing=json.loads(DATA_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError: existing=[]
    by_doi={x.get("doi"):x for x in existing if x.get("doi")}
    by_doi.update(records)
    merged=sorted(by_doi.values(),key=lambda x:(x.get("publication_date") or "",x.get("cited_by_count",0)),reverse=True)
    DATA_FILE.parent.mkdir(parents=True,exist_ok=True)
    DATA_FILE.write_text(json.dumps(merged,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"{len(merged)} articles enregistrés.")

if __name__=="__main__": main()
