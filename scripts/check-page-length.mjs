// Fails when a Styles page is too long to read in one go.
// Prose words exclude front matter, ERB, code, tables and markup.
// Overview pages (nav_order 0 with sub-pages in the same group) have a lower limit.
import { readFileSync, readdirSync } from 'node:fs';

const dir = 'docs/source/styles';
const LIMIT = 900;
const OVERVIEW_LIMIT = 450;
// Palette pages are mostly reference lists of swatches, so they get more room.
const COLOUR_LIMIT = 1500;

const pages = readdirSync(dir).filter((f) => f.endsWith('.html.md.erb')).map((file) => {
  const raw = readFileSync(`${dir}/${file}`, 'utf8');
  const match = raw.match(/^---\n([\s\S]*?)\n---\n?([\s\S]*)$/);
  const front = match ? match[1] : '';
  const body = match ? match[2] : raw;
  const group = (front.match(/^group:\s*"?([^"\n]+)"?/m) || [])[1];
  const retired = /^status:\s*"?retired/m.test(front);
  const order = Number((front.match(/^nav_order:\s*(\d+)/m) || [])[1] ?? NaN);
  const prose = body
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/<%[\s\S]*?%>/g, ' ')
    .replace(/<svg[\s\S]*?<\/svg>/g, ' ')
    .replace(/<[^>]+>/g, ' ')
    .split('\n')
    .filter((line) => !line.trim().startsWith('|'))
    .join(' ')
    .replace(/\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/[#*_`>-]/g, ' ');
  const words = prose.split(/\s+/).filter((w) => /[A-Za-z0-9]/.test(w)).length;
  return { file, group, retired, order, words };
});

const failures = [];
for (const p of pages) {
  if (p.retired) continue;
  const siblings = pages.filter((o) => o.group === p.group && !o.retired).length;
  const overview = p.order === 0 && siblings > 1 && p.group !== 'Colour';
  const limit = p.group === 'Colour' ? COLOUR_LIMIT : overview ? OVERVIEW_LIMIT : LIMIT;
  if (p.words > limit) failures.push(`${p.file}: ${p.words} prose words, limit ${limit}`);
}
if (failures.length) {
  console.error('Pages too long:\n' + failures.join('\n'));
  process.exit(1);
}
console.log(`check-page-length: ${pages.length} Styles pages within limits`);
