(() => {
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const nav = document.querySelector('.navbar');
  const progress = document.querySelector('.scroll-progress');
  const updateScroll = () => {
    const y = window.scrollY;
    nav?.classList.toggle('scrolled', y > 24);
    if (progress) {
      const max = document.documentElement.scrollHeight - innerHeight;
      progress.style.transform = `scaleX(${max > 0 ? y / max : 0})`;
    }
  };
  addEventListener('scroll', updateScroll, {passive:true}); updateScroll();

  const menuBtn = document.querySelector('.menu-toggle');
  const navPanel = document.querySelector('.links');
  menuBtn?.addEventListener('click', () => {
    const open = document.body.classList.toggle('nav-open');
    menuBtn.setAttribute('aria-expanded', open ? 'true':'false');
  });

  if (!reduced) {
    const io = new IntersectionObserver(entries => entries.forEach(e => {
      if (e.isIntersecting) { e.target.classList.add('is-visible'); io.unobserve(e.target); }
    }), {threshold:.12, rootMargin:'0px 0px -5% 0px'});
    document.querySelectorAll('[data-reveal], section > .section-head, .card, .experience-card, .offer-card, .metric-card').forEach((el,i) => {
      el.classList.add('reveal'); el.style.setProperty('--delay', `${Math.min(i%8,6)*55}ms`); io.observe(el);
    });

    document.querySelectorAll('[data-parallax]').forEach(el => addEventListener('scroll', () => {
      const r=el.getBoundingClientRect(); if(r.bottom>0 && r.top<innerHeight) el.style.transform=`translate3d(0,${(r.top-innerHeight/2)*-.025}px,0) scale(1.04)`;
    }, {passive:true}));
  }

  document.querySelectorAll('[data-count]').forEach(el => {
    const target = Number(el.dataset.count || 0); if (!target || reduced) return;
    const obs = new IntersectionObserver(([e]) => { if(!e.isIntersecting) return; obs.disconnect(); const start=performance.now();
      const tick=t=>{ const p=Math.min(1,(t-start)/900); el.textContent=Math.round(target*(1-Math.pow(1-p,3))).toLocaleString('en-IN'); if(p<1) requestAnimationFrame(tick);}; requestAnimationFrame(tick);
    }); obs.observe(el);
  });
})();

/* BrewAI scroll-controlled story timeline */
(() => {
  const story = document.getElementById('brewaiStory');
  if (!story || window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  const stage = story.querySelector('.story-stage');
  const stepEl = document.getElementById('storyStep');
  const clamp=(v,a=0,b=1)=>Math.max(a,Math.min(b,v));
  const range=(p,a,b)=>clamp((p-a)/(b-a));
  const mix=(a,b,t)=>a+(b-a)*t;
  let ticking=false;
  function render(){
    ticking=false;
    const r=story.getBoundingClientRect();
    const travel=story.offsetHeight-innerHeight;
    const p=clamp(-r.top/Math.max(1,travel));
    stage.style.setProperty('--story-progress',p.toFixed(4));
    const intro=range(p,0,.18), gather=range(p,.18,.48), think=range(p,.46,.70), reveal=range(p,.68,.94);
    stage.style.setProperty('--word-left-x',`${mix(0,-36,gather)}vw`);
    stage.style.setProperty('--word-right-x',`${mix(0,36,gather)}vw`);
    stage.style.setProperty('--word-opacity',`${mix(.92,.08,gather)}`);
    stage.style.setProperty('--product-scale',`${mix(.72,1.04,range(p,0,.48))}`);
    stage.style.setProperty('--product-rotate',`${mix(-5,0,range(p,0,.42))}deg`);
    stage.style.setProperty('--halo-rot',`${p*180}deg`);
    stage.style.setProperty('--halo-scale',`${mix(1,1.22,think)}`);
    stage.style.setProperty('--chip-opacity',`${Math.min(range(p,.12,.25),1-range(p,.55,.68))}`);
    const collapse=range(p,.34,.58);
    stage.style.setProperty('--mood-x',`${mix(-60,37,collapse)}vw`); stage.style.setProperty('--mood-y',`${mix(30,22,collapse)}vh`);
    stage.style.setProperty('--temp-x',`${mix(60,-37,collapse)}vw`); stage.style.setProperty('--temp-y',`${mix(20,19,collapse)}vh`);
    stage.style.setProperty('--taste-x',`${mix(-60,37,collapse)}vw`); stage.style.setProperty('--taste-y',`${mix(-20,-23,collapse)}vh`);
    stage.style.setProperty('--budget-x',`${mix(60,-37,collapse)}vw`); stage.style.setProperty('--budget-y',`${mix(-30,-22,collapse)}vh`);
    const thinkVis=Math.min(range(p,.48,.57),1-range(p,.68,.76));
    stage.style.setProperty('--thinking-opacity',thinkVis); stage.style.setProperty('--thinking-y',`${mix(18,0,thinkVis)}px`);
    stage.style.setProperty('--ai-opacity',`${Math.min(range(p,.48,.58),1-range(p,.69,.78))}`);
    stage.style.setProperty('--ai-scale',`${mix(0,1,range(p,.48,.61))}`);
    stage.style.setProperty('--glow-scale',`${mix(1,1.5,think)}`); stage.style.setProperty('--story-glow',`${mix(.35,.72,think)}`);
    stage.style.setProperty('--result-opacity',reveal); stage.style.setProperty('--result-y',`${mix(60,0,reveal)}px`);
    stage.style.setProperty('--product-clip',`${mix(0,7,reveal)}%`);
    if(stepEl) stepEl.textContent=p<.22?'01':p<.48?'02':p<.72?'03':'04';
  }
  function request(){if(!ticking){ticking=true;requestAnimationFrame(render)}}
  addEventListener('scroll',request,{passive:true}); addEventListener('resize',request); render();
})();
