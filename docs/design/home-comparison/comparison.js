'use strict';
// Browser-only composition and focus model. This never imports or changes app code.
const studies = [];
for (const option of document.querySelectorAll('.option')) {
  const name = option.dataset.option;
  const screen = option.querySelector('.screen');
  const caption = option.querySelector('.caption');
  let page = 'home', lastAction = 'play';
  function button(id, label, primary = false) {
    return `<button data-id="${id}" class="${primary ? 'primary' : ''}"${id === 'play' && page === 'home' ? ' aria-label="Play: Harbor"' : id === 'details' ? ' aria-label="Details: Harbor"' : ''}>${label}</button>`;
  }
  function render(focus) {
    screen.className = `screen ${name}${page !== 'home' ? ' flow' : ''}${page === 'playback' || page === 'practicePlayback' ? ' playback' : ''}`;
    let content = '';
    if (page === 'home') {
      content = `<nav class="tv-nav" aria-label="Home navigation">${button('help','How it works')}${button('parents','Parents')}</nav><div class="hero"><h3>Calm Frames</h3><div class="actions">${button('play','Play',true)}${button('details','Details')}</div></div>`;
    } else {
      const titles = {details:'Harbor',practice:'Try the demo',parents:'Parents',help:'How it works',playback:'Harbor',practicePlayback:'Picture pause demo'};
      const copy = {details:'20 sec · No flashing found',practice:'20 sec · 2 picture pauses',parents:'Enter your household PIN on the TV.',help:'Flashing scenes are replaced by a still picture. Sound and captions continue.',playback:'Playback route simulation. No media is playing.',practicePlayback:'Practice route simulation. No media is playing.'};
      let actions = '';
      if (page === 'details') actions = button('play','Play',true) + button('practice','Try the demo');
      if (page === 'practice') actions = button('play','Play demo',true);
      if (page === 'parents') actions = '<p class="pin" aria-label="PIN not collected">○ ○ ○ ○</p>' + button('cancel','Cancel');
      content = `${button('back','Back')}<div class="content"><h3>${titles[page]}</h3><p>${copy[page]}</p><div class="actions">${actions}</div></div><span class="badge">Route simulation</span>`;
    }
    screen.innerHTML = `<div class="stage"><div class="art"></div><div class="shade"></div>${content}</div>`;
    const backButton = screen.querySelector('[data-id="back"]');
    if (backButton) backButton.classList.add('back');
    for (const control of screen.querySelectorAll('button')) {
      control.addEventListener('click', () => activate(control.dataset.id));
      control.addEventListener('focus', () => {
        if (page === 'home' && ['play','details'].includes(control.dataset.id)) lastAction = control.dataset.id;
        caption.textContent = `${name.toUpperCase()} · ${pageLabel()} · Focus: ${control.textContent}`;
      });
    }
    caption.textContent = `${name.toUpperCase()} · Home · Start at Play`;
    if (focus) screen.querySelector(`[data-id="${focus}"]`)?.focus();
  }
  function pageLabel() { return ({home:'Home',details:'Harbor Details',practice:'Practice Details',parents:'Parents PIN gate',help:'How it works',playback:'Harbor playback simulation',practicePlayback:'Practice playback simulation'})[page]; }
  function go(next, focus) { page = next; render(focus); }
  function back() {
    if (page === 'home') return;
    if (page === 'practicePlayback') return go('practice','play');
    if (page === 'practice') return go('details','practice');
    if (page === 'details') return go('home','details');
    if (page === 'parents') return go('home','parents');
    if (page === 'help') return go('home','help');
    if (page === 'playback') return go(playOrigin, 'play');
  }
  let playOrigin = 'home';
  function activate(id) {
    if (id === 'back' || id === 'cancel') return back();
    if (page === 'home') {
      if (id === 'play') { playOrigin = 'home'; return go('playback','back'); }
      return go(id, id === 'details' ? 'play' : id === 'parents' ? 'cancel' : 'back');
    }
    if (page === 'details' && id === 'practice') return go('practice','play');
    if (page === 'details' && id === 'play') { playOrigin = 'details'; return go('playback','back'); }
    if (page === 'practice' && id === 'play') return go('practicePlayback','back');
  }
  screen.addEventListener('keydown', event => {
    if (event.key === 'Escape') { event.preventDefault(); back(); return; }
    if (!event.key.startsWith('Arrow')) return;
    const id = document.activeElement.dataset.id;
    let target;
    if (page === 'home') {
      const graph = name === 'a'
        ? {play:{Right:'details',Up:'help'},details:{Left:'play',Up:'help'},help:{Right:'parents',Down:lastAction},parents:{Left:'help',Down:lastAction}}
        : {play:{Right:'details',Up:'help'},details:{Left:'play',Up:'parents'},help:{Right:'parents',Down:'play'},parents:{Left:'help',Down:'details'}};
      target = graph[id]?.[event.key.slice(5)];
    } else {
      const ids = [...screen.querySelectorAll('button')].map(b => b.dataset.id);
      const i = ids.indexOf(id);
      target = ids[Math.max(0, Math.min(ids.length - 1, i + (['ArrowRight','ArrowDown'].includes(event.key) ? 1 : -1)))];
    }
    event.preventDefault();
    if (target) screen.querySelector(`[data-id="${target}"]`)?.focus();
  });
  studies.push({reset:()=>{page='home';lastAction='play';render();}});
  render();
}
for (const mode of ['gray','color']) document.getElementById(mode).onclick = () => {
  document.body.classList.toggle('gray',mode==='gray');
  for (const id of ['gray','color']) document.getElementById(id).setAttribute('aria-pressed',String(id===mode));
};
for (const button of document.querySelectorAll('[data-view]')) button.onclick = () => {
  const view = button.dataset.view;
  document.body.classList.toggle('single',view!=='both');
  for (const option of document.querySelectorAll('.option')) option.classList.toggle('hidden',view!=='both' && option.dataset.option!==view);
  for (const b of document.querySelectorAll('[data-view]')) b.setAttribute('aria-pressed',String(b===button));
};
document.getElementById('reset').onclick = () => studies.forEach(study=>study.reset());
