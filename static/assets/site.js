(function(){
  var d=document;
  function track(ev,params){try{window.dataLayer=window.dataLayer||[];window.dataLayer.push(Object.assign({event:ev},params||{}));if(typeof window.gtag==='function'){window.gtag('event',ev,params||{});}}catch(e){}}

  // menu
  var burger=d.querySelector('.burger'),mnav=d.getElementById('mnav');
  if(burger&&mnav){
    var closeBtn=mnav.querySelector('.close');
    function setOpen(o){mnav.classList.toggle('open',o);burger.setAttribute('aria-expanded',o?'true':'false');d.body.style.overflow=o?'hidden':'';if(o){closeBtn.focus();}else{burger.focus();}}
    burger.addEventListener('click',function(){setOpen(true);});
    closeBtn.addEventListener('click',function(){setOpen(false);});
    mnav.addEventListener('click',function(e){if(e.target.tagName==='A'){mnav.classList.remove('open');burger.setAttribute('aria-expanded','false');d.body.style.overflow='';}});
    d.addEventListener('keydown',function(e){if(e.key==='Escape'&&mnav.classList.contains('open')){setOpen(false);}});
  }

  // reveal
  var rv=d.querySelectorAll('.rv');
  if('IntersectionObserver' in window){
    var io=new IntersectionObserver(function(es){es.forEach(function(en){if(en.isIntersecting){en.target.classList.add('in');io.unobserve(en.target);}});},{rootMargin:'0px 0px -8% 0px'});
    rv.forEach(function(el){io.observe(el);});
  }else{rv.forEach(function(el){el.classList.add('in');});}

  // mobile bar after hero
  var bar=d.querySelector('.mbar'),hero=d.getElementById('uvod'),kontakt=d.getElementById('kontakt');
  if(bar&&hero){
    var heroOut=false,inContact=false;
    function upd(){bar.classList.toggle('show',heroOut&&!inContact);}
    if('IntersectionObserver' in window){
      new IntersectionObserver(function(es){heroOut=!es[0].isIntersecting;upd();}).observe(hero);
      if(kontakt){new IntersectionObserver(function(es){inContact=es[0].isIntersecting;upd();}).observe(kontakt);}
    }else{bar.classList.add('show');}
  }

  // preselect topic from CTA
  d.querySelectorAll('[data-topic]').forEach(function(a){a.addEventListener('click',function(){var r=d.querySelector('#poptavka input[name=tema][value="'+a.getAttribute('data-topic')+'"]');if(r){r.checked=true;}});});

  // tracking
  d.querySelectorAll('[data-ev]').forEach(function(a){a.addEventListener('click',function(){track(a.getAttribute('data-ev'),{link_url:a.href});});});

  // form validation
  var f=d.getElementById('poptavka');
  if(f){
    var err=f.querySelector('.err');
    f.addEventListener('submit',function(e){
      var ok=f.jmeno.value.trim()&&f.telefon.value.trim().replace(/\D/g,'').length>=9&&f.gdpr.checked;
      if(!ok){e.preventDefault();err.hidden=false;var first=!f.jmeno.value.trim()?f.jmeno:(f.telefon.value.trim().replace(/\D/g,'').length<9?f.telefon:f.gdpr);first.focus();return;}
      err.hidden=true;
      var t=f.querySelector('input[name=tema]:checked');
      track('generate_lead',{form:'poptavka',tema:t?t.value:''});
    });
  }
  var eb=d.querySelector('form[name=ebook]');
  if(eb){eb.addEventListener('submit',function(){track('generate_lead',{form:'ebook'});});}
})();
(function(){
  var d=document;
  // archiv: filtr
  var fl=d.querySelector('.filters'),sold=d.getElementById('sold');
  if(fl&&sold){fl.addEventListener('click',function(e){var b=e.target.closest('button');if(!b)return;fl.querySelectorAll('button').forEach(function(x){x.setAttribute('aria-pressed',x===b?'true':'false');});var f=b.getAttribute('data-f');sold.querySelectorAll('li').forEach(function(li){li.hidden=!(f==='Vše'||li.getAttribute('data-k')===f);if(!li.hidden)li.classList.add('in');});});}
  // galerie
  var lb=d.querySelector('.lb'),btns=[].slice.call(d.querySelectorAll('.gal button'));
  if(lb&&btns.length){
    var img=lb.querySelector('img'),cnt=lb.querySelector('.cnt'),i=0,last=null;
    function show(n){i=(n+btns.length)%btns.length;img.src=btns[i].getAttribute('data-full');cnt.textContent=(i+1)+' / '+btns.length;}
    function open(n){last=d.activeElement;show(n);lb.classList.add('open');d.body.style.overflow='hidden';lb.querySelector('.x').focus();}
    function close(){lb.classList.remove('open');d.body.style.overflow='';if(last)last.focus();}
    btns.forEach(function(b,n){b.addEventListener('click',function(){open(n);});});
    lb.querySelector('.x').addEventListener('click',close);
    lb.querySelector('.pv').addEventListener('click',function(){show(i-1);});
    lb.querySelector('.nx').addEventListener('click',function(){show(i+1);});
    lb.addEventListener('click',function(e){if(e.target===lb)close();});
    d.addEventListener('keydown',function(e){if(!lb.classList.contains('open'))return;if(e.key==='Escape')close();if(e.key==='ArrowLeft')show(i-1);if(e.key==='ArrowRight')show(i+1);});
    var x0=null;lb.addEventListener('touchstart',function(e){x0=e.touches[0].clientX;},{passive:true});lb.addEventListener('touchend',function(e){if(x0===null)return;var dx=e.changedTouches[0].clientX-x0;if(Math.abs(dx)>40)show(i+(dx<0?1:-1));x0=null;});
  }
})();

