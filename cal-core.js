/* هستهٔ مشترک تقویم هر سه برد (plan، content، index). */
(function(){
function div(a,b){return ~~(a/b)}function mod(a,b){return a-~~(a/b)*b}
function jalCal(jy){var br=[-61,9,38,199,426,686,756,818,1111,1181,1210,1635,2060,2097,2192,2262,2324,2394,2456,3178],gy=jy+621,lj=-14,jp=br[0],jm,jump,leap,lg,march,n,i;for(i=1;i<br.length;i++){jm=br[i];jump=jm-jp;if(jy<jm)break;lj=lj+div(jump,33)*8+div(mod(jump,33),4);jp=jm}n=jy-jp;lj=lj+div(n,33)*8+div(mod(n,33)+3,4);if(mod(jump,33)===4&&jump-n===4)lj+=1;lg=div(gy,4)-div((div(gy,100)+1)*3,4)-150;march=20+lj-lg;if(jump-n<6)n=n-jump+div(jump+4,33)*33;leap=mod(mod(n+1,33)-1,4);if(leap===-1)leap=4;return{leap:leap,gy:gy,march:march}}
function g2d(gy,gm,gd){var d=div((gy+div(gm-8,6)+100100)*1461,4)+div(153*mod(gm+9,12)+2,5)+gd-34840408;return d-div(div(gy+100100+div(gm-8,6),100)*3,4)+752}
function d2g(jdn){var j=4*jdn+139361631;j=j+div(div(4*jdn+183187720,146097)*3,4)*4-3908;var i=div(mod(j,1461),4)*5+308,gd=div(mod(i,153),5)+1,gm=mod(div(i,153),12)+1,gy=div(j,1461)-100100+div(8-gm,6);return{gy:gy,gm:gm,gd:gd}}
function j2d(jy,jm,jd){var r=jalCal(jy);return g2d(r.gy,3,r.march)+(jm-1)*31-div(jm,7)*(jm-7)+jd-1}
function d2j(jdn){var gy=d2g(jdn).gy,jy=gy-621,r=jalCal(jy),f=g2d(gy,3,r.march),jd,jm,k=jdn-f;if(k>=0){if(k<=185){jm=1+div(k,31);jd=mod(k,31)+1;return{jy:jy,jm:jm,jd:jd}}else k-=186}else{jy-=1;k+=179;if(r.leap===1)k+=1}jm=7+div(k,30);jd=mod(k,30)+1;return{jy:jy,jm:jm,jd:jd}}

/* مناسبت‌ها ۱۴۰۵. منبع: pasoon.ir/years/1405 (تقویم رسمی) + چند روز جهانی. مناسبت‌های قمری با رؤیت ماه ممکنه یه روز جابه‌جا بشن. نشان: h تعطیل، m سوگواری. ایده = فرضیه برای کانسپت */
var LUNAR=[['1405/07/20','جمادی‌الاول',1448],['1405/08/20','جمادی‌الثانی',1448],['1405/09/20','رجب',1448],['1405/10/20','شعبان',1448],['1405/11/19','رمضان',1448],['1405/12/19','شوال',1448],['1406/01/18','ذی‌القعده',1448]];
var GM=['January','February','March','April','May','June','July','August','September','October','November','December'];
var EV={
'1405/08/06':[['روز جهانی انیمیشن','','کمیک سرآشپزهای سوسیس: روز خوبی برای یه قسمت']],
'1405/08/07':[['روز کوروش بزرگ','','']],'1405/08/08':[['روز نوجوان','','']],
'1405/08/09':[['هالووین','','استوری با سرآشپزهای عبوس؛ بدون تخفیف']],
'1405/08/10':[['جشن آبانگان','','']],
'1405/08/12':[['روز ساندویچ (آمریکا)','','یه پست جدی دربارهٔ اینکه هات‌داگ ساندویچ هست یا نه']],
'1405/08/13':[['روز دانش‌آموز','','']],'1405/08/15':[['جشن میانهٔ پاییز','','']],
'1405/08/22':[['شهادت حضرت فاطمه زهرا (س)','hm','']],
'1405/08/24':[['روز کتاب و کتابخوانی','','']],
'1405/08/29':[['روز جهانی کودک','','']],'1405/08/30':[['روز جهانی تلویزیون','','یه شوخی جدی با منوی تلویزیونی']],
'1405/09/01':[['جشن آذر','','']],
'1405/09/06':[['جمعهٔ سیاه (بلک‌فرایدی)','','ریل ضدتخفیف: اینجا هیچی ارزون‌تر نشد']],
'1405/09/07':[['روز نیروی دریایی','','']],
'1405/09/09':[['ولادت حضرت فاطمه؛ روز زن و مادر · جشن آذرگان','','پست تقدیر از مامان‌ها؛ بدون هدیهٔ تبلیغاتی']],
'1405/09/10':[['روز مجلس','','']],
'1405/09/15':[['روز حسابدار','','']],
'1405/09/16':[['روز دانشجو','','مشهد پر از دانشجوئه؛ استوری شب امتحان و فست‌فود']],
'1405/09/20':[['ولادت امام محمدباقر (ع)','','']],'1405/09/22':[['شهادت امام هادی (ع)','m','']],
'1405/09/25':[['روز پژوهش','','']],'1405/09/26':[['روز حمل‌ونقل','','']],
'1405/09/29':[['ولادت امام جواد (ع)','','']],
'1405/09/30':[['شب یلدا','','هات‌داگ کنار انار؟ کانسپت یلدا یه ماه قبل باید ببنده']],
'1405/10/01':[['جشن خرم‌روز؛ روز میلاد خورشید','','']],
'1405/10/02':[['ولادت امام علی (ع) و روز پدر','h','پست بابا و هات‌داگ؛ رفاقت پدر و پسر پشت پیشخوان']],
'1405/10/04':[['کریسمس','',''],['وفات حضرت زینب (س)','m','']],
'1405/10/11':[['سال نو میلادی ۲۰۲۷','','جمع‌بندی سال با سرآشپزها']],
'1405/10/14':[['شهادت امام موسی کاظم (ع)','m','']],
'1405/10/16':[['مبعث حضرت رسول (ص)','h','']],
'1405/10/22':[['ولادت امام حسین (ع)؛ روز پاسدار','','']],'1405/10/23':[['ولادت حضرت ابوالفضل؛ روز جانباز','','']],'1405/10/24':[['ولادت امام سجاد (ع)','','']],
'1405/10/30':[['ولادت حضرت علی‌اکبر؛ روز جوان','','']],
'1405/11/01':[['زادروز فردوسی','','']],'1405/11/02':[['جشن بهمنگان','','']],
'1405/11/04':[['نیمهٔ شعبان؛ ولادت حضرت قائم (عج)','h','']],
'1405/11/10':[['جشن سده','','گریل و آتیش: ریل سینمایی ماه؟']],
'1405/11/12':[['بازگشت امام خمینی به ایران','','']],'1405/11/15':[['جشن میانهٔ زمستان','','']],
'1405/11/19':[['آغاز ماه رمضان · روز نیروی هوایی','','از قبلش برنامهٔ ماه رمضان و ساعت کار رو با امیررضا ببند']],
'1405/11/22':[['پیروزی انقلاب اسلامی','h','']],
'1405/11/25':[['ولنتاین','','']],'1405/11/28':[['وفات حضرت خدیجه (س)','m','']],
'1405/12/03':[['ولادت امام حسن مجتبی (ع)','','']],
'1405/12/05':[['سپندارمذگان؛ روز عشق ایرانی · روز مهندس','','']],
'1405/12/06':[['شب قدر','m','']],'1405/12/07':[['ضربت خوردن امام علی (ع)','m','']],'1405/12/08':[['شب قدر','m','']],
'1405/12/09':[['شهادت امام علی (ع)','hm','']],'1405/12/10':[['شب قدر','m','']],
'1405/12/15':[['روز درختکاری','','']],'1405/12/17':[['روز جهانی زن','','']],
'1405/12/19':[['عید سعید فطر','h','پایان رمضان؛ اولین ناهار بعد از یه ماه']],'1405/12/20':[['تعطیل به مناسبت عید فطر','h','']],
'1405/12/25':[['شب چهارشنبه‌سوری','','']],
'1405/12/29':[['ملی شدن صنعت نفت · روز جهانی شادی','h','جمع‌بندی سال و برگشت بعد از نوروز']]};

var WD=['یکشنبه','دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه','شنبه'],MN=['فروردین','اردیبهشت','خرداد','تیر','مرداد','شهریور','مهر','آبان','آذر','دی','بهمن','اسفند'];
var TIER_COLOR={'reel-cine':'#D5222B','reel-simple':'#FFF9EC','post-pro':'#2C2C2C','post-graphic':'#F09E00','post-simple':'#FDF0D7','story-general':'#CFC3AC','story-count':'#FFD27A'};
function fa(s){return String(s==null?'':s).replace(/\d/g,function(d){return '۰۱۲۳۴۵۶۷۸۹'[d]})}
function esc(s){return String(s==null?'':s).replace(/[&<>"']/g,function(c){return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]})}
function pad(n){return (n<10?'0':'')+n}
function toJ(s){var p=s.split('/').map(Number);return j2d(p[0],p[1],p[2])}
function fromJ(n){var j=d2j(n);return j.jy+'/'+pad(j.jm)+'/'+pad(j.jd)}
function satIdx(s){var g=d2g(toJ(s));return (new Date(g.gy,g.gm-1,g.gd).getDay()+1)%7}
function wdName(s){var g=d2g(toJ(s));return WD[new Date(g.gy,g.gm-1,g.gd).getDay()]}
function today(){var t=new Date();return fromJ(g2d(t.getFullYear(),t.getMonth()+1,t.getDate()))}
function monthLen(y,m){return m<=6?31:m<=11?30:(j2d(y+1,1,1)-j2d(y,12,1))}
function greg(d){return d2g(toJ(d))}
function lunar(d){var r=null;for(var i=0;i<LUNAR.length;i++){if(LUNAR[i][0]<=d)r=LUNAR[i];else break}if(!r||d>='1406/02')return null;return {d:toJ(d)-toJ(r[0])+1,m:r[1],y:r[2]}}
var S={own:[],notes:{}};
function events(d){var a=(EV[d]||[]).map(function(e){return {t:e[0],h:e[1].indexOf('h')>=0,m:e[1].indexOf('m')>=0,i:e[2]||''}});S.own.forEach(function(e){if(e.date===d)a.unshift({t:e.label,own:true,i:''})});return a}
function isHol(d){return satIdx(d)===6||events(d).some(function(e){return e.h})}
function monthSub(m){var p=m.split('/').map(Number),a=m+'/01',b=m+'/'+pad(monthLen(p[0],p[1])),ga=greg(a),gb=greg(b),la=lunar(a),lb=lunar(b);
  var g=ga.gy===gb.gy?GM[ga.gm-1]+' – '+GM[gb.gm-1]+' '+ga.gy:GM[ga.gm-1]+' '+ga.gy+' – '+GM[gb.gm-1]+' '+gb.gy;
  return '<span dir="ltr">'+g+'</span>'+(la&&lb?' · '+la.m+(la.m!==lb.m?' – '+lb.m:'')+' '+fa(lb.y):'')}
/* o: {m, nav:fn(v)->attrs, cell:fn(d,n)->{cls,attrs,body,dots,add}, sel, extra} */
function monthHtml(o){var m=o.m,p=m.split('/').map(Number),len=monthLen(p[0],p[1]),lead=satIdx(m+'/01'),t=today();
  var h='<div class="sc-cal"><div class="sc-rings">'+Array(11).join('<i></i>')+'</div><div class="sc-head"><div class="sc-mn">'+MN[p[1]-1]+'</div><div class="sc-y">'+fa(p[0])+'</div><div class="sc-nav"><button class="sc-btn" '+o.nav(-1)+' aria-label="ماه قبل">→</button><button class="sc-btn" '+o.nav(0)+'>امروز</button><button class="sc-btn" '+o.nav(1)+' aria-label="ماه بعد">←</button></div><div class="sc-sub">'+monthSub(m)+'</div></div><div class="sc-wd">'+['شنبه','یکشنبه','دوشنبه','سه‌شنبه','چهارشنبه','پنج‌شنبه','جمعه'].map(function(d){return '<div>'+d+'</div>'}).join('')+'</div><div class="sc-grid">';
  for(var i=0;i<lead;i++)h+='<div class="sc-off" aria-hidden="true"></div>';
  for(var n=1;n<=len;n++){var d=m+'/'+pad(n),c=o.cell(d,n)||{},ev=events(d),g=greg(d),l=lunar(d);
    h+='<div class="sc-day '+(c.cls||'')+(satIdx(d)===6?' sc-fri':'')+(isHol(d)?' sc-hol':'')+(d===t?' sc-today':'')+(d<t?' sc-past':'')+(d===o.sel?' sc-sel':'')+'" '+(c.attrs||'')+'><div class="sc-dh"><span class="sc-dn">'+fa(n)+'</span>'+(l?'<span class="sc-dq">'+fa(l.d)+'</span>':'')+'<span class="sc-dg" dir="ltr">'+g.gd+(g.gd===1||n===1?' '+GM[g.gm-1].slice(0,3):'')+'</span>'+(c.add||'')+'</div>'+
      ev.slice(0,2).map(function(e){return '<span class="sc-evt'+(e.h?' h':'')+'">'+esc(e.t)+'</span>'}).join('')+(ev.length>2?'<span class="sc-evt">و '+fa(ev.length-2)+' مناسبت دیگه</span>':'')+(c.body||'')+
      '<div class="sc-dots">'+(c.dots||[]).map(function(x){return '<i style="background:'+x+'"></i>'}).join('')+'</div>'+(c.warn?'<span class="sc-warn">⚠ '+esc(c.warn)+'</span>':'')+'</div>'}
  var tail=(7-(lead+len)%7)%7;for(i=0;i<tail;i++)h+='<div class="sc-off" aria-hidden="true"></div>';
  return h+'</div></div>'}
/* o: {body, foot} */
function leafHtml(d,o){o=o||{};var p=d.split('/').map(Number),g=greg(d),l=lunar(d),ev=events(d),hol=isHol(d),nt=S.notes[d];
  return '<div class="sc-leaf'+(hol?' hol':'')+'"><div class="sc-lt">'+MN[p[1]-1]+' '+fa(p[0])+'<span dir="ltr">'+g.gd+' '+GM[g.gm-1]+' '+g.gy+'</span></div><div class="sc-ln">'+fa(p[2])+'</div><div class="sc-lw">'+wdName(d)+(l?'<small>'+fa(l.d)+' '+l.m+' '+fa(l.y)+'</small>':'')+'</div><div class="sc-lb">'+
   (ev.length?ev.map(function(e){return '<div class="sc-lev'+(e.h?' h':'')+'">'+(e.h?'تعطیل · ':'')+esc(e.t)+(e.i?'<small>ایده: '+esc(e.i)+'</small>':'')+'</div>'}).join(''):'<div class="sc-mute">مناسبت خاصی ثبت نشده.</div>')+
   (ev.some(function(e){return e.m})?'<div class="sc-lm">روز سوگواری؛ لحن محتوا آروم بمونه.</div>':'')+(nt?'<div class="sc-note">یادداشت روز: '+esc(nt)+'</div>':'')+
   '<div class="sc-ll">'+(o.body||'')+'</div>'+(o.foot||'')+'</div></div>'}
function occHtml(m,sel){var p=m.split('/').map(Number),len=monthLen(p[0],p[1]),h='';
  for(var n=1;n<=len;n++){var d=m+'/'+pad(n);events(d).forEach(function(e){h+='<button class="sc-occ'+(e.h?' h':'')+'" '+sel(d)+'><b>'+fa(n)+' '+MN[p[1]-1]+'</b><span>'+esc(e.t)+(e.h?' <em>تعطیل</em>':'')+(e.i?'<small>ایده: '+esc(e.i)+'</small>':'')+'</span></button>'})}
  return '<section class="sc-occs"><h2>مناسبت‌های '+MN[p[1]-1]+'</h2>'+(h||'<p class="sc-mute">برای این ماه مناسبتی ثبت نشده.</p>')+'<p class="sc-mute">مناسبت‌های قمری با رؤیت ماه ممکنه یه روز جابه‌جا بشن. ایده‌ها فرضیه‌ن؛ تأیید با امیررضا.</p></section>'}
function shift(m,n){var p=m.split('/').map(Number),i=p[0]*12+p[1]-1+n;return Math.floor(i/12)+'/'+pad(i%12+1)}
window.SCal={EV:EV,LUNAR:LUNAR,GM:GM,MN:MN,TIER_COLOR:TIER_COLOR,monthHtml:monthHtml,leafHtml:leafHtml,occHtml:occHtml,events:events,isHol:isHol,greg:greg,lunar:lunar,monthSub:monthSub,today:today,shift:shift,state:S,toJdn:toJ,fromJdn:fromJ,wdName:wdName};
})();
