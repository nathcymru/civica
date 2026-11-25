// Reads the Civica guidance pages straight from docs/source and returns them
// as plain data an LLM can use: front matter, Markdown body, and every
// example's title, description and visible text. No Ruby build is needed.
//
// Why read the source: the published HTML wraps the guidance in layout and
// scripts. The source pages already hold the prose in Markdown, and the
// examples live in docs/data/*examples.yml, so resolving the example helper
// calls here removes the one place content was hidden from readers.
//
// Usage: node scripts/guidance-export.mjs            (summary and gap report)
//        node scripts/guidance-export.mjs --gaps     (also list each gap)
//        node scripts/guidance-export.mjs --out dir  (one JSON file per page)
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import YAML from 'yaml';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const sourceDir = path.join(root, 'docs', 'source');
const dataDir = path.join(root, 'docs', 'data');
const SECTIONS = ['styles', 'content', 'components', 'patterns', 'accessibility', 'get-started', 'home-assistant', 'publishing', 'community'];
const PAGE_SUFFIX = '.html.md.erb';

function walk(dir) {
  return fs.readdirSync(dir, { withFileTypes: true }).flatMap((e) =>
    e.isDirectory() ? walk(path.join(dir, e.name)) : [path.join(dir, e.name)]);
}

// Visible text of an example's HTML, so the example can be read without a browser.
export function htmlToText(html) {
  return String(html)
    .replace(/<(script|style)[\s\S]*?<\/\1>/gi, '')
    .replace(/<svg[\s\S]*?<\/svg>/gi, (svg) => {
      const label = /<title[^>]*>([\s\S]*?)<\/title>/i.exec(svg);
      return label ? ` [Image: ${label[1].trim()}] ` : ' ';
    })
    .replace(/<img[^>]*alt="([^"]*)"[^>]*>/gi, ' [Image: $1] ')
    .replace(/<\/(p|div|li|tr|h[1-6]|article|section|figcaption|caption)>/gi, '\n')
    .replace(/<br\s*\/?>/gi, '\n')
    .replace(/<\/(td|th)>/gi, ' | ')
    .replace(/<[^>]+>/g, '')
    .replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&').replace(/&lt;/g, '<').replace(/&gt;/g, '>')
    .replace(/&quot;/g, '"').replace(/&#39;|&apos;/g, "'")
    .split('\n').map((l) => l.replace(/[ \t]+/g, ' ').trim()).filter(Boolean).join('\n');
}

export function loadExamples() {
  const examples = {};
  for (const file of fs.readdirSync(dataDir).filter((f) => f.endsWith('examples.yml')).sort()) {
    const doc = YAML.parse(fs.readFileSync(path.join(dataDir, file), 'utf8')) || {};
    for (const [id, spec] of Object.entries(doc.examples || {})) {
      examples[id] = {
        id,
        title: spec.title || null,
        description: spec.description || null,
        device: spec.device || null,
        text: htmlToText(spec.html || ''),
        html: spec.html || '',
        source: `docs/data/${file}`,
      };
    }
  }
  return examples;
}

// Replaces ERB with readable content. Example helpers become the example's own
// text. Anything else that builds content in Ruby is recorded as dynamic, so a
// reader knows the Markdown is not the whole page.
export function resolveBody(raw, examples) {
  const dynamic = [];
  const usedExamples = [];
  let body = raw.replace(/<%=\s*(?:colour_)?example\(\s*'([^']+)'[^%]*%>/g, (_, id) => {
    const ex = examples[id];
    if (!ex) { dynamic.push(`unknown example ${id}`); return ''; }
    usedExamples.push(id);
    const lines = [`> Example \`${id}\`${ex.title ? `: ${ex.title}` : ''}`];
    if (ex.description) lines.push(`> ${ex.description}`);
    if (ex.text) lines.push('>', ...ex.text.split('\n').map((l) => `> ${l}`));
    return lines.join('\n');
  });
  body = body.replace(/<%=([\s\S]*?)%>/g, (_, expr) => {
    const e = expr.trim().replace(/\s+/g, ' ');
    dynamic.push(e.slice(0, 80));
    return `[Generated content not in this file: ${e.slice(0, 60)}]`;
  });
  const blocks = body.match(/<%[\s\S]*?%>/g) || [];
  if (blocks.length) dynamic.push(`${blocks.length} Ruby block(s)`);
  body = body.replace(/<%[\s\S]*?%>/g, '');
  return { body: body.trim(), dynamic, usedExamples: [...new Set(usedExamples)] };
}

export function loadPages() {
  const examples = loadExamples();
  const pages = [];
  for (const file of walk(sourceDir).filter((f) => f.endsWith(PAGE_SUFFIX)).sort()) {
    const rel = path.relative(sourceDir, file);
    const urlPath = '/' + rel.replace(PAGE_SUFFIX, '.html');
    const text = fs.readFileSync(file, 'utf8');
    const m = /^---\n([\s\S]*?)\n---\n/.exec(text);
    if (!m) continue;
    const fm = YAML.parse(m[1]) || {};
    const { body, dynamic, usedExamples } = resolveBody(text.slice(m[0].length), examples);
    const section = fm.section || (SECTIONS.includes(rel.split(path.sep)[0]) ? rel.split(path.sep)[0] : null);
    pages.push({
      path: urlPath,
      file: path.join('docs', 'source', rel),
      section,
      group: fm.group || null,
      title: fm.title || null,
      description: fm.description || null,
      status: fm.status || null,
      nav_order: fm.nav_order ?? null,
      updated_on: fm.updated_on ? String(fm.updated_on).slice(0, 10) : null,
      ai_instructions: fm.ai_instructions || null,
      ai_related: fm.ai_related || [],
      examples: usedExamples,
      dynamic,
      body,
    });
  }
  return { pages, examples };
}

// Lists what stops a page being fully readable from its source.
export function gapReport(pages) {
  const known = new Set(pages.map((p) => p.path));
  const gaps = [];
  for (const p of pages) {
    if (!p.ai_instructions) gaps.push([p.path, 'no ai_instructions']);
    if (!p.group) gaps.push([p.path, 'no group']);
    if (!p.status) gaps.push([p.path, 'no status']);
    if (p.dynamic.length) gaps.push([p.path, `generated content: ${p.dynamic.join('; ')}`]);
    for (const r of p.ai_related) {
      if (!known.has(r.path) && !fs.existsSync(path.join(sourceDir, r.path.replace(/\.html$/, '.html.erb'))) &&
          !fs.existsSync(path.join(sourceDir, r.path + '.erb')) && !fs.existsSync(path.join(sourceDir, r.path)))
        gaps.push([p.path, `ai_related target not found: ${r.path}`]);
    }
  }
  return gaps;
}

if (process.argv[1] === fileURLToPath(import.meta.url)) {
  const { pages, examples } = loadPages();
  const outIndex = process.argv.indexOf('--out');
  if (outIndex > 0) {
    const out = path.resolve(process.argv[outIndex + 1]);
    fs.mkdirSync(out, { recursive: true });
    for (const p of pages) {
      const name = p.path.replace(/^\//, '').replace(/\//g, '__').replace(/\.html$/, '.json');
      fs.writeFileSync(path.join(out, name), JSON.stringify(p, null, 2) + '\n');
    }
  }
  const gaps = gapReport(pages);
  console.log(`${pages.length} pages, ${Object.keys(examples).length} examples, ${gaps.length} gaps`);
  if (process.argv.includes('--gaps')) for (const [p, g] of gaps) console.log(`${p}: ${g}`);
}