(function(){var b=document.querySelector('.gal-more');if(b){b.addEventListener('click',function(){document.querySelector('.gal').classList.add('all');b.remove();});}})();
(function(){
  var d=document;
  function num(v){return parseFloat(String(v).replace(/\s/g,'').replace(',','.'))||0;}
  function kc(n){return Math.round(n).toLocaleString('cs-CZ')+' Kč';}
  function out(root,k,v){var e=root.querySelector('[data-o="'+k+'"]');if(e)e.textContent=v;return e;}
  // formátování čísel v polích
  d.querySelectorAll('.calc input[inputmode=numeric]').forEach(function(i){i.addEventListener('blur',function(){var n=num(i.value);if(n)i.value=Math.round(n).toLocaleString('cs-CZ');});});
  var h=d.getElementById('hypo');
  if(h){var f=h.querySelector('form');function calc(){var cena=num(f.cena.value),vl=num(f.vlastni.value),r=num(f.sazba.value)/100/12,n=num(f.roky.value)*12,P=Math.max(cena-vl,0);
    var m=r>0?P*r/(1-Math.pow(1+r,-n)):P/n;var ltv=cena?P/cena*100:0;
    out(h,'splatka',isFinite(m)&&m>0?kc(m):'–');out(h,'uver',kc(P));out(h,'ltv',ltv.toFixed(1).replace('.',',')+' %');out(h,'celkem',kc(m*n));out(h,'uroky',kc(m*n-P));
    var inv=f.querySelector('input[name=ucel]:checked').value==='invest',lim=inv?70:(f.mlady.checked?90:80),w=h.querySelector('[data-o=warn]');
    if(ltv>lim){w.hidden=false;w.textContent='LTV '+ltv.toFixed(0)+' % je nad doporučeným limitem ČNB '+lim+' %. Banka nejspíš bude chtít vyšší vlastní zdroje, alespoň '+kc(cena*(100-lim)/100)+'.';}else w.hidden=true;}
    f.addEventListener('input',calc);f.addEventListener('change',calc);calc();}
  var y=d.getElementById('vynos');
  if(y){var g=y.querySelector('form');function calc2(){var cena=num(g.cena.value),nk=num(g.naklady.value),naj=num(g.najem.value),mes=num(g.mesicni.value),pr=Math.min(num(g.prazdno.value),12);
    var inv=cena+nk,hr=cena?naj*12/cena*100:0,prij=naj*(12-pr)-mes*12,ci=inv?prij/inv*100:0;
    out(y,'hruby',hr.toFixed(2).replace('.',',')+' %');out(y,'cisty',ci.toFixed(2).replace('.',',')+' %');out(y,'prijem',kc(prij));out(y,'navrat',prij>0?(inv/prij).toFixed(1).replace('.',',')+' let':'–');}
    g.addEventListener('input',calc2);calc2();}
  // odhad: 2 kroky
  var o=d.getElementById('odhad');
  if(o){var s1=o.querySelector('[data-step="1"]'),s2=o.querySelector('[data-step="2"]'),tabs=o.querySelectorAll('.wiz-steps span'),err=o.querySelector('.err');
    o.querySelector('.next').addEventListener('click',function(){if(!o.adresa.value.trim()){o.adresa.focus();o.adresa.setAttribute('aria-invalid','true');return;}s1.hidden=true;s2.hidden=false;tabs[0].classList.remove('on');tabs[1].classList.add('on');o.jmeno.focus();try{window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:'odhad_krok2'});}catch(e){}});
    o.querySelector('.back').addEventListener('click',function(){s2.hidden=true;s1.hidden=false;tabs[1].classList.remove('on');tabs[0].classList.add('on');});
    o.addEventListener('submit',function(e){var ok=o.jmeno.value.trim()&&o.telefon.value.replace(/\D/g,'').length>=9&&o.gdpr.checked;if(!ok){e.preventDefault();err.hidden=false;return;}try{window.dataLayer=window.dataLayer||[];window.dataLayer.push({event:'generate_lead',form:'odhad'});}catch(e2){}});}
})();
