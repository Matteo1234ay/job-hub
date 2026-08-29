import re

DEFAULT_ROLE_TERMS = (
    'social media manager','social media specialist','social media coordinator','community manager',
    'content creator','digital content creator','social content creator','content specialist','content marketing',
    'video editor','social video editor','videomaker','video maker','video content creator','reels editor',
)
DEFAULT_TASK_TERMS = (
    'editorial plan','piano editoriale','social strategy','strategia social','content creation','creazione contenuti',
    'content ideation','copywriting','riprese','shooting','video editing','montaggio video','reels','tiktok',
    'instagram','youtube','community management','community','analytics','performance analysis','storytelling','organic growth',
)
DEFAULT_TOOL_TERMS = ('davinci','premiere','after effects','capcut','canva','figma','meta business suite','analytics')
ADJACENT_TITLE_TERMS = ('communication specialist','digital marketing specialist','employer branding','junior creative','creative content','communication')
NEARBY = ('moncalieri','grugliasco','venaria','nichelino','settimo torinese','orbassano','beinasco','alpignano','pianezza','san mauro','chieri','rivalta','rosta','avigliana')
SALES_TERMS = ('cold calling','outbound sales','lead generation','sales target','sales targets','account closing','business development','commerciale','vendita','sales representative')
SEO_TERMS = ('seo specialist','sem specialist','ppc specialist','paid acquisition','google ads specialist','performance marketing')
IT_TERMS = ('software engineer','backend developer','frontend developer','data engineer','devops','cybersecurity')
CLOSED_UNPAID = ('unpaid','volunteer','volontario','non retribuito','senza retribuzione')


def _hits(text, terms):
    return [t for t in terms if t.lower() in text]


def classify_geography(job):
    loc = f"{job.get('location','')} {job.get('work_mode','')}".lower()
    if any(x in loc for x in ('torino','turin','collegno','rivoli')):
        return 'LOCAL_STRONG'
    if any(x in loc for x in NEARBY):
        return 'LOCAL_NEARBY'
    if 'remote' in loc or 'remoto' in loc:
        if not loc.strip() or any(x in loc for x in ('italy','italia','remote','remoto')):
            return 'REMOTE_ITALY'
    if not loc.strip():
        return 'UNKNOWN'
    return 'OUTSIDE_SCOPE'


def _seniority(text, title):
    junior = any(x in text for x in ('junior','tirocinante','stage','intern','internship','apprendistato','entry level','entry-level','0-2 years','0–2 years','1-2 years','1–2 years','1-3 years','1–3 years'))
    title_senior = any(x in title for x in ('senior','lead','head of','director','responsabile'))
    years = [int(x) for x in re.findall(r'\b(\d{1,2})\s*\+?\s*(?:years|anni)', text)]
    mandatory_words = any(x in text for x in ('mandatory','minimum','required','must have','obbligatori','obbligatorio','minimo'))
    long_mandatory = bool(years and max(years) >= 5 and mandatory_words)
    if title_senior or long_mandatory:
        return 'SENIOR_BLOCK', junior
    if junior:
        return 'JUNIOR_ACCESSIBLE', True
    return 'NEUTRAL', False


