/* Documentation demonstrations only. Home Assistant settings live in civica-ui.js. */
(() => {
  const demo = document.querySelector('[data-palette-demo]');
  if (!demo) return;
  const select = demo.querySelector('select');
  const muted = demo.querySelector('input[type="checkbox"]');
  const status = demo.querySelector('[role="status"]');
  const update = () => {
    const option = select.selectedOptions[0];
    demo.style.setProperty('--demo-primary', option.dataset[muted.checked ? 'muted' : 'vivid']);
    demo.style.setProperty('--demo-canvas', muted.checked ? option.dataset.canvas : '#ffffff');
    status.textContent = `${option.textContent}, ${muted.checked ? 'Muted' : 'Vivid'} preview. These choices affect this example only.`;
  };
  select.addEventListener('change', update);
  muted.addEventListener('change', update);
})();

/* Progressive enhancement: navigation, catalogue and source tabs remain usable without JS. */
(() => {
  const narrow = matchMedia('(max-width:760px)');
  const mainToggle = document.querySelector('.c-menu-toggle');
  const mainLinks = document.getElementById('primary-navigation');
  const arrangeNavigation = () => {
    if (mainToggle && mainLinks) {
      mainToggle.hidden = !narrow.matches;
      mainToggle.setAttribute('aria-expanded', String(!narrow.matches));
      mainLinks.hidden = narrow.matches;
    }
  };
  arrangeNavigation(); narrow.addEventListener('change', arrangeNavigation);
  mainToggle?.addEventListener('click', () => {
    mainLinks.hidden = !mainLinks.hidden;
    mainToggle.setAttribute('aria-expanded', String(!mainLinks.hidden));
  });
  for (const tabs of document.querySelectorAll('[data-code-tabs]')) {
    const list = tabs.querySelector('.c-code-tabs__list');
    const links = [...list.querySelectorAll('a')];
    const panels = links.map(link => document.getElementById(link.hash.slice(1)));
    list.setAttribute('role', 'tablist'); list.setAttribute('aria-label', 'Example code');
    const activate = index => links.forEach((link, i) => {
      link.setAttribute('aria-selected', String(i === index)); link.tabIndex = i === index ? 0 : -1;
      panels[i].hidden = i !== index;
    });
    links.forEach((link, i) => {
      link.id = `tab-${panels[i].id}`; link.setAttribute('role', 'tab'); link.setAttribute('aria-controls', panels[i].id);
      panels[i].setAttribute('role', 'tabpanel'); panels[i].setAttribute('aria-labelledby', link.id); panels[i].tabIndex = 0;
      link.addEventListener('click', event => { event.preventDefault(); activate(i); });
      link.addEventListener('keydown', event => {
        const next = event.key === 'ArrowRight' ? (i + 1) % links.length : event.key === 'ArrowLeft' ? (i + links.length - 1) % links.length : event.key === 'Home' ? 0 : event.key === 'End' ? links.length - 1 : null;
        if (next !== null) { event.preventDefault(); activate(next); links[next].focus(); }
      });
    }); activate(0);
  }
  for (const button of document.querySelectorAll('[data-copy]')) {
    if (!navigator.clipboard) continue;
    button.hidden = false;
    button.addEventListener('click', async () => {
      const status = button.closest('.c-example').querySelector('.c-copy-status');
      try { await navigator.clipboard.writeText(document.getElementById(button.dataset.copy).textContent); status.textContent = 'HTML copied.'; }
      catch { status.textContent = 'Could not copy automatically. Select and copy the HTML below.'; }
    });
  }
  window.addEventListener('message', event => {
    if (event.origin !== location.origin || event.data?.type !== 'civica-example-height' || !Number.isFinite(event.data.height)) return;
    const frame = [...document.querySelectorAll('.c-example__frame')].find(item => item.contentWindow === event.source);
    if (frame) frame.height = String(Math.max(100, Math.min(5000, Math.ceil(event.data.height))));
  });
  const filter = document.querySelector('[data-catalogue-filter]');
  if (filter) {
    const items = [...document.querySelectorAll('[data-catalogue-item]')];
    const status = document.querySelector('[data-catalogue-status]');
    const update = () => {
      const words = filter.value.toLocaleLowerCase().trim().split(/\s+/).filter(Boolean);
      let count = 0;
      items.forEach(item => { item.hidden = !words.every(word => item.textContent.toLocaleLowerCase().includes(word)); if (!item.hidden) count++; });
      for (const group of document.querySelectorAll('[data-catalogue-group]')) group.hidden = !group.querySelector('[data-catalogue-item]:not([hidden])');
      status.textContent = `${count} ${count === 1 ? 'page' : 'pages'}${words.length ? ' found' : ''}.`;
    };
    filter.value = new URLSearchParams(location.search).get('q') || ''; filter.addEventListener('input', update); update();
  }
})();

