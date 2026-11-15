"""Validate edit timing or the current source, approval scope, and delivery evidence."""
import hashlib
import argparse
import json
import math
import sys
from pathlib import Path


def request_fingerprint(request):
    encoded = json.dumps(request, ensure_ascii=False, sort_keys=True, separators=(',', ':'), allow_nan=False)
    return hashlib.sha256(encoded.encode('utf8')).hexdigest()


def validate(p, base):
    errors = []
    base = Path(base)
    def check(ok, label):
        if not ok:
            errors.append(label)
    def exists(path):
        return isinstance(path, str) and bool(path) and (base/path).is_file()
    def number(value):
        return type(value) in (int, float) and math.isfinite(value)
    check(exists(p.get('video')), 'missing video')
    if p.get('captions_enabled', True) or p.get('srt'):
        check(exists(p.get('srt')), 'missing srt')
    duration = p.get('duration')
    if not number(duration) or duration <= 0:
        return errors+['invalid duration']
    if 'captions_enabled' in p:
        check(type(p['captions_enabled']) is bool, 'captions_enabled must be boolean')
    previous, ids = 0, set()
    scenes = p.get('scenes', [])
    check(isinstance(scenes, list) and bool(scenes), 'empty scenes')
    if not isinstance(scenes, list):
        return errors
    for scene in scenes:
        sid, start, end = scene['id'], scene['start'], scene['end']
        check(sid not in ids, 'duplicate scene '+sid)
        ids.add(sid)
        if not number(start) or not number(end):
            errors.append(sid+': invalid scene time');continue
        check(0 <= start < end <= duration, sid+': scene bounds')
        check(abs(start-previous) <= .05, sid+': gap/overlap')
        previous = end
        lids = set()
        for layer in scene.get('layers', []):
            label = sid+'/'+layer['id']
            check(layer['id'] not in lids, label+': duplicate layer');lids.add(layer['id'])
            a, b = layer['in'], layer['out']
            if not number(a) or not number(b):
                errors.append(label+': invalid layer time');continue
            check(start <= a < b <= end, label+': timing bounds')
            if 'cue_time' in layer:
                cue = layer['cue_time']
                if number(cue):
                    check(start <= cue <= end, label+': cue bounds')
                    check(abs(a-cue) <= .15 or bool(layer.get('timing_reason')), label+': early/late reveal')
                else:
                    errors.append(label+': invalid cue time')
            if 'speech_end' in layer:
                speech_end = layer['speech_end']
                if number(speech_end):
                    check(a <= speech_end <= b, label+': leaves before speech ends')
                else:
                    errors.append(label+': invalid speech end')
            if 'trigger' in layer:
                check(bool(layer['trigger']) and layer['trigger'] in scene.get('text', ''), label+': trigger absent')
            if 'asset' in layer:
                check(exists(layer['asset']), label+': missing asset')
            if 'source_in' in layer:
                si, so, sd, speed = (layer[k] for k in ('source_in', 'source_out', 'source_duration', 'speed'))
                if all(number(v) for v in (si, so, sd, speed)) and speed > 0:
                    check(0 <= si < so <= sd, label+': invalid source interval')
                    check(abs((so-si)/speed-(b-a)) <= .1, label+': speed mismatch')
                else:
                    errors.append(label+': invalid source interval')
    check(abs(previous-duration) <= .05, 'incomplete timeline')
    for lock in p.get('locked', []):
        if not exists(lock.get('path')):
            errors.append('missing locked file')
        else:
            with (base/lock['path']).open('rb') as stream:
                check(hashlib.file_digest(stream, 'sha256').hexdigest() == lock['sha256'], 'locked file changed')
    return errors


