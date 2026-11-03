"""Runs inside CTFd 3.7.7 using the instructor's namespaced pods/exec permission.

Only challenge content/progress is managed. Accounts, passwords, branding,
settings, and infrastructure are retained. Input travels over stdin, never argv.
"""
import json
import re
import sys


class DefinitionError(ValueError):
    pass


def validate(payload):
    if payload.get('mode') not in ('reset', 'update'):
        raise DefinitionError('Invalid operation')
    challenges = payload['challenges']
    if not isinstance(challenges, list) or not challenges:
        raise DefinitionError('Challenge definitions must be a nonempty list')
    names = [c['name'] for c in challenges]
    if any(not isinstance(n, str) or not n.strip() for n in names) or len(names) != len(set(names)):
        raise DefinitionError('Challenge names must be nonempty and unique')
    for c in challenges:
        if c.get('type', 'standard') != 'standard':
            raise DefinitionError('Only standard challenges are supported')
        if not isinstance(c['value'], int) or c['value'] < 0 or c.get('state', 'visible') not in ('visible', 'hidden'):
            raise DefinitionError('Invalid challenge points or state')
        if not isinstance(c['description'], str) or not isinstance(c['category'], str):
            raise DefinitionError('Invalid challenge description or category')
        if not c.get('flags'):
            raise DefinitionError('Every challenge requires a resolved flag')
        for f in c['flags']:
            value = f['content']
            if not isinstance(value, str) or not value.strip() or '{{' in value or value == 'CHANGEME':
                raise DefinitionError('Flag values must be resolved from the vault')
            if f.get('type', 'static') not in ('static', 'regex'):
                raise DefinitionError('Unsupported flag type')
            if f.get('type') == 'regex':
                try:
                    re.compile(value)
                except re.error:
                    raise DefinitionError('Invalid regular expression flag') from None
        for h in c.get('hints', []):
            if not isinstance(h['content'], str) or not isinstance(h['cost'], int) or h['cost'] < 0:
                raise DefinitionError('Invalid hint')
        if any(n not in names or n == c['name'] for n in c.get('prerequisites', [])):
            raise DefinitionError('Unknown or self-referencing prerequisite')
    graph = {c['name']: c.get('prerequisites', []) for c in challenges}
    visiting, visited = set(), set()
    def walk(name):
        if name in visiting:
            raise DefinitionError('Cyclic challenge prerequisites')
        if name in visited:
            return
        visiting.add(name)
        for child in graph[name]:
            walk(child)
        visiting.remove(name)
        visited.add(name)
    for name in graph:
        walk(name)


def synchronize(payload):
    validate(payload)  # Reject bad input before opening the application/database.
    from CTFd import create_app
    app = create_app()
    with app.app_context():
        from CTFd.models import db, Challenges, Flags, Hints, Unlocks, Submissions, Awards
        from CTFd.cache import cache
        existing = Challenges.query.all()
        names = [c.name for c in existing]
        if len(names) != len(set(names)):
            raise DefinitionError('Duplicate challenge names on the board')
        if any(c.type != 'standard' for c in existing):
            raise DefinitionError('Unsupported existing challenge type; ask the organizer')
        by_name = {c.name: c for c in existing}
        result = dict(changed=False, created=0, updated=0, reset_progress=False, check=payload.get('check', False))
        try:
            # Reset progress without deleting accounts, pages, uploads, or challenges.
            # Definitions absent from YAML are retained; hide them explicitly if needed.
            if payload['mode'] == 'reset':
                for model in (Submissions, Awards, Unlocks):
                    if model.query.count():
                        result['changed'] = result['reset_progress'] = True
                    if not payload.get('check'):
                        for row in model.query.all():
                            db.session.delete(row)
            for definition in payload['challenges']:
                challenge = by_name.get(definition['name'])
                created = challenge is None
                if created:
                    challenge = Challenges(name=definition['name'], type='standard')
                    db.session.add(challenge)
                    by_name[challenge.name] = challenge
                    result['created'] += 1
                dirty = created
                for field, value in {k: definition.get(k, default) for k, default in
                                     [('description', ''), ('category', ''), ('value', 0), ('state', 'visible')]}.items():
                    if getattr(challenge, field) != value:
                        setattr(challenge, field, value)
                        dirty = True
                db.session.flush()
                for model, key, fields, defaults in [
                    (Flags, 'flags', ('type', 'content', 'data'), {'type': 'static', 'data': ''}),
                    (Hints, 'hints', ('type', 'content', 'cost'), {'type': 'standard', 'cost': 0}),
                ]:
                    current = model.query.filter_by(challenge_id=challenge.id).order_by(model.id).all()
                    desired = [{field: wanted.get(field, defaults.get(field))
                                for field in fields} for wanted in definition.get(key, [])]
                    if model is Flags:
                        for wanted in desired:
                            wanted['data'] = wanted['data'] or ''
                    remaining = list(current)
                    matches = {}
                    # Match all unchanged rows first, preserving purchases when hints move.
                    for index, wanted in enumerate(desired):
                        for row in remaining:
                            actual = {field: (getattr(row, field) or '' if field == 'data'
                                              else getattr(row, field)) for field in fields}
                            if actual == wanted:
                                matches[index] = row
                                remaining.remove(row)
                                break
                    for index, wanted in enumerate(desired):
                        row = matches.get(index)
                        if row is None:
                            row = remaining.pop(0) if remaining else model(challenge_id=challenge.id)
                            if row.id is None:
                                db.session.add(row)
                            dirty = True
                        for field, value in wanted.items():
                            if getattr(row, field) != value:
                                setattr(row, field, value)
                                dirty = True
                    for row in remaining:
                        if model is Hints:
                            for unlock in Unlocks.query.filter_by(type='hints', target=row.id).all():
                                db.session.delete(unlock)
                        db.session.delete(row)
                        dirty = True
                if dirty and not created:
                    result['updated'] += 1
                result['changed'] |= dirty
            db.session.flush()
            for definition in payload['challenges']:
                challenge = by_name[definition['name']]
                ids = [by_name[n].id for n in definition.get('prerequisites', [])]
                requirements = {'prerequisites': ids} if ids else None
                if challenge.requirements != requirements:
                    challenge.requirements = requirements
                    result['changed'] = True
            if payload.get('check'):
                db.session.rollback()
            else:
                db.session.commit()
                if result['changed']:
                    cache.clear()
            return result
        except Exception:
            db.session.rollback()
            raise


def main():
    try:
        result = synchronize(json.load(sys.stdin))
        print('AIA_RESULT:' + json.dumps(result))
    except Exception as error:
        # Only our fixed validation messages are safe to report.
        message = str(error) if isinstance(error, DefinitionError) else 'Content operation failed; verify definitions and CTFd compatibility.'
        print('AIA_ERROR:' + message, file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