/* Components combobox (ARIA 1.2 editable combobox with a list popup).
   The data is the same inventory-derived record as /reference/component-index.json,
   embedded in the page, so searching makes no network request. Without JavaScript
   the full A to Z list below remains the way to find a component. */
(() => {
  const root = document.querySelector('[data-component-search]');
  const source = document.getElementById('component-search-data');
  if (!root || !source) return;
  const entries = JSON.parse(source.textContent);
  const input = root.querySelector('[role="combobox"]');
  const listbox = document.getElementById(input.getAttribute('aria-controls'));
  const status = root.querySelector('[data-component-search-status]');
  const limit = 50;
  const kinds = { parent: 'Component', child: 'Element', grandchild: 'Variant or part' };
  let results = [];
  let active = -1;
  root.hidden = false;

  const describe = entry => entry.k === 'parent'
    ? `${kinds.parent}${entry.a ? '' : ', specification not yet published'}`
    : `${kinds[entry.k]} in ${entry.o}${entry.w ? `, within ${entry.w}` : ''}${entry.a ? '' : ', specification not yet published'}`;
  const rank = (entry, query) => {
    const name = entry.n.toLocaleLowerCase();
    const bare = name.replace(/^<|>$/g, '');
    if (name === query || bare === query) return 0;
    if (name.startsWith(query) || bare.startsWith(query)) return 1;
    if (name.includes(query)) return 2;
    return entry.k === 'parent' && entry.o.toLocaleLowerCase().includes(query) ? 3 : -1;
  };
  const close = () => {
    input.setAttribute('aria-expanded', 'false');
    input.removeAttribute('aria-activedescendant');
    listbox.hidden = true;
    active = -1;
  };
  const highlight = index => {
    const options = [...listbox.children];
    options.forEach((option, i) => option.setAttribute('aria-selected', String(i === index)));
    active = index;
    if (index < 0) { input.removeAttribute('aria-activedescendant'); return; }
    input.setAttribute('aria-activedescendant', options[index].id);
    options[index].scrollIntoView({ block: 'nearest' });
  };
  const go = entry => {
    close();
    if (entry.h.startsWith('#')) {
      location.hash = entry.h;
      const target = document.getElementById(entry.h.slice(1));
      target?.setAttribute('tabindex', '-1');
      target?.focus();
    } else location.assign(entry.h);
  };
  const render = () => {
    const query = input.value.toLocaleLowerCase().trim();
    listbox.replaceChildren();
    if (!query) { results = []; status.textContent = ''; close(); return; }
    results = entries.map((entry, order) => ({ entry, order, score: rank(entry, query) }))
      .filter(item => item.score >= 0)
      .sort((a, b) => a.score - b.score || a.order - b.order)
      .map(item => item.entry);
    if (!results.length) { status.textContent = 'No components or elements match.'; close(); return; }
    results.slice(0, limit).forEach((entry, i) => {
      const option = document.createElement('li');
      option.id = `component-option-${i}`;
      option.setAttribute('role', 'option');
      option.setAttribute('aria-selected', 'false');
      option.className = 'c-component-search__option';
      const name = document.createElement('span');
      name.className = 'c-component-search__name';
      name.textContent = entry.n;
      const meta = document.createElement('span');
      meta.className = 'c-component-search__meta';
      meta.textContent = describe(entry);
      option.append(name, ' ', meta);
      option.addEventListener('mousedown', event => event.preventDefault());
      option.addEventListener('click', () => go(entry));
      listbox.append(option);
    });
    listbox.hidden = false;
    input.setAttribute('aria-expanded', 'true');
    active = -1;
    input.removeAttribute('aria-activedescendant');
    const shown = Math.min(results.length, limit);
    status.textContent = `${results.length} ${results.length === 1 ? 'result' : 'results'}${results.length > limit ? `, showing the first ${shown}` : ''}.`;
  };
  input.addEventListener('input', render);
  input.addEventListener('keydown', event => {
    const count = listbox.children.length;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      if (listbox.hidden) { render(); if (!listbox.children.length) return; }
      highlight(active + 1 < listbox.children.length ? active + 1 : 0);
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      if (!count || listbox.hidden) return;
      highlight(active > 0 ? active - 1 : count - 1);
    } else if (event.key === 'Enter') {
      if (!listbox.hidden && active >= 0) { event.preventDefault(); go(results[active]); }
      else if (!listbox.hidden && results.length === 1) { event.preventDefault(); go(results[0]); }
    } else if (event.key === 'Escape') {
      if (!listbox.hidden) { event.preventDefault(); close(); }
      else if (input.value) { event.preventDefault(); input.value = ''; status.textContent = ''; }
    }
  });
  input.addEventListener('blur', () => setTimeout(close, 0));
})();
