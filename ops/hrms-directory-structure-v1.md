# Meridian HCM — Directory Structure
## Version: 2.0 | Date: 2026-06-07 (restructured from flat root to domain-named dirs)

---

```
D:\HRMS\
│
├── .claude\                                    ← session memory (MEMORY.md + memory files)
│
├── backend\                                    ← backend repo (was v3_extracted\SME-HRMS-main\ before 2026-06-07)
│   ├── event_contract.py                       ← canonical event registry (155 entries — source of truth)
│   ├── [service files: *_service.py, etc.]
│   ├── services\
│   │   ├── employee-service\
│   │   ├── settings-service\
│   │   ├── auth-service\
│   │   └── hiring_service\
│   ├── attendance_service\
│   └── docs\
│       ├── canon\                              ← authoritative system definitions
│       │   ├── service-map.md                  ← 24-service inventory (authoritative)
│       │   ├── domain-model.md                 ← entity definitions
│       │   ├── data-architecture.md            ← DB schemas
│       │   ├── event-catalog.md                ← event registry (85+ events)
│       │   ├── workflow-catalog.md             ← 9 canonical workflows
│       │   ├── api-standards.md                ← routing rules (authoritative for /api/v1)
│       │   ├── decision-system.md
│       │   └── [other canon docs]
│       ├── system\                             ← session docs — load every session
│       │   ├── catalogue.md                    ← ENTRY POINT: session start checklist + doc map
│       │   ├── progress.md                     ← gap scoreboard (all phases)
│       │   ├── gap-register.md                 ← full gap detail (83 gaps + normalisation logs)
│       │   ├── pending.md                      ← current blocking items
│       │   └── [other system docs]
│       ├── services\                           ← per-service documentation (29 docs)
│       │   ├── employee-service.md
│       │   ├── leave-service.md
│       │   └── [27 more service docs]
│       └── specs\
│           ├── ui\                             ← UI spec docs per page
│           └── [other spec files]
│
├── frontend\
│   ├── pages\                                  ← 48 built Meridian HCM HTML pages
│   │   ├── h01-dashboard.html
│   │   └── [47 more h[N]-[page].html files]
│   └── seeds\                                  ← 13 archetype seed/reference pages — READ ONLY, never modify
│       ├── p1-dashboard.html
│       └── [12 more p[N]-[archetype].html files]
│
├── design\                                     ← UI design-layer docs (was docs\ at root before 2026-06-07)
│   ├── design-language.html                    ← Meridian design system (authoritative)
│   ├── hrms-doc-catalogue-v1.md                ← v1.6 — master doc catalogue (ground truth)
│   ├── hrms-archetype-system-v1.md             ← 13 archetypes + full page map
│   ├── hrms-contract-structure-v1.md           ← DSL format + isolation rules
│   ├── hrms-api-contracts.md                   ← all enums + service map (UI layer)
│   ├── hrms-claude-code-prompt-v1.md           ← Claude Code session prompt
│   └── [other design docs]
│
└── ops\                                        ← workspace ops (was loose root files before 2026-06-07)
    ├── tracker.md                              ← Session 9 OIG overlap register + action table
    ├── normalisation-tracker.md               ← Full-workspace normalisation pass (2026-06-08, 109 files)
    ├── build-progress.md                       ← build status + full session history
    ├── hrms-progress.md                        ← UI audit progress
    ├── hrms-audit-v1.py                        ← audit script
    ├── hrms-audit-manifest-v1.json             ← sealed hashes (104/104 clean)
    ├── pending.md                              ← workspace-level pending items
    ├── answers.md
    ├── HRMS PRODUCT SPEC.md
    └── hrms-directory-structure-v1.md          ← this file
```

---

## RULES

```
1. hrms-audit-v1.py and hrms-audit-manifest-v1.json sit in ops/.
   Run from ops/ or use: py -X utf8 ops/hrms-audit-v1.py
   The script resolves all paths relative to its own location.

2. frontend/seeds/ are READ ONLY.
   Never edit seed pages. They are design anchors.
   Claude Code reads them, never writes to them.

3. frontend/pages/ contains the 48 built HTML pages.
   One file per page. Named h[N]-[page].html.

4. backend/docs/ is the backend documentation root.
   backend/docs/system/catalogue.md is the entry point for every session.
   backend/docs/canon/ docs are authoritative — divergences resolve here.

5. design/ contains all UI design-layer docs.
   hrms-doc-catalogue-v1.md is the master catalogue (ground truth for what every file is).

6. ops/ contains workspace ops docs.
   tracker.md = Session 9 OIG log.
   normalisation-tracker.md = 2026-06-08 full-workspace normalisation pass.
```

---

## FIRST RUN ON NEW MACHINE

```
1. Copy D:\HRMS\ workspace to local drive
2. py -X utf8 ops\hrms-audit-v1.py --rebuild    ← normalises all paths to relative
3. py -X utf8 ops\hrms-audit-v1.py              ← verify clean (should be 104/104)
```
