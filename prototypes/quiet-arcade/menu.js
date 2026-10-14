/**
 * The four controls outside the canvas, and the one panel they open. They work
 * the same whether the scene started or the still fallback is showing.
 */
const panel = document.getElementById('panel');
const title = document.getElementById('panel-title');
const body = document.getElementById('panel-body');
const status = document.getElementById('status');

const ATMOSPHERES = [
  { id: 'arcade', name: 'Arcade', note: 'This scene', built: true },
  { id: 'forest', name: 'Forest', note: 'Not built yet', built: false },
  { id: 'coast', name: 'Coast', note: 'Not built yet', built: false },
];

let opener = null;
let onClose = null;

function arcade() { return window.__quietArcade && !window.__quietArcade.fallback ? window.__quietArcade : null; }

function open(name, heading, render, closeHook) {
  opener = document.activeElement;
  onClose = closeHook ?? null;
  status.textContent = '';
  title.textContent = heading;
  body.replaceChildren(...render());
  panel.hidden = false;
  panel.dataset.name = name;
  (body.querySelector('button:not([aria-disabled="true"])') ?? body.querySelector('button'))?.focus();
}

export function closePanel() {
  if (panel.hidden) return false;
  panel.hidden = true;
  delete panel.dataset.name;
  onClose?.(); onClose = null;
  opener?.focus(); opener = null;
  return true;
}

function closeButton() {
  const button = document.createElement('button');
  button.type = 'button'; button.className = 'quiet close'; button.textContent = 'Close';
  button.addEventListener('click', closePanel);
  return button;
}

function tryDemo() {
  arcade()?.setDemoLit(true);
  open('try-demo', 'Try demo', () => {
    const p = document.createElement('p');
    p.textContent = 'Prototype. The Harbor demo is not wired here. In the app, Try demo plays a 20 second film with two practice holds while sound and captions continue.';
    return [p, closeButton()];
  }, () => arcade()?.setDemoLit(false));
}

function atmosphere() {
  open('atmosphere', 'Atmosphere', () => {
    const list = document.createElement('ul');
    for (const one of ATMOSPHERES) {
      const item = document.createElement('li');
      const button = document.createElement('button');
      button.type = 'button';
      button.dataset.atmosphere = one.id;
      if (!one.built) button.setAttribute('aria-disabled', 'true');
      if (one.built) button.setAttribute('aria-current', 'true');
      const name = document.createElement('span'); name.textContent = one.name;
      const note = document.createElement('small'); note.textContent = one.note;
      button.append(name, note);
      button.addEventListener('click', () => {
        if (one.built) { status.textContent = 'Arcade.'; closePanel(); }
        else { status.textContent = `${one.name} is not built yet.`; }
      });
      item.append(button); list.append(item);
    }
    return [list, closeButton()];
  });
}

function help() {
  open('help', 'Help', () => {
    const list = document.createElement('ul');
    for (const [keys, does] of [
      ['Left, Right', 'choose a thing in the room'],
      ['Enter', 'greet the keeper or select a cabinet'],
      ['Escape', 'clear, or close this'],
      ['Up, Down', 'move between the menu and the room'],
      ['Still', 'keeps the room from moving'],
    ]) {
      const item = document.createElement('li');
      const kbd = document.createElement('kbd'); kbd.textContent = keys;
      const text = document.createElement('span'); text.textContent = does;
      item.append(kbd, text); list.append(item);
    }
    return [list, closeButton()];
  });
}

export function installMenu() {
  const still = document.getElementById('still');
  const applyStill = (on) => {
    still.setAttribute('aria-pressed', String(on));
    arcade()?.setStill(on);
  };
  applyStill(window.matchMedia('(prefers-reduced-motion: reduce)').matches);
  still.addEventListener('click', () => applyStill(still.getAttribute('aria-pressed') !== 'true'));
  document.getElementById('try-demo').addEventListener('click', tryDemo);
  document.getElementById('atmosphere').addEventListener('click', atmosphere);
  document.getElementById('help').addEventListener('click', help);
  panel.addEventListener('keydown', (event) => {
    const buttons = [...panel.querySelectorAll('button')];
    const i = buttons.indexOf(document.activeElement);
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      buttons[(i + (event.key === 'ArrowDown' ? 1 : buttons.length - 1)) % buttons.length]?.focus(); event.preventDefault();
    }
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape' && closePanel()) event.preventDefault();
  });
  window.__quietArcadeMenu = { closePanel, isOpen: () => !panel.hidden, panelName: () => panel.dataset.name ?? null };
}