def classify_job(job, profile):
    out = dict(job)
    title = str(job.get('title') or '').lower()
    description = str(job.get('description') or '').lower()
    text = f'{title} {description}'
    role_terms = tuple(profile.get('role_terms') or profile.get('keywords') or DEFAULT_ROLE_TERMS)
    task_terms = tuple(profile.get('task_terms') or DEFAULT_TASK_TERMS)
    tool_terms = tuple(profile.get('tool_terms') or DEFAULT_TOOL_TERMS)
    role_hits = _hits(title, role_terms)
    task_hits = _hits(text, task_terms)
    tool_hits = _hits(text, tool_terms)
    adjacent_hits = _hits(title, ADJACENT_TITLE_TERMS)
    geo_class = classify_geography(job)
    seniority, junior = _seniority(text, title)
    blockers = []

    sales_hits = _hits(text, SALES_TERMS)
    seo_hits = _hits(text, SEO_TERMS)
    it_hits = _hits(text, IT_TERMS)
    if len(sales_hits) >= 2 and len(task_hits) < 3:
        blockers.append('Ruolo prevalentemente sales/business development')
    if len(seo_hits) >= 2 and len(task_hits) < 3:
        blockers.append('Ruolo prevalentemente SEO/SEM/performance')
    if it_hits and len(task_hits) < 3:
        blockers.append('Ruolo IT non pertinente')
    if seniority == 'SENIOR_BLOCK':
        blockers.append('Seniorità o 5+ anni obbligatori')
    if geo_class == 'OUTSIDE_SCOPE':
        blockers.append('Fuori area Torino e non remoto Italia')
    if _hits(text, CLOSED_UNPAID):
        blockers.append('Opportunità non retribuita/volontaria')

    if role_hits:
        role_family = 'DIRECT'
    elif adjacent_hits and len(task_hits) >= 2:
        role_family = 'ADJACENT'
    elif len(task_hits) >= 3:
        role_family = 'TASK_MATCH'
    else:
        role_family = 'WEAK'

    out.update(
        role_hits=role_hits,
        task_hits=task_hits,
        tool_hits=tool_hits,
        role_family=role_family,
        geo_class=geo_class,
        seniority_class=seniority,
        blockers=blockers,
        junior_signal=junior,
    )
    return out


def score_job_v2(job, profile):
    classified = job if 'role_family' in job else classify_job(job, profile)
    blockers = list(classified.get('blockers') or [])
    role_family = classified.get('role_family')
    role_points = {'DIRECT': 25, 'ADJACENT': 20, 'TASK_MATCH': 17, 'WEAK': 0}.get(role_family, 0)
    task_hits = classified.get('task_hits') or []
    tool_hits = classified.get('tool_hits') or []
    task_points = min(25, len(task_hits) * 4)
    tool_points = min(15, len(tool_hits) * 5)
    seniority = classified.get('seniority_class')
    seniority_points = 15 if seniority == 'JUNIOR_ACCESSIBLE' else (0 if seniority == 'SENIOR_BLOCK' else 10)
    geo_points = {'LOCAL_STRONG': 10, 'LOCAL_NEARBY': 9, 'REMOTE_ITALY': 8, 'UNKNOWN': 3, 'OUTSIDE_SCOPE': 0}.get(classified.get('geo_class'), 0)
    quality = 0
    if classified.get('company'): quality += 3
    if str(classified.get('url','')).startswith(('http://','https://')): quality += 3
    if len(str(classified.get('description',''))) >= 100: quality += 2
    if classified.get('source_kind') in ('official','ats'): quality += 2
    score = min(100, role_points + task_points + tool_points + seniority_points + geo_points + quality)
    if not blockers and role_family == 'DIRECT' and classified.get('geo_class') in ('LOCAL_STRONG','LOCAL_NEARBY','REMOTE_ITALY'):
        score = max(score, 60)
    if blockers:
        score = min(score, 45)

    why = []
    if role_points: why.append(f'+ ruolo {role_family.lower()}')
    for hit in task_hits[:4]: why.append(f'+ {hit}')
    for hit in tool_hits[:2]: why.append(f'+ strumento {hit}')
    if classified.get('geo_class') == 'LOCAL_STRONG': why.append('+ Torino/Collegno/Rivoli')
    elif classified.get('geo_class') == 'LOCAL_NEARBY': why.append('+ cintura torinese')
    elif classified.get('geo_class') == 'REMOTE_ITALY': why.append('+ remoto Italia')
    if seniority == 'JUNIOR_ACCESSIBLE': why.append('+ seniorità accessibile')

    gaps = []
    if not tool_hits: gaps.append('Strumenti specifici non indicati')
    if seniority == 'NEUTRAL': gaps.append('Seniorità non chiarissima')
    if classified.get('geo_class') == 'UNKNOWN': gaps.append('Località non indicata')

    if blockers or score < 60:
        label = 'NON_PERTINENTE'
    elif score >= 75:
        label = 'MATCH_FORTE'
    else:
        label = 'DA_VALUTARE'
    return score, label, why, gaps, blockers
