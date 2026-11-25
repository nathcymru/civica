// Checks the guidance export and the MCP server answer real requests.
import test from 'node:test';
import assert from 'node:assert/strict';
import { spawn } from 'node:child_process';
import { loadPages } from '../scripts/guidance-export.mjs';

test('every example helper call is resolved to text', () => {
  const { pages } = loadPages();
  const clear = pages.find((p) => p.path === '/content/writing-guidelines/clear-language.html');
  assert.ok(clear, 'writing guideline page is exported');
  assert.ok(clear.examples.length > 0);
  assert.ok(!/<%/.test(clear.body), 'no ERB left in the body');
  assert.ok(clear.body.includes('> Example'));
});

test('MCP server lists tools and returns a page', async () => {
  const child = spawn('node', ['scripts/guidance-mcp.mjs'], { stdio: ['pipe', 'pipe', 'inherit'] });
  const lines = [];
  let waiting = null;
  let buffer = '';
  child.stdout.on('data', (d) => {
    buffer += d;
    let i;
    while ((i = buffer.indexOf('\n')) >= 0) {
      lines.push(JSON.parse(buffer.slice(0, i)));
      buffer = buffer.slice(i + 1);
      if (waiting) waiting();
    }
  });
  const call = (msg) => new Promise((resolve) => {
    waiting = () => { waiting = null; resolve(lines.shift()); };
    child.stdin.write(JSON.stringify(msg) + '\n');
  });
  const init = await call({ jsonrpc: '2.0', id: 1, method: 'initialize', params: {} });
  assert.equal(init.result.serverInfo.name, 'civica-guidance');
  const list = await call({ jsonrpc: '2.0', id: 2, method: 'tools/list' });
  assert.deepEqual(list.result.tools.map((t) => t.name).sort(),
    ['check_readiness', 'get_example', 'get_page', 'list_pages', 'lookup_term', 'search_guidance']);
  const page = await call({ jsonrpc: '2.0', id: 3, method: 'tools/call',
    params: { name: 'get_page', arguments: { path: '/styles/illustration-principles.html' } } });
  assert.match(page.result.content[0].text, /Six principles/);
  const term = await call({ jsonrpc: '2.0', id: 4, method: 'tools/call',
    params: { name: 'lookup_term', arguments: { term: 'Action' } } });
  assert.match(term.result.content[0].text, /household_wording/);
  child.kill();
});
