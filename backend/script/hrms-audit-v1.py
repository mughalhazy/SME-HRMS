#!/usr/bin/env python3
"""
Meridian HCM — Audit Script v1
Windows / Mac / Linux portable.
All paths stored RELATIVE to script directory.

COMMANDS
────────
  python hrms-audit.py              full audit
  python hrms-audit.py --sync       seal after approved changes
  python hrms-audit.py --rebuild    convert any absolute paths to relative (run once on new machine)
  python hrms-audit.py --add <p>    register new file pair
  python hrms-audit.py --check <n>  single file status
  python hrms-audit.py --contracts  contract-layer checks
"""

import hashlib, json, os, re, sys
from datetime import datetime, timezone

# ── Paths ─────────────────────────────────────────────────────────────────────
BASE         = os.path.dirname(os.path.abspath(__file__))
MANIFEST     = os.path.join(BASE, 'hrms-audit-manifest-v1.json')
REPO_DIR     = os.path.join(BASE, '..', 'backend')
GAPS_FILE    = os.path.join(BASE, '..', 'design', 'hrms-ui-backend-gaps.md')
CONTRACTS_DIR = os.path.join(BASE, '..', 'contracts')

def abs_path(p):
    """Stored path (relative or legacy absolute) → absolute."""
    if p is None:
        return None
    if os.path.isabs(p):
        # Legacy absolute — try re-root by filename under BASE
        fname = os.path.basename(p)
        candidate = os.path.join(BASE, fname)
        if os.path.exists(candidate):
            return candidate
        return p
    return os.path.normpath(os.path.join(BASE, p))

def rel_path(p):
    """Absolute → relative from BASE for storage."""
    if p is None:
        return None
    try:
        rel = os.path.relpath(p, BASE)
        # On Windows relpath across drives raises ValueError — caught below
        return rel
    except ValueError:
        return p  # different drive — store as-is

# ── Helpers ───────────────────────────────────────────────────────────────────
def file_hash(path):
    with open(path, 'rb') as f:
        return hashlib.sha256(f.read()).hexdigest()

def file_stats(path):
    with open(path, 'rb') as f:
        content = f.read()
    return {
        'sha256': hashlib.sha256(content).hexdigest(),
        'size':   len(content),
        'lines':  content.count(b'\n'),
    }

def now_utc():
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

def load():
    if not os.path.exists(MANIFEST):
        print('❌  No manifest found. Use --add to start tracking files.')
        sys.exit(1)
    with open(MANIFEST, encoding='utf-8') as f:
        return json.load(f)

