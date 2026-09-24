#!/usr/bin/env python3
from pathlib import Path
import re, sys, tomllib

ROOT = Path(__file__).resolve().parents[2]
CTX = ROOT / '.codex' / 'context'

REQUIRED = [
    'AGENTS.md', '.codex/README.md', '.codex/config.toml',
    '.codex/inheritance-manifest.toml', '.codex/context/index.md',
    '.codex/context/project-overview.md', '.codex/context/architecture.md',
    '.codex/context/policy-precedence.md', '.codex/context/repository-boundaries.md',
    '.codex/context/goal-driven-execution.md', '.codex/context/rtk-policy.md',
    '.codex/context/commands.md', '.codex/context/testing.md',
    '.codex/context/security.md', '.codex/context/finding-management.md',
    '.codex/context/dependency-and-supply-chain.md', '.codex/context/github-actions.md',
    '.codex/context/tool-provenance.md', '.codex/context/documentation.md',
    '.codex/context/evidence.md', '.codex/context/git-policy.md',
    '.codex/context/fork-and-upstream-policy.md', '.codex/context/delivery-and-ci.md',
    '.codex/context/feasibility.md', '.codex/context/cleanup.md',
    '.codex/context/definition-of-done.md', '.codex/context/read-only-policy.md',
    '.codex/context/governance-validation.md', '.codex/context/manifest.toml',
]

MARKERS = {
    'AGENTS.md': [
        'codex-control-plane-routing:mrts', 'Mandatory goal-driven execution',
        'read-only by default', 'current top-level user',
        'The current user must expressly authorize each material action class.',
        'worktree_create', 'Gitlink relationship', 'blocked_remote_mismatch',
        'origin', 'upstream',
    ],
    '.codex/context/policy-precedence.md': ['current explicit top-level user request', 'task-scoped', 'Gitlink'],
    '.codex/context/repository-boundaries.md': ['read-only by default', 'Framework may show `tools/MRTS (new commits)`', 'task-owned worktree', 'Gitlink'],
    '.codex/context/read-only-policy.md': ['declared default', 'current top-level user', 'does not imply permission'],
    '.codex/context/git-policy.md': ['origin/main', 'Never commit/push directly to `main`', 'blocked_remote_mismatch', 'verified_pr_remote_cleanup_deferred', 'Gitlink'],
    '.codex/context/fork-and-upstream-policy.md': ['Easton97-Jens/MRTS', 'git remote get-url --push origin', 'blocked_remote_mismatch', 'Never'],
    '.codex/context/delivery-and-ci.md': ['Draft PR', 'never a merge', 'verified_pr_remote_cleanup_deferred', 'Gitlink'],
    '.codex/context/cleanup.md': ['task-owned external worktree', 'worktree remove', 'git branch -d', 'remote_branch_retained_for_open_pr', 'push origin --delete'],
    '.codex/context/finding-management.md': ['FND-MRTS-', 'concrete evidence', 'legitimate control'],
}

def norm(s):
    return ' '.join(s.split()).lower()

def main():
    errors=[]
    for rel in REQUIRED:
        p=ROOT/rel
        if p.is_symlink() or not p.is_file():
            errors.append(f'missing regular file: {rel}')
            continue
        try: p.read_text(encoding='utf-8')
        except Exception as e: errors.append(f'utf8 read failed: {rel}: {e}')
    if errors:
        for e in errors: print('ERROR:',e)
        return 1
    for rel, markers in MARKERS.items():
        txt=norm((ROOT/rel).read_text(encoding='utf-8'))
        for m in markers:
            if norm(m) not in txt:
                errors.append(f'{rel} missing marker: {m}')
    cfg=(ROOT/'.codex/config.toml').read_text(encoding='utf-8')
    if not re.search(r'^\s*sandbox_mode\s*=\s*"workspace-write"\s*$',cfg,re.M):
        errors.append('config must keep sandbox_mode = "workspace-write" for repository governance compatibility')
    if '/root/git/ModSecurity-conector/.venv' in cfg:
        errors.append('config must not reuse Parent .venv')
    if '/var/tmp/codex/MRTS/venv' not in cfg:
        errors.append('config must define MRTS-owned external venv')
    with (ROOT/'.codex/inheritance-manifest.toml').open('rb') as f:
        inh=tomllib.load(f)
    if inh.get('repository') != 'mrts': errors.append('inheritance manifest repository must be mrts')
    ids={x.get('id') for x in inh.get('inherit',[]) if isinstance(x,dict)}
    for pid in ['PARENT-POLICY-PRECEDENCE','PARENT-TASK-WORKFLOW','PARENT-COMMAND-EXECUTION','PARENT-RESOURCES-AND-STORAGE','PARENT-SECURITY-POLICY','PARENT-PYTHON-POLICY','PARENT-TESTING-AND-EVIDENCE','PARENT-DEFINITION-OF-DONE']:
        if pid not in ids: errors.append(f'missing inherited owner: {pid}')
    if errors:
        for e in errors: print('ERROR:',e)
        return 1
    print('MRTS V3.2 structure: OK')
    return 0

if __name__=='__main__': raise SystemExit(main())
