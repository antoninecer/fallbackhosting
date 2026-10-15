"""Versioned repository catalog. No network, credentials or runtime operations."""
from datetime import datetime, timezone, timedelta
import json
from pathlib import Path
import re

TASK_STATUSES = {'BACKLOG', 'READY', 'IN_PROGRESS', 'TESTING', 'DONE', 'BLOCKED', 'BLOCKED_BY_OPERATOR'}
MILESTONE_STATUSES = {'PLANNED', 'IN_PROGRESS', 'NEEDS_TEST', 'BLOCKED', 'DONE'}
TRANSITIONS = {
    'BACKLOG': {'READY', 'BLOCKED'}, 'READY': {'IN_PROGRESS', 'BLOCKED'},
    'IN_PROGRESS': {'TESTING', 'BLOCKED'}, 'TESTING': {'DONE', 'IN_PROGRESS', 'BLOCKED'},
    'BLOCKED': {'READY'}, 'BLOCKED_BY_OPERATOR': {'READY'}, 'DONE': set(),
}

for _status in ('BACKLOG','READY','IN_PROGRESS','TESTING','BLOCKED'):
    TRANSITIONS[_status].add('BLOCKED_BY_OPERATOR')


def keys(value, expected):
    if not isinstance(value, dict) or set(value) != set(expected.split()):
        raise ValueError('Unexpected or missing catalog fields')


def timestamp(value):
    if not isinstance(value, str) or not re.fullmatch(r'\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ', value):
        raise ValueError('Expected explicit UTC timestamp')
    return datetime.strptime(value, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)