def save(manifest):
    with open(MANIFEST, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

# ── Audit ─────────────────────────────────────────────────────────────────────
def audit_all(manifest, verbose=False):
    results = []
    for name, rec in manifest.items():
        primary = abs_path(rec['primary'])
        mirror  = abs_path(rec.get('mirror'))
        sealed  = rec['sha256']
        row = {'name': name, 'primary': primary, 'mirror': mirror}

        if not os.path.exists(primary):
            row['status'] = 'missing_primary'
            results.append(row)
            continue

        ps = file_stats(primary)
        row.update({'primary_hash': ps['sha256'], 'primary_lines': ps['lines'],
                    'sealed_hash': sealed, 'sealed_lines': rec['lines']})
        primary_clean = (ps['sha256'] == sealed)

        if mirror and os.path.exists(mirror):
            ms = file_stats(mirror)
            row.update({'mirror_hash': ms['sha256'], 'mirror_lines': ms['lines']})
            mirror_ok = (ms['sha256'] == ps['sha256'])
        else:
            row.update({'mirror_hash': None, 'mirror_lines': None})
            mirror_ok = (mirror is None)

        if primary_clean and mirror_ok:      row['status'] = 'clean'
        elif not primary_clean and mirror_ok: row['status'] = 'primary_drifted'
        elif primary_clean and not mirror_ok: row['status'] = 'mirror_stale'
        else:                                 row['status'] = 'both_drifted'

        results.append(row)
    return results

def print_report(results):
    clean  = [r for r in results if r['status'] == 'clean']
    issues = [r for r in results if r['status'] != 'clean']
    total  = len(results)
    print()
    print('╔══════════════════════════════════════════════════════════════╗')
    print('║      Meridian HCM — AUDIT REPORT v1                         ║')
    print(f'║  {now_utc()}                                   ║')
    print('╚══════════════════════════════════════════════════════════════╝')
    print()
    if not issues:
        print(f'  ✅  ALL {total} FILES CLEAN')
        print()
        print('  Safe to proceed.')
    else:
        print(f'  📊  {len(clean)}/{total} clean  ·  {len(issues)} need attention')
        print()
        for r in issues:
            s = r['status']
            sym = '🔴' if 'drifted' in s else '🟡'
            print(f'  {sym}  {r["name"]}  [{s}]')
            if s == 'primary_drifted':
                delta = r['primary_lines'] - r['sealed_lines']
                print(f'      Primary changed: {r["sealed_hash"][:16]}… → {r["primary_hash"][:16]}…')
                print(f'      Lines: {r["sealed_lines"]} → {r["primary_lines"]} ({("+" if delta>=0 else "")}{delta})')
            elif s == 'mirror_stale':
                print(f'      Mirror out of sync. Run --sync to fix.')
            elif s == 'both_drifted':
                print(f'      Primary: {r["primary_hash"][:16]}…  sealed: {r["sealed_hash"][:16]}…')
                print(f'      🔴 Both drifted. Investigate before syncing.')
            elif s == 'missing_primary':
                print(f'      🔴 Primary not found: {r["primary"]}')
            print()
        print('  ──────────────────────────────────────────────────────────')
        print('  Approved: python hrms-audit.py --sync')
        print('  ──────────────────────────────────────────────────────────')
    print()

# ── Sync ──────────────────────────────────────────────────────────────────────
def sync(manifest):
    print()
    print('  Syncing mirrors and resealing...')
    print()
    updated = 0
    for name, rec in manifest.items():
        primary = abs_path(rec['primary'])
        mirror  = abs_path(rec.get('mirror'))
        if not os.path.exists(primary):
            print(f'  ❌  skipped (missing): {name}')
            continue
        stats   = file_stats(primary)
        changed = (stats['sha256'] != rec['sha256'])
        if mirror:
            mirror_stale = not os.path.exists(mirror) or (file_stats(mirror)['sha256'] != stats['sha256'])
            if mirror_stale:
                os.makedirs(os.path.dirname(mirror), exist_ok=True) if os.path.dirname(mirror) else None
                with open(primary, 'rb') as f: data = f.read()
                with open(mirror,  'wb') as f: f.write(data)
        if changed:
            delta = stats['lines'] - rec['lines']
            manifest[name].update({'sha256': stats['sha256'], 'size': stats['size'],
                                   'lines': stats['lines'], 'sealed': now_utc(),
                                   'prev_sha256': rec['sha256']})
            d = f'+{delta}' if delta >= 0 else str(delta)
            print(f'  🔒  resealed: {name} ({stats["lines"]} lines, {d})')
            updated += 1
        else:
            print(f'  ✅  clean:    {name}')
    save(manifest)
    print()
    print(f'  {updated} file(s) resealed.')
    print()

# ── Add ───────────────────────────────────────────────────────────────────────
def add_file(manifest, primary_path, mirror_path=None):
    primary_abs = os.path.abspath(primary_path)
    mirror_abs  = os.path.abspath(mirror_path) if mirror_path else None
    if not os.path.exists(primary_abs):
        print(f'❌  Not found: {primary_abs}')
        sys.exit(1)
    name = os.path.splitext(os.path.basename(primary_abs))[0]
    if name in manifest:
        print(f'⚠️   Already tracked: {name}')
        return
    stats = file_stats(primary_abs)
    manifest[name] = {
        'primary': rel_path(primary_abs),
        'mirror':  rel_path(mirror_abs),
        'sha256':  stats['sha256'],
        'size':    stats['size'],
        'lines':   stats['lines'],
        'sealed':  now_utc(),
    }
    save(manifest)
    print(f'✅  Added: {name}  ({stats["lines"]} lines, {stats["sha256"][:16]}…)')
    if mirror_abs:
        os.makedirs(os.path.dirname(mirror_abs), exist_ok=True) if os.path.dirname(mirror_abs) else None
        with open(primary_abs, 'rb') as f: data = f.read()
        with open(mirror_abs,  'wb') as f: f.write(data)
        print(f'    Mirror: {rel_path(mirror_abs)}')

# ── Rebuild ───────────────────────────────────────────────────────────────────
def rebuild_manifest(manifest):
    print()
    print(f'  Rebuilding manifest with relative paths...')
    print(f'  BASE: {BASE}')
    print()
    updated = skipped = 0
    for name, rec in manifest.items():
        p_abs = abs_path(rec['primary'])
        m_abs = abs_path(rec.get('mirror'))
        new_p = rel_path(p_abs) if p_abs else None
        new_m = rel_path(m_abs) if m_abs else None
        if os.path.exists(p_abs):
            stats = file_stats(p_abs)
            manifest[name].update({'primary': new_p, 'mirror': new_m,
                                   'sha256': stats['sha256'], 'size': stats['size'],
                                   'lines': stats['lines'], 'sealed': now_utc()})
            print(f'  ✅  {name}  →  {new_p}')
            updated += 1
        else:
            manifest[name]['primary'] = new_p
            manifest[name]['mirror']  = new_m
            print(f'  ⚠️   {name}  (missing primary — path updated)')
            skipped += 1
    save(manifest)
    print()
    print(f'  Rebuild complete. {updated} rehashed · {skipped} missing primaries.')
    print(f'  Run: python hrms-audit.py to verify.')
    print()

# ── Check one ─────────────────────────────────────────────────────────────────
def check_one(manifest, name):
    if name not in manifest:
        matches = [k for k in manifest if name.lower() in k.lower()]
        if matches:
            name = matches[0]
            print(f'  (matched: {name})')
        else:
            print(f'❌  Not tracked: {name}')
            return
    results = audit_all({name: manifest[name]})
    print_report(results)

# ── Contracts ─────────────────────────────────────────────────────────────────
def contract_checks():
    issues = []

    # 1. SCHEMA TEMPLATE EXISTS
    template = os.path.join(CONTRACTS_DIR, 'hrms-schema-template.json')
    if not os.path.exists(template):
        issues.append({'check': 'SCHEMA_TEMPLATE', 'severity': 'BLOCKER',
            'msg': 'contracts/hrms-schema-template.json does not exist — create before any page contracts.'})

    # 2. SCHEMA REFERENCE in page contracts
    if os.path.isdir(CONTRACTS_DIR):
        for fname in os.listdir(CONTRACTS_DIR):
            if fname.endswith('-contract.json'):
                fpath = os.path.join(CONTRACTS_DIR, fname)
                try:
                    data = json.load(open(fpath, encoding='utf-8'))
                    ref  = data.get('archetype_ref') or (data.get('_meta') or {}).get('archetype_ref')
                    if not ref:
                        issues.append({'check': 'SCHEMA_REFERENCE', 'severity': 'WARNING',
                            'msg': f'{fname}: missing "archetype_ref" field.'})
                    elif not os.path.exists(os.path.join(CONTRACTS_DIR, ref)):
                        issues.append({'check': 'SCHEMA_FILE_EXISTS', 'severity': 'BLOCKER',
                            'msg': f'{fname}: archetype_ref "{ref}" not found on disk.'})
                except Exception as e:
                    issues.append({'check': 'SCHEMA_REFERENCE', 'severity': 'ERROR', 'msg': f'{fname}: {e}'})

    # 3. GAP ID VALIDITY
    if os.path.exists(GAPS_FILE) and os.path.isdir(CONTRACTS_DIR):
        gaps_text  = open(GAPS_FILE, encoding='utf-8').read()
        known_gaps = set(re.findall(r'###\s+(BG-\d+|CG-\d+|DG-\d+|UG-\d+)', gaps_text))
        for fname in os.listdir(CONTRACTS_DIR):
            if fname.endswith('-contract.json'):
                text = open(os.path.join(CONTRACTS_DIR, fname), encoding='utf-8').read()
                for gap_id in set(re.findall(r'(BG-\d+|CG-\d+|DG-\d+|UG-\d+)', text)) - known_gaps:
                    issues.append({'check': 'GAP_ID_VALIDITY', 'severity': 'WARNING',
                        'msg': f'{fname}: {gap_id} not in gap register.'})

    # 4. CONTRACT VERSIONING
    if os.path.isdir(CONTRACTS_DIR):
        for fname in os.listdir(CONTRACTS_DIR):
            if fname.endswith('-contract.json'):
                try:
                    data = json.load(open(os.path.join(CONTRACTS_DIR, fname), encoding='utf-8'))
                    meta = data.get('_meta') or data
                    if not (meta.get('version') or data.get('version')):
                        issues.append({'check': 'CONTRACT_VERSIONING', 'severity': 'WARNING',
                            'msg': f'{fname}: missing "version" field.'})
                    if not (meta.get('last_updated') or data.get('last_updated')):
                        issues.append({'check': 'CONTRACT_VERSIONING', 'severity': 'WARNING',
                            'msg': f'{fname}: missing "last_updated" field.'})
                except Exception:
                    pass

    # 5. COLUMN WIDTH SUM
    if os.path.isdir(CONTRACTS_DIR):
        for fname in os.listdir(CONTRACTS_DIR):
            if fname.endswith('-contract.json'):
                try:
                    data = json.load(open(os.path.join(CONTRACTS_DIR, fname), encoding='utf-8'))
                    cols = (data.get('renderer_schema', {}).get('slots', {})
                                .get('DATA_TABLE', {}).get('columns', []))
                    if cols:
                        total = sum(c.get('width_pct', 0) for c in cols if isinstance(c, dict))
                        if total > 0 and not (99 <= total <= 101):
                            issues.append({'check': 'COLUMN_WIDTH_SUM', 'severity': 'WARNING',
                                'msg': f'{fname}: column width_pct sum = {total} (must be 99–101).'})
                except Exception:
                    pass

    return issues

def print_contract_report(issues):
    checks = ['SCHEMA_TEMPLATE', 'SCHEMA_REFERENCE', 'SCHEMA_FILE_EXISTS',
              'GAP_ID_VALIDITY', 'CONTRACT_VERSIONING', 'COLUMN_WIDTH_SUM']
    labels = {'SCHEMA_TEMPLATE':   '1. Schema Template Exists',
              'SCHEMA_REFERENCE':  '2. Schema Reference',
              'SCHEMA_FILE_EXISTS':'3. Schema File Exists',
              'GAP_ID_VALIDITY':   '4. Gap ID Validity',
              'CONTRACT_VERSIONING':'5. Contract Versioning',
              'COLUMN_WIDTH_SUM':  '6. Column Width Sum'}
    blockers_set = {'SCHEMA_TEMPLATE', 'SCHEMA_FILE_EXISTS'}
    issue_checks = {i['check'] for i in issues}
    print()
    print('╔══════════════════════════════════════════════════════════════╗')
    print('║      Meridian HCM — CONTRACT CHECKS v1                      ║')
    print(f'║  {now_utc()}                                   ║')
    print('╚══════════════════════════════════════════════════════════════╝')
    print()
    for c in checks:
        sym = '✅' if c not in issue_checks else ('🔴' if c in blockers_set else '⚠️ ')
        print(f'  {sym}  {labels.get(c, c)}')
    if issues:
        print()
        for i in issues:
            sym = '🔴' if i['severity'] == 'BLOCKER' else ('❌' if i['severity'] == 'ERROR' else '⚠️ ')
            print(f'  {sym}  [{i["check"]}] {i["msg"]}')
    else:
        print()
        print('  ✅  ALL CONTRACT CHECKS PASSED')
    print()
    blockers = [i for i in issues if i['severity'] == 'BLOCKER']
    if blockers:
        print('  🔴  BLOCKER(S) — fix before creating page contracts.')
        print()
    return len(blockers) > 0

# ── Entry ─────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    args = sys.argv[1:]

    if '--add' in args:
        idx  = args.index('--add')
        rest = args[idx+1:]
        if not rest:
            print('Usage: python hrms-audit.py --add <primary> [mirror]')
            sys.exit(1)
        m = load()
        add_file(m, rest[0], rest[1] if len(rest) > 1 else None)

    elif '--sync' in args:
        m = load()
        sync(m)

    elif '--rebuild' in args:
        m = load()
        rebuild_manifest(m)

    elif '--check' in args:
        idx  = args.index('--check')
        name = args[idx+1] if idx+1 < len(args) else None
        if not name:
            print('Usage: python hrms-audit.py --check <name>')
            sys.exit(1)
        m = load()
        check_one(m, name)

    elif '--contracts' in args:
        issues      = contract_checks()
        has_blocker = print_contract_report(issues)
        sys.exit(1 if has_blocker else 0)

    else:
        m       = load()
        results = audit_all(m, verbose='--report' in args)
        print_report(results)
        sys.exit(0 if not any(r['status'] != 'clean' for r in results) else 1)
