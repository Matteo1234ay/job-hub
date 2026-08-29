import requests
UA={'User-Agent':'JobHub/1.0 (+personal job discovery; respectful rate)'}
def arbeitnow():
    data=requests.get('https://www.arbeitnow.com/api/job-board-api',headers=UA,timeout=25).json().get('data',[])
    return [{'title':x.get('title'),'company':x.get('company_name'),'url':x.get('url'),'location':x.get('location'),'description':x.get('description'),'remote':x.get('remote'),'published_at':x.get('created_at')} for x in data]
def remoteok():
    data=requests.get('https://remoteok.com/api',headers=UA,timeout=25).json()
    return [{'title':x.get('position'),'company':x.get('company'),'url':x.get('url'),'location':x.get('location') or 'Remote','description':x.get('description'),'remote':True,'published_at':x.get('date')} for x in data if isinstance(x,dict) and x.get('position')]
