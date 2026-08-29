PUBLIC={'id','title','company','url','location','description','source','published_at','work_mode','score','why','gaps','verification','match_label','blockers','role_family','geo_class','first_seen_at','last_seen_at','active_status','source_kind','source_attribution','canonical_source','alternate_sources'}
SENSITIVE={'email','notes','token','secret','password','oauth','application_history','cv','resume','phone','gmail','home_address','home_location','user_name','candidate_name'}

def sanitize_public_job(job):
    return {k:v for k,v in job.items() if k in PUBLIC}

def assert_public_payload_safe(payload):
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                key=k.lower().strip()
                if key in SENSITIVE or any(key.endswith('_'+s) for s in ('email','token','password','phone')):
                    raise ValueError(f'sensitive key: {k}')
                walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(payload)
