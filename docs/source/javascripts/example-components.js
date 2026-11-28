//= require govuk/all.bundle.js
// Examples do not need to retain accordion preferences between page loads.
// Keep expansion in the current document without reading or writing storage.
window.GOVUKFrontend.initAll({ accordion: { rememberExpanded: false } });
// The generated heading and Show/Hide spans need a literal word boundary when
// the visually hidden divider is excluded from the visible control label.
// Preserve the upstream accessible name, expanded state and event handlers.
document.querySelectorAll('.govuk-accordion__section-toggle').forEach(toggle => {
  toggle.before(document.createTextNode(' '));
});
// Character count for the examples. It counts as people type and keeps the
// message and the error state in step, without the framework script.
document.querySelectorAll('[data-civica-character-count]').forEach(root => {
  const field = root.querySelector('textarea');
  const message = root.querySelector('.civica-character-count__message');
  const limit = Number(root.dataset.maxlength);
  if (!field || !message || !limit) return;
  const update = () => {
    const left = limit - field.value.length;
    const over = left < 0;
    const count = Math.abs(left);
    message.textContent = over
      ? 'You have ' + count + ' character' + (count === 1 ? '' : 's') + ' too many'
      : 'You have ' + count + ' character' + (count === 1 ? '' : 's') + ' remaining';
    message.classList.toggle('civica-error-message', over);
    message.classList.toggle('civica-hint', !over);
    field.classList.toggle('civica-textarea--error', over);
  };
  field.addEventListener('input', update);
});
