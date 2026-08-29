PUBLIC={'id','title','company','url','location','description','source','published_at','work_mode','score','why','gaps','verification'}
SENSITIVE={'email','notes','token','secret','password','oauth','application_history','cv'}
def sanitize_public_job(job): return {k:v for k,v in job.items() if k in PUBLIC}
def assert_public_payload_safe(payload):
    def walk(x):
        if isinstance(x,dict):
            for k,v in x.items():
                if k.lower() in SENSITIVE: raise ValueError(f'sensitive key: {k}')
                walk(v)
        elif isinstance(x,list):
            for v in x: walk(v)
    walk(payload)
