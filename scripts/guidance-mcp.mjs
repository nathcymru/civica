#!/usr/bin/env node
// Civica guidance MCP server (stdio). Serves the writing, illustration, colour,
// typography and other guidance pages, and their examples, to an LLM.
//
// Why hand-written JSON-RPC: the protocol surface needed here is four methods,
// and a dependency would add to the licence inventory this repository audits.
// Why read from docs/source on each start: the source is the single owner of
// the content, so there is no generated copy to drift.
//
// Run:  node scripts/guidance-mcp.mjs
// Add to an MCP client (for example .mcp.json):
//   { "mcpServers": { "civica-guidance": { "command": "node", "args": ["scripts/guidance-mcp.mjs"] } } }
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import readline from 'node:readline';
import { loadPages, gapReport } from './guidance-export.mjs';

const { pages, examples } = loadPages();
// The Technical A to Z page is built from this register, so it is served here
// as data: its Markdown file holds only the template.
const register = JSON.parse(fs.readFileSync(
  path.join(path.dirname(fileURLToPath(import.meta.url)), '..', 'docs', 'data', 'ha-terminology.json'), 'utf8'));
const byPath = new Map(pages.map((p) => [p.path, p]));
const summary = (p) => ({ path: p.path, title: p.title, section: p.section, group: p.group, description: p.description });

function findPage(input) {
  let p = String(input || '').trim().replace(/^https?:\/\/[^/]+(\/civica)?/, '');
  if (!p.startsWith('/')) p = '/' + p;
  p = p.replace(/#.*$/, '');
  if (byPath.has(p)) return byPath.get(p);
  if (byPath.has(p + '.html')) return byPath.get(p + '.html');
  if (byPath.has(p.replace(/\/$/, '') + '/index.html')) return byPath.get(p.replace(/\/$/, '') + '/index.html');
  return null;
}

function score(page, terms) {
  const hay = { title: (page.title || '').toLowerCase(), desc: (page.description || '').toLowerCase(), body: page.body.toLowerCase() };
  let s = 0;
  for (const t of terms) {
    if (hay.title.includes(t)) s += 10;
    if (hay.desc.includes(t)) s += 4;
    const n = hay.body.split(t).length - 1;
    s += Math.min(n, 10);
  }
  return s;
}

const tools = [
  {
    name: 'list_pages',
    description: 'List Civica guidance pages. Filter by section (for example "styles" or "content") and group (for example "Illustration" or "Writing guidelines").',
    inputSchema: { type: 'object', properties: { section: { type: 'string' }, group: { type: 'string' } } },
    run: ({ section, group }) => pages
      .filter((p) => (!section || p.section === section) && (!group || (p.group || '').toLowerCase() === group.toLowerCase()))
      .map(summary),
  },
  {
    name: 'get_page',
    description: 'Get one guidance page by path (for example "/content/writing-guidelines/clear-language.html"): front matter, the AI instructions for the page, related pages, and the full body with its examples written out as text.',
    inputSchema: { type: 'object', properties: { path: { type: 'string' } }, required: ['path'] },
    run: ({ path }) => {
      const p = findPage(path);
      if (!p) throw new Error(`No page at ${path}. Use list_pages or search_guidance.`);
      return p;
    },
  },
  {
    name: 'search_guidance',
    description: 'Search all guidance pages for words or a phrase. Returns the best matches with their path and title.',
    inputSchema: { type: 'object', properties: { query: { type: 'string' }, limit: { type: 'integer' } }, required: ['query'] },
    run: ({ query, limit = 8 }) => {
      const terms = String(query).toLowerCase().split(/\s+/).filter(Boolean);
      return pages.map((p) => ({ p, s: score(p, terms) })).filter((x) => x.s > 0)
        .sort((a, b) => b.s - a.s).slice(0, limit).map((x) => summary(x.p));
    },
  },
  {
    name: 'get_example',
    description: 'Get one example by id: title, description, visible text and the source HTML.',
    inputSchema: { type: 'object', properties: { id: { type: 'string' } }, required: ['id'] },
    run: ({ id }) => {
      const e = examples[id];
      if (!e) throw new Error(`No example "${id}".`);
      return e;
    },
  },
  {
    name: 'lookup_term',
    description: 'Look up a Home Assistant term in the Technical A to Z register: the exact native name, household wording, first-use explanation and what not to confuse it with. Matches names and aliases.',
    inputSchema: { type: 'object', properties: { term: { type: 'string' } }, required: ['term'] },
    run: ({ term }) => {
      const q = String(term).toLowerCase();
      const hits = register.terms.filter((t) => t.native_name.toLowerCase() === q ||
        (t.aliases || []).some((a) => a.toLowerCase() === q) || t.native_name.toLowerCase().includes(q));
      return hits.slice(0, 10).map(({ id, source_ids, reviewed_on, ...rest }) => rest);
    },
  },
  {
    name: 'check_readiness',
    description: 'List the gaps that stop pages being fully readable from their source (missing front matter, generated content). Optionally limit to one section.',
    inputSchema: { type: 'object', properties: { section: { type: 'string' } } },
    run: ({ section }) => gapReport(pages.filter((p) => !section || p.section === section)).map(([path, gap]) => ({ path, gap })),
  },
];

const send = (msg) => process.stdout.write(JSON.stringify(msg) + '\n');
const reply = (id, result) => send({ jsonrpc: '2.0', id, result });
const fail = (id, code, message) => send({ jsonrpc: '2.0', id, error: { code, message } });

function handle(req) {
  const { id, method, params } = req;
  if (id === undefined) return; // notifications need no reply
  if (method === 'initialize') {
    return reply(id, {
      protocolVersion: params?.protocolVersion || '2025-03-26',
      capabilities: { tools: {} },
      serverInfo: { name: 'civica-guidance', version: '1.0.0' },
      instructions: 'Civica guidance for Home Assistant: writing, illustration, colour, typography and structure. Start with search_guidance or list_pages, then get_page. Follow each page\'s ai_instructions.',
    });
  }
  if (method === 'ping') return reply(id, {});
  if (method === 'tools/list') {
    return reply(id, { tools: tools.map(({ name, description, inputSchema }) => ({ name, description, inputSchema })) });
  }
  if (method === 'tools/call') {
    const tool = tools.find((t) => t.name === params?.name);
    if (!tool) return fail(id, -32602, `Unknown tool ${params?.name}`);
    try {
      const out = tool.run(params.arguments || {});
      return reply(id, { content: [{ type: 'text', text: JSON.stringify(out, null, 2) }] });
    } catch (e) {
      return reply(id, { isError: true, content: [{ type: 'text', text: e.message }] });
    }
  }
  return fail(id, -32601, `Method not found: ${method}`);
}

readline.createInterface({ input: process.stdin }).on('line', (line) => {
  if (!line.trim()) return;
  let req;
  try { req = JSON.parse(line); } catch { return fail(null, -32700, 'Parse error'); }
  handle(req);
});