def validate_workflow(state, base, stage, expected_source=None, selected_scopes=None):
    """Check evidence relationships. The reviewer remains responsible for their truth."""
    if stage not in ('keyframes', 'render', 'deliver'):
        return ['invalid workflow stage']
    if selected_scopes is not None and stage != 'render':
        return ['--scope is available only for the render check']
    errors = []
    base = Path(base)
    hashes = {}

    def fail(message):
        errors.append(message)

    def file_record(record, label):
        if not isinstance(record, dict) or not record.get('path') or not record.get('sha256'):
            fail(label+': missing path or fingerprint')
            return None
        path = (base/record['path']).resolve()
        if not path.is_file():
            fail(label+': file missing')
            return None
        if path not in hashes:
            with path.open('rb') as stream:
                hashes[path] = hashlib.file_digest(stream, 'sha256').hexdigest()
        if hashes[path] != record['sha256']:
            fail(label+': file changed since recorded')
            return None
        return record['sha256']

    def evidence(check, label):
        status = check.get('status')
        if status == 'not_applicable':
            if not check.get('detail'):
                fail(label+': inapplicable without explanation')
        elif status != 'passed':
            fail(label+': '+str(status or 'not_run'))
        for key in ('method', 'coverage', 'detail'):
            if not check.get(key):
                fail(label+': missing '+key)
        records = check.get('evidence', [])
        if not records:
            fail(label+': evidence missing')
        bound = False
        for i, record in enumerate(records):
            valid = file_record(record, f'{label}/evidence-{i+1}')
            if valid and record.get('kind') == 'verification_report':
                report = json.loads((base/record['path']).read_text(encoding='utf-8-sig'))
                for key, value in [('source_sha256',source_hash),('output_sha256',output_hash),('request_sha256',request_hash)]:
                    if report.get(key) != value:
                        fail(label+': evidence subject mismatch for '+key)
                observed = report.get('checks', {}).get(label, {})
                for key in ('status','method','coverage'):
                    if observed.get(key) != check.get(key):
                        fail(label+': result does not match recorded evidence for '+key)
                bound = True
        if not bound:
            fail(label+': bound verification report missing')

    if state.get('workflow_version') != 1:
        fail('workflow state version missing')
    source = state.get('source', {})
    source_hash = file_record(source, 'source')
    duration = source.get('duration')
    valid_duration = type(duration) in (int, float) and math.isfinite(duration) and duration > 0
    if not valid_duration:
        fail('source: valid duration missing')
    if expected_source is not None:
        expected = (base/expected_source).resolve()
        actual = (base/source.get('path', '')).resolve()
        if actual != expected:
            fail('source: does not match current user input')
    request = state.get('request', {})
    request_hash = request_fingerprint(request)
    for key in ('id', 'user_text'):
        if not request.get(key):
            fail('request: missing '+key)
    if not source_hash or request.get('source_sha256') != source_hash:
        fail('request: source version mismatch')
    supporting_sources = request.get('supporting_sources', [])
    if not isinstance(supporting_sources, list):
        fail('request: supporting sources must be a list')
    else:
        for index, supporting in enumerate(supporting_sources, start=1):
            file_record(supporting, f'supporting source {index}')
    requirements = request.get('requirements', [])
    identifiers = set()
    if not requirements:
        fail('request: concrete requirements missing')
    for row in requirements:
        ident = row.get('id')
        if not ident or ident in identifiers:
            fail('request: missing or duplicate requirement ID')
        identifiers.add(ident)
        if not row.get('user_text') or not row.get('acceptance'):
            fail('request: requirement needs user instruction and acceptance criterion')
    if stage == 'keyframes':
        return errors

    approval_mode = request.get('approval_mode', 'keyframe_review')
    if approval_mode not in ('keyframe_review', 'directed_change', 'explicit_skip'):
        fail('request: invalid approval mode')
    scopes = request.get('visual_scopes', [])
    if not isinstance(scopes, list) or not scopes or len(set(scopes)) != len(scopes):
        fail('render: intended visual scopes missing or duplicated')
        scopes = []
    if selected_scopes is not None:
        unknown = [scope for scope in selected_scopes if scope not in scopes]
        if not selected_scopes or unknown or len(set(selected_scopes)) != len(selected_scopes):
            return errors + ['render: select distinct scopes from this request']
        scopes = selected_scopes
    for scope in scopes:
        ranges = request.get('visual_ranges', {}).get(scope, [])
        valid_ranges = valid_duration and isinstance(ranges,list) and bool(ranges)
        if valid_ranges:
            valid_ranges = all(isinstance(r,list) and len(r)==2 and
                               all(type(n) in (int,float) and math.isfinite(n) for n in r) and
                               0<=r[0]<r[1]<=duration for r in ranges)
        if not valid_ranges:
            fail(str(scope)+': valid timeline ranges missing')
        matching = [r for r in state.get('reviews', []) if r.get('scope') == scope]
        if len(matching) != 1:
            fail(str(scope)+': exactly one current review is required')
            continue
        review = matching[0]
        if review.get('source_sha256') != source_hash:
            fail(str(scope)+': keyframes belong to another source')
        if review.get('request_sha256') != request_hash:
            fail(str(scope)+': confirmation belongs to a different request')
        if not valid_ranges or review.get('ranges') != ranges:
            fail(str(scope)+': approved timeline range differs from requested range')
        if review.get('status') != 'approved':
            fail(str(scope)+': visual scope has not been approved')
        basis = review.get('basis', {})
        kind = basis.get('kind')
        quote = basis.get('user_text')
        if kind != approval_mode:
            fail(str(scope)+': approval does not match the current request mode')
        if not isinstance(quote, str) or not quote.strip():
            fail(str(scope)+': user confirmation or precise instruction missing')
        elif kind in ('directed_change', 'explicit_skip'):
            if quote.strip() not in request.get('user_text', ''):
                fail(str(scope)+': direct instruction must be quoted from the current request')
        elif kind == 'keyframe_review':
            positions = (request.get('message_index'), basis.get('preview_message_index'),
                         basis.get('confirmation_message_index'))
            if not all(type(i) is int and i > 0 for i in positions) or not positions[0] < positions[1] < positions[2]:
                fail(str(scope)+': need a delivered preview and a later user confirmation in this chat')
        frames = review.get('frames', [])
        if not frames and kind != 'explicit_skip':
            fail(str(scope)+': keyframe files missing')
        for i, record in enumerate(frames):
            file_record(record, f'{scope}/frame-{i+1}')
            at = record.get('at')
            if type(at) not in (int,float) or not math.isfinite(at) or not valid_ranges or not any(a <= at < b for a, b in ranges):
                fail(f'{scope}/frame-{i+1}: preview is outside its timeline range')
    if stage == 'render':
        return errors

    output_hash = file_record(state.get('output'), 'output')
    for i, attachment in enumerate(state.get('output', {}).get('attachments', [])):
        file_record(attachment, f'output/attachment-{i+1}')
    verification = state.get('verification', {})
    for key, expected in [('source_sha256', source_hash), ('output_sha256', output_hash), ('request_id', request.get('id')), ('request_sha256',request_hash)]:
        if not expected or verification.get(key) != expected:
            fail('verification: '+key+' mismatch')
    supplied = verification.get('requirements', [])
    for ident in identifiers:
        matching = [v for v in supplied if v.get('id') == ident]
        if len(matching) != 1:
            fail(str(ident)+': requirement result missing or duplicated')
        else:
            evidence(matching[0], str(ident))
            if matching[0].get('status') == 'not_applicable':
                fail(str(ident)+': a requested requirement cannot be silently skipped')
    for key in ('technical', 'visual', 'audio', 'playback'):
        check = verification.get(key, {})
        evidence(check, key)
        if check.get('status') == 'not_applicable' and not (key == 'audio' and source.get('has_audio') is False):
            fail(key+': this review is required for the current video')
        if key in ('visual', 'audio') and check.get('status') == 'passed':
            if check.get('coverage') != 'full':
                fail(key+': partial review cannot be recorded as full pass')
            if check.get('method') != 'continuous_'+key+'_review':
                fail(key+': automated analysis cannot replace continuous review')
        if key == 'playback' and check.get('status') == 'passed':
            if check.get('method') != 'user_entry_playback':
                fail('playback: launch or file existence does not verify playback')
    return errors


if __name__ == '__main__':
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument('path', type=Path)
        parser.add_argument('--stage', choices=['keyframes', 'render', 'deliver'])
        parser.add_argument('--expected-source')
        parser.add_argument('--scope', action='append', help='Check only this requested scope before a scoped render. Can be repeated.')
        args = parser.parse_args()
        path = args.path.resolve()
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if args.scope and args.stage != 'render':
            parser.error('--scope requires --stage render')
        errors = validate_workflow(data, path.parent, args.stage, args.expected_source, args.scope) if args.stage else validate(data, path.parent)
    except (IndexError, OSError, KeyError, ValueError, TypeError, AttributeError) as exc:
        errors = [str(exc)]
    print(json.dumps({'passed': not errors, 'errors': errors}, ensure_ascii=False))
    sys.exit(bool(errors))
