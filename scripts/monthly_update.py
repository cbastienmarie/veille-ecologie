import datetime as dt
import html
import json
import re
import time
import unicodedata
import urllib.parse
import urllib.request
from pathlib import Path

JOURNALS = ['Nature Climate Change', 'Global Change Biology', 'Frontiers in Ecology and the Environment', 'Trends in Ecology & Evolution', 'Ecology', 'Journal of Ecology', 'Journal of Applied Ecology', 'Oecologia', 'Landscape Ecology', 'Ecography', 'Naturae', 'Sciences Eaux & Territoires', 'Écologie & Politique', "Revue d'Écologie (La Terre et la Vie)"]
RULES = {
 'Fragmentation / destruction des habitats': ['fragmentation', 'habitat loss', 'deforestation', 'déforestation', 'habitat destruction'],
 'Chasse et pêche': ['hunting', 'fishing', 'fisheries', 'bycatch', 'poaching', 'chasse', 'pêche'],
 'Changement climatique': ['climate change', 'warming', 'heatwave', 'climatique', 'réchauffement'],
 'Pollutions dont pesticides': ['pollution', 'pesticid', 'insecticid', 'microplastic', 'contaminant'],
 'Espèces invasives': ['invasive', 'alien species', 'non-native', 'envahissant'],
 'Impact des activités humaines': ['anthropogenic', 'urbanization', 'agriculture', 'human impact', 'anthropique']
}

def norm(s):
    s = unicodedata.normalize('NFKD', s.casefold().replace('&', 'and'))
    return re.sub('[^a-z0-9]', '', s)

def request(route, params):
    url = 'https://api.crossref.org/' + route + '?' + urllib.parse.urlencode(params)
    for attempt in range(4):
        try:
            req = urllib.request.Request(url, headers={'User-Agent': 'VeilleEcologie/1.0 (https://github.com/cbastienmarie/veille-ecologie)'})
            with urllib.request.urlopen(req, timeout=60) as response:
                result = json.load(response)['message']
            time.sleep(1)
            return result
        except Exception:
            if attempt == 3:
                raise
            time.sleep(3 * (attempt + 1))

def plain(s):
    return html.unescape(re.sub('<[^>]+>', ' ', s)).strip()

def main():
    today = dt.datetime.now(dt.timezone.utc).date()
    since = (today - dt.timedelta(days=90)).isoformat()
    source = Path('data/articles.json')
    if not source.exists():
        source = Path('articles.json')
    existing = json.loads(source.read_text(encoding='utf-8'))
    if not isinstance(existing, list):
        raise ValueError('La base existante doit être une liste.')
    def doi_key(s):
        return str(s or '').lower().removeprefix('https://doi.org/').removeprefix('http://doi.org/').strip()
    known = {doi_key(x.get('doi')) for x in existing if x.get('doi')}
    additions = []
    report = {'date_utc': today.isoformat(), 'depuis': since, 'revues': [], 'avertissement': 'Couverture Crossref seulement. Classements automatiques provisoires ; résumés non traduits. Les anciennes fiches ne sont pas validées par cette collecte.'}
    successes = 0
    for name in JOURNALS:
        status = {'revue': name, 'nouveaux': 0}
        staged = []
        try:
            candidates = request('journals', {'query': name, 'rows': 30}).get('items', [])
            matches = [j for j in candidates if norm(j.get('title', '')) == norm(name)]
            issns = sorted({issn for j in matches for issn in j.get('ISSN', [])})
            if not issns:
                raise ValueError('Aucune correspondance exacte de titre : vérification ISSN nécessaire.')
            status['issn'] = issns
            local = set(known)
            for issn in issns:
                cursor = '*'
                for page in range(100):
                    msg = request('journals/' + urllib.parse.quote(issn) + '/works', {'filter': 'type:journal-article,from-pub-date:' + since + ',until-pub-date:' + today.isoformat(), 'rows': 100, 'cursor': cursor})
                    works = msg.get('items', [])
                    for w in works:
                        doi = doi_key(w.get('DOI'))
                        title = plain(' '.join(w.get('title', [])))
                        if not doi or not title or doi in local:
                            continue
                        abstract = plain(w.get('abstract', ''))
                        text = (title + ' ' + abstract).casefold()
                        themes = [label for label, words in RULES.items() if any(word in text for word in words)]
                        if not themes:
                            themes = ['À qualifier']
                        authors = [' '.join(filter(None, [a.get('given'), a.get('family')])) for a in w.get('author', [])]
                        dateparts = (w.get('published', w.get('issued', {})).get('date-parts') or [[]])[0]
                        year = dateparts[0] if dateparts else None
                        summary = 'Notice automatique à vérifier. '
                        summary += ('Extrait du résumé éditeur, langue originale : ' + abstract[:1200] + ('…' if len(abstract) > 1200 else '')) if abstract else 'Résumé éditeur indisponible dans Crossref ; consulter la source.'
                        staged.append({'titre': title, 'auteurs': ', '.join(authors) or 'Non renseignés', 'revue': name, 'annee': year, 'doi': doi, 'url': 'https://doi.org/' + doi, 'taxon': ['À qualifier'], 'zone': ['À qualifier'], 'themes': themes, 'pression': themes[0], 'focus': themes[0], 'resume': summary, 'statut': 'Classement automatique à vérifier', 'source_metadata': 'Crossref', 'collecte_date': today.isoformat()})
                        local.add(doi)
                    if len(works) < 100:
                        break
                    next_cursor = msg.get('next-cursor')
                    if not next_cursor or next_cursor == cursor:
                        raise ValueError('Pagination interrompue.')
                    cursor = next_cursor
                else:
                    raise ValueError('Limite de pagination atteinte.')
            additions.extend(staged)
            known.update(x['doi'] for x in staged)
            status.update({'etat': 'OK', 'nouveaux': len(staged)})
            successes += 1
        except Exception as exc:
            status.update({'etat': 'NON COUVERTE OU ERREUR', 'detail': str(exc)})
        report['revues'].append(status)
    report['nouveaux_total'] = len(additions)
    Path('reports').mkdir(exist_ok=True)
    Path('reports/latest.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    if not successes:
        raise RuntimeError('Aucune revue collectée : base conservée, publication interrompue.')
    source.write_text(json.dumps(existing + additions, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