def text(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 8000:
        raise ValueError('Expected bounded nonempty text')
    if '\n' in value or '|' in value:
        raise ValueError('Catalog table text must be a single cell')


def reference(root, value):
    if not isinstance(value, str) or not re.fullmatch(r'(?:docs|checkpoints)/[A-Za-z0-9_.-]+\.md', value):
        raise ValueError('Invalid evidence reference')
    path = root / value
    if not path.is_file() or not path.resolve().is_relative_to(root.resolve()):
        raise ValueError('Missing or escaping evidence reference')


def evidence(root, values):
    if not isinstance(values, list) or len(values) != len(set(values)):
        raise ValueError('Expected unique evidence list')
    for value in values:
        reference(root, value)


def validate(catalog, root):
    root = Path(root)
    keys(catalog, 'schema_version milestones tasks incidents observations agent')
    if type(catalog['schema_version']) is not int or catalog['schema_version'] != 1:
        raise ValueError('Unsupported catalog version')
    all_ids = set()
    for group, pattern, statuses, extra in (
        ('milestones', r'M\d{2}', MILESTONE_STATUSES, ''),
        ('tasks', r'FH-\d{4}', TASK_STATUSES, 'milestone scope rollback history'),
    ):
        records = catalog[group]
        if not isinstance(records, list) or not records:
            raise ValueError('Missing catalog records')
        for item in records:
            keys(item, 'id title status owner acceptance dependencies evidence completed_at_utc completion_revision ' + extra)
            if not isinstance(item['id'], str) or not re.fullmatch(pattern, item['id']) or item['id'] in all_ids:
                raise ValueError('Invalid or duplicate ID')
            all_ids.add(item['id'])
            if item['status'] not in statuses:
                raise ValueError('Invalid status')
            for field in ('title', 'owner', 'acceptance') + (('scope', 'rollback') if group == 'tasks' else ()):
                text(item[field])
            deps = item['dependencies']
            if not isinstance(deps, list) or any(not isinstance(d, str) for d in deps) or len(deps) != len(set(deps)):
                raise ValueError('Invalid dependencies')
            evidence(root, item['evidence'])
            if item['status'] == 'DONE':
                timestamp(item['completed_at_utc'])
                if not item['evidence'] or not isinstance(item['completion_revision'], str) or not re.fullmatch(r'[a-f0-9]{40}', item['completion_revision']):
                    raise ValueError('DONE requires evidence, timestamp and full revision')
            elif item['completed_at_utc'] is not None or item['completion_revision'] is not None:
                raise ValueError('Unfinished item cannot claim completion')
            if group == 'tasks':
                if not isinstance(item['history'], list):
                    raise ValueError('Invalid task history')
                previous = None
                previous_time = None
                for step in item['history']:
                    keys(step, 'from to utc evidence')
                    when = timestamp(step['utc'])
                    if step['from'] not in TRANSITIONS or step['to'] not in TRANSITIONS[step['from']]:
                        raise ValueError('Invalid task transition')
                    if previous is not None and step['from'] != previous:
                        raise ValueError('Broken task history')
                    if previous_time is not None and when < previous_time:
                        raise ValueError('Unordered task history')
                    evidence(root, step['evidence'])
                    if not step['evidence']:
                        raise ValueError('Transition needs evidence')
                    previous, previous_time = step['to'], when
                if previous is not None and previous != item['status']:
                    raise ValueError('History/current status mismatch')
    milestones = {m['id'] for m in catalog['milestones']}
    tasks = {t['id'] for t in catalog['tasks']}
    graph = {}
    for item in catalog['milestones'] + catalog['tasks']:
        allowed = milestones if item['id'] in milestones else tasks
        if any(d not in allowed or d == item['id'] for d in item['dependencies']):
            raise ValueError('Missing, cross-type or self dependency')
        graph[item['id']] = item['dependencies']
        if item['id'] in tasks and item['milestone'] not in milestones:
            raise ValueError('Missing milestone')
    visited, active = set(), set()
    def visit(node):
        if node in active:
            raise ValueError('Dependency cycle')
        if node in visited:
            return
        active.add(node)
        for dep in graph[node]:
            visit(dep)
        active.remove(node)
        visited.add(node)
    for node in graph:
        visit(node)
    if not isinstance(catalog['incidents'], list):
        raise ValueError('Invalid incidents')
    for item in catalog['incidents']:
        keys(item, 'id utc severity component symptoms cause cause_provenance resolution status evidence')
        if not isinstance(item['id'], str) or not re.fullmatch(r'INC-\d{4}', item['id']) or item['id'] in all_ids:
            raise ValueError('Invalid incident ID')
        all_ids.add(item['id'])
        timestamp(item['utc'])
        if item['severity'] not in {'INFO', 'WARNING', 'CRITICAL'} or item['status'] not in {'OPEN', 'RESOLVED'} or item['cause_provenance'] not in {'UNKNOWN', 'SUSPECTED', 'VERIFIED'}:
            raise ValueError('Invalid incident classification')
        for field in ('component', 'symptoms', 'cause', 'resolution'):
            text(item[field])
        evidence(root, item['evidence'])
        if item['status'] == 'RESOLVED' and not item['evidence']:
            raise ValueError('Resolved incident needs evidence')
    if not isinstance(catalog['observations'], list):
        raise ValueError('Invalid observations')
    for item in catalog['observations']:
        keys(item, 'id component dependencies provenance status observed_at_utc expires_at_utc method evidence')
        if not isinstance(item['id'], str) or not re.fullmatch(r'OBS-\d{4}', item['id']) or item['id'] in all_ids:
            raise ValueError('Invalid observation ID')
        all_ids.add(item['id'])
        if item['provenance'] not in {'OBSERVED', 'HISTORICAL', 'PLANNED', 'UNKNOWN'} or item['status'] not in {'PASS', 'FAIL', 'UNKNOWN'}:
            raise ValueError('Invalid observation classification')
        for field in ('component', 'method'):
            text(item[field])
        evidence(root, item['evidence'])
        start, end = item['observed_at_utc'], item['expires_at_utc']
        if start is not None:
            timestamp(start)
        if end is not None and (start is None or timestamp(end) <= timestamp(start)):
            raise ValueError('Invalid observation expiry')
        if item['provenance'] == 'OBSERVED' and (start is None or not item['evidence']):
            raise ValueError('Observed health needs time and evidence')
        if item['status'] != 'UNKNOWN' and item['provenance'] not in {'OBSERVED', 'HISTORICAL'}:
            raise ValueError('Unobserved health cannot claim a result')
    observation_ids = {o['id'] for o in catalog['observations']}
    for item in catalog['observations']:
        deps = item['dependencies']
        if not isinstance(deps, list) or any(d not in observation_ids or d == item['id'] for d in deps) or len(set(deps)) != len(deps):
            raise ValueError('Invalid observation dependencies')
    graph.update({o['id']: o['dependencies'] for o in catalog['observations']})
    for node in observation_ids:
        visit(node)
    agent = catalog['agent']
    keys(agent, 'identity task_id heartbeat_utc session_ended checkpoint revision')
    text(agent['identity'])
    if agent['task_id'] not in tasks or type(agent['session_ended']) is not bool:
        raise ValueError('Invalid agent task/session')
    if agent['heartbeat_utc'] is not None:
        timestamp(agent['heartbeat_utc'])
    reference(root, agent['checkpoint'])
    if agent['revision'] is not None and not re.fullmatch(r'[a-f0-9]{40}', agent['revision']):
        raise ValueError('Invalid agent revision')
    return catalog


def load(root):
    def unique_pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError('Duplicate JSON key')
            result[key] = value
        return result
    data = json.loads((Path(root) / 'state/catalog.json').read_text(), object_pairs_hook=unique_pairs)
    return validate(data, root)


def observation_state(item, now):
    if item['provenance'] != 'OBSERVED' or item['observed_at_utc'] is None or item['expires_at_utc'] is None:
        return 'UNKNOWN'
    if timestamp(item['observed_at_utc']) > now:
        return 'UNKNOWN'
    if timestamp(item['expires_at_utc']) <= now:
        return 'STALE'
    return item['status']


def agent_state(agent, now, ttl_seconds=300):
    if agent['session_ended']:
        return 'STOPPED'
    if agent['heartbeat_utc'] is None:
        return 'UNKNOWN'
    age = now - timestamp(agent['heartbeat_utc'])
    if age < timedelta(0):
        return 'UNKNOWN'
    return 'RECENT' if age < timedelta(seconds=ttl_seconds) else 'STALE'


def table(catalog, group):
    if group == 'tasks':
        lines = ['| ID | Milestone | Status | Owner | Acceptance / next step |', '| --- | --- | --- | --- | --- |']
        lines += [f"| {t['id']} | {t['milestone']} | {t['status']} | {t['owner']} | {t['acceptance']} |" for t in catalog[group]]
    else:
        lines = ['| ID | Milestone | Current status | Gate for DONE |', '| --- | --- | --- | --- |']
        lines += [f"| {m['id']} | {m['title']} | {m['status']} | {m['acceptance']} |" for m in catalog[group]]
    return '\n'.join(lines)


def sync_markdown(root, catalog, write=False):
    for group, name in (('tasks', 'TASKS.md'), ('milestones', 'ROADMAP.md')):
        path = Path(root) / name
        body = path.read_text()
        start = body.index('| ID |')
        end = body.index('\n\n', start)
        # Refuse stray record rows outside the managed table as well.
        suffix = body[end:]
        if re.search(r'^\| (?:FH-\d{4}|M\d{2}) \|', suffix, re.MULTILINE):
            raise ValueError('Record outside canonical Markdown table')
        updated = body[:start] + table(catalog, group) + suffix
        if body != updated:
            if not write:
                raise ValueError(f'{name} differs from canonical catalog; run sync')
            pending = path.with_suffix('.md.tmp')
            pending.write_text(updated)
            pending.replace(path)


def validate_change(previous, current):
    """Compare committed baseline to stop status/history edits bypassing transitions."""
    old = {t['id']: t for t in previous['tasks']}
    new = {t['id']: t for t in current['tasks']}
    if not old.keys() <= new.keys():
        raise ValueError('Existing task IDs cannot disappear')
    if not {m['id'] for m in previous['milestones']} <= {m['id'] for m in current['milestones']}:
        raise ValueError('Existing milestone IDs cannot disappear')
    for task_id, before in old.items():
        after = new[task_id]
        prefix = before['history']
        if after['history'][:len(prefix)] != prefix:
            raise ValueError('Committed task history cannot be rewritten')
        added = after['history'][len(prefix):]
        if added:
            if added[0]['from'] != before['status']:
                raise ValueError('Transition must start at committed status')
        elif before['status'] != after['status']:
            raise ValueError('Status change requires new transition evidence')
        if before['status'] == 'DONE' and any(before[k] != after[k] for k in ('status', 'completed_at_utc', 'completion_revision', 'evidence')):
            raise ValueError('Committed completion evidence cannot be rewritten')
