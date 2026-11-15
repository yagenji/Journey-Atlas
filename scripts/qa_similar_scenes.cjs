#!/usr/bin/env node
/* Global recommendation contract QA. Uses the production selector itself, not
   a second implementation, and every Country/Region JSON in the repository. */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

const ROOT = path.resolve(__dirname, '..');
const read = rel => JSON.parse(fs.readFileSync(path.join(ROOT, rel), 'utf8'));
const index = read('data/top-scene-index.json');
const registry = read('data/atlas-destinations.json').destinations || [];
const regions = read('data/region-taxonomy.json').regions || [];

if (index.version < 7 || !index.heroLatitudes) {
  throw new Error('Build the current geography-enabled top-scene-index.json before recommendation QA');
}
const source = fs.readFileSync(path.join(ROOT, 'assets/js/similar-scenes.js'), 'utf8');
const instrumented = source.replace(
  /\}\)\(\);\s*$/,
  '  window.__qa = {ownScenes,buildPool,choose};\n})();'
);
if (instrumented === source) throw new Error('Selector is not accessible to QA');
const window = {addEventListener() {}};
vm.runInNewContext(instrumented, {window, document: {}, fetch() {
  throw new Error('Recommendation QA must not make network requests');
}}, {filename: 'similar-scenes.js'});
const {ownScenes, buildPool, choose} = window.__qa;
const isoRegions = new Map();
regions.forEach(region => (region.iso2 || []).forEach(iso => isoRegions.set(iso, region.id)));
const pool = buildPool(index, registry, isoRegions);
const published = new Set(registry.filter(row => row.atlasPublished && row.href).map(row => row.slug));
const family = slug => ({'hong-kong': 'china', macau: 'china'}[slug] || slug);
let checked = 0;
let nonempty = 0;
const distribution = {};
const failures = [];

function audit(page, origin) {
  const anchors = ownScenes(page, index);
  if (!anchors.some(item => item.types?.length)) return;
  const self = page.regionParent || family(page.slug);
  const picks = choose(anchors, pool, self);
  checked++;
  nonempty += Number(picks.length > 0);
  distribution[picks.length] = (distribution[picks.length] || 0) + 1;
  if (picks.length > 6) failures.push(origin + ': more than six suggestions');
  const seen = new Set([self]);
  for (const item of picks) {
    if (!item.href || !item.image || !item.types?.length) {
      failures.push(origin + ': incomplete suggestion ' + item.slug);
    }
    if (seen.has(item.family)) failures.push(origin + ': repeated or self family ' + item.family);
    seen.add(item.family);
    if (item.score < 4.25) failures.push(origin + ': below affinity threshold');
    if (!published.has(item.slug) && !item.place.parentSlug) {
      failures.push(origin + ': unpublished recommendation ' + item.slug);
    }
  }
  if (page.slug === 'antarctica' && picks.some(item =>
    item.types.some(type => ['beach', 'lagoon', 'reef', 'harbor'].includes(type)))) {
    failures.push('antarctica: unrelated warm-water/coastal suggestion');
  }
  if (picks.map(p => p.href).join('|') !==
      choose(anchors, pool, self).map(p => p.href).join('|')) {
    failures.push(origin + ': nondeterministic recommendations');
  }
}
for (const row of registry) {
  const file = path.join(ROOT, 'data/countries', row.slug + '.json');
  if (!fs.existsSync(file)) continue;
  audit(JSON.parse(fs.readFileSync(file, 'utf8')), 'country/' + row.slug);
}
const regionRoot = path.join(ROOT, 'data/regions');
for (const parent of fs.readdirSync(regionRoot)) {
  const dir = path.join(regionRoot, parent);
  if (!fs.statSync(dir).isDirectory()) continue;
  for (const file of fs.readdirSync(dir).filter(name => name.endsWith('.json'))) {
    const data = JSON.parse(fs.readFileSync(path.join(dir, file), 'utf8'));
    audit({...data, regionParent: data.parentSlug || parent}, 'region/' + parent + '/' + data.slug);
  }
}
if (!checked || !nonempty || !pool.length || failures.length) {
  console.error('Scenery recommendation QA FAIL:', {checked, nonempty, pool: pool.length, failures});
  process.exit(1);
}
console.log('Scenery recommendation QA PASS:', JSON.stringify({checked, nonempty, pool: pool.length, distribution}));
