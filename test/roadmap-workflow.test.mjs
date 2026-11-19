import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import YAML from 'yaml';

const workflow = YAML.parse(readFileSync('.github/workflows/validate.yml', 'utf8'));
const checks = workflow.jobs.checks;
const deploy = workflow.jobs.deploy;

test('roadmap refresh handles withdrawal and recovery without granting issue-write access', () => {
  for (const event of ['edited', 'labeled', 'unlabeled', 'closed', 'reopened', 'deleted', 'transferred']) {
    assert.ok(workflow.on.issues.types.includes(event), `${event} must refresh or remove public items`);
  }
  assert.ok(workflow.on.schedule.length && 'workflow_dispatch' in workflow.on);
  assert.equal(workflow.permissions.issues, 'read');
  assert.equal(workflow.permissions.contents, 'read');
  assert.equal(deploy.permissions.issues, 'read');
  assert.equal(deploy.permissions.contents, 'read');
  for (const label of ['accepted', 'in-works', 'completed']) {
    assert.match(deploy.if, new RegExp(`contains\\(github\\.event\\.issue\\.labels\\.\\*\\.name, 'roadmap: ${label}'\\)`));
    assert.match(deploy.if, new RegExp(`github\\.event\\.label\\.name == 'roadmap: ${label}'`));
  }
});

test('trusted refresh cannot interpolate issue text into shell or execute a PR build', () => {
  assert.match(deploy.if, /github\.ref == 'refs\/heads\/main' && github\.event_name != 'pull_request'/);
  const steps = deploy.steps;
  const refresh = steps.find(step => step.name === 'Refresh reviewed theme roadmap');
  assert.equal(refresh.run, 'npm run roadmap:fetch');
  assert.equal(refresh.env.GH_TOKEN, '${{ github.token }}');
  assert.ok(steps.indexOf(refresh) < steps.findIndex(step => step.run === 'npm run build'));
  for (const job of [checks, deploy]) {
    for (const step of job.steps) {
      if (step.run) assert.doesNotMatch(step.run, /\$\{\{[\s\S]*github\.event\.(issue|comment|label)/);
    }
  }
  const checkout = steps.find(step => step.uses?.startsWith('actions/checkout@'));
  assert.equal(checkout.with.ref, 'main');
  // Pull-request code never runs with Pages or token write access.
  assert.equal(checks.permissions, undefined);
  assert.doesNotMatch(checks.if, /issues/);
});

test('publication is serialised and a pending publication is never cancelled', () => {
  assert.equal(deploy.concurrency.group, 'github-pages');
  assert.equal(deploy.concurrency['cancel-in-progress'], false);
});

test('pull requests run every fast check and a browser smoke test; nightly runs the full suite', () => {
  const runs = checks.steps.map(step => step.run).filter(Boolean);
  assert.ok(runs.includes('npm run check'), 'npm run check must run on pull requests');
  const script = JSON.parse(readFileSync('package.json', 'utf8')).scripts.check.split(' && ');
  for (const command of ['npm test', 'npm run check:guidance', 'npm run check:coverage', 'npm run check:brand -- --check-built', 'npm run check:naming', 'npm run check:components', 'npm run check:colours', 'npm run check:content', 'python3 scripts/check-docs.py']) {
    assert.ok(script.includes(command), `${command} must be part of npm run check`);
  }
  const smoke = checks.steps.find(step => step.run === 'npm run test:browser:smoke');
  const full = checks.steps.find(step => step.run === 'npm run test:browser');
  assert.equal(smoke.if, "github.event_name == 'pull_request'");
  assert.equal(full.if, "github.event_name != 'pull_request'");
  assert.ok(workflow.on.schedule.length);
});
