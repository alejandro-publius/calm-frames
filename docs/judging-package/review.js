'use strict';

// Progressive enhancement: without JavaScript every walkthrough stop is visible.
const stops = Array.from(document.querySelectorAll('.tour-panel'));
const choices = Array.from(document.querySelectorAll('[data-stop]'));
const status = document.getElementById('tour-status');
const previous = document.getElementById('previous-stop');
const next = document.getElementById('next-stop');
const labels = ['Choose', 'Watch', 'Check the edition', 'Read the record', 'See the limits'];
let selected = 0;

function showStop(index) {
  selected = Math.max(0, Math.min(stops.length - 1, index));
  stops.forEach((stop, position) => { stop.hidden = position !== selected; });
  choices.forEach((choice, position) => {
    choice.setAttribute('aria-pressed', String(position === selected));
  });
  previous.disabled = selected === 0;
  next.disabled = selected === stops.length - 1;
  status.textContent = `Stop ${selected + 1} of ${stops.length}: ${labels[selected]}`;
}

choices.forEach((choice, index) => {
  choice.addEventListener('click', () => showStop(index));
});
previous.addEventListener('click', () => {
  showStop(selected - 1);
  if (previous.disabled) next.focus();
});
next.addEventListener('click', () => {
  showStop(selected + 1);
  if (next.disabled) previous.focus();
});
document.querySelector('.tour-controls').hidden = false;
document.querySelector('.tour-footer').hidden = false;
showStop(0);
