const FRESHNESS_KEY='jobhub.deployedVersion.v1';
let freshnessCheckRunning=false;

async function updateServiceWorker(){
  if(!('serviceWorker' in navigator))return;
  try{
    const registration=await navigator.serviceWorker.ready;
    await registration.update();
  }catch{}
}

async function checkForFreshVersion(){
  if(freshnessCheckRunning)return;
  freshnessCheckRunning=true;
  try{
    await updateServiceWorker();
    const response=await fetch(`version.json?t=${Date.now()}`,{cache:'no-store'});
    if(!response.ok)return;
    const data=await response.json();
    const version=String(data.version||'').trim();
    if(!version)return;
    const previous=localStorage.getItem(FRESHNESS_KEY);
    if(previous&&previous!==version){
      localStorage.setItem(FRESHNESS_KEY,version);
      const url=new URL(location.href);
      url.searchParams.set('_v',version.slice(0,12));
      location.replace(url.href);
      return;
    }
    localStorage.setItem(FRESHNESS_KEY,version);
  }catch{}finally{
    freshnessCheckRunning=false;
  }
}

document.addEventListener('visibilitychange',()=>{
  if(document.visibilityState==='visible')checkForFreshVersion();
});
window.addEventListener('pageshow',()=>checkForFreshVersion());
window.addEventListener('focus',()=>checkForFreshVersion());
checkForFreshVersion();
