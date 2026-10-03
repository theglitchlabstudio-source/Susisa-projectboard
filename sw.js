const V='susisa-v8';
const SHELL=['./','index.html','config.js','manifest.webmanifest','icon-192.png','icon-512.png','icon-180.png'];
self.addEventListener('install',e=>{e.waitUntil(caches.open(V).then(c=>c.addAll(SHELL).catch(()=>{})).then(()=>self.skipWaiting()));});
self.addEventListener('activate',e=>{e.waitUntil(caches.keys().then(ks=>Promise.all(ks.filter(k=>k.startsWith('susisa-')&&k!==V&&k!=='susisa-ext').map(k=>caches.delete(k)))).then(()=>self.clients.claim()));});
self.addEventListener('fetch',e=>{
  const r=e.request; if(r.method!=='GET') return;
  const u=new URL(r.url);
  if(u.origin===location.origin){
    e.respondWith(fetch(r,{cache:'no-cache'}).then(res=>{ if(res.ok){ const cp=res.clone(); caches.open(V).then(c=>c.put(r,cp)); } return res; }).catch(()=>caches.match(r,{ignoreSearch:true}).then(m=>m||caches.match('index.html'))));
    return;
  }
  if(/gstatic\.com|fonts\.googleapis\.com|cdnjs\.cloudflare\.com/.test(u.host)){
    e.respondWith(caches.open('susisa-ext').then(c=>c.match(r).then(m=>{ const f=fetch(r).then(res=>{ if(res.ok||res.type==='opaque') c.put(r,res.clone()); return res; }).catch(()=>m); return m||f; })));
  }
});
