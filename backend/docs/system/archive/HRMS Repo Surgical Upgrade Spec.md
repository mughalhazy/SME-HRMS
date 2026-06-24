> **SUPERSEDED** — This document is an archived draft. Canonical authority: `docs/system/MASTER BUILD SPEC.md`
> Do not edit. Retained for historical reference only.

TITLE:  
HRMS Repo Surgical Upgrade Spec — Target \= 100% in Every Area

SOURCE OF TRUTH:  
\- Existing repo docs/canon  
\- Pakistan HRMS benchmark from Manus report  
\- Current repo audit gaps already identified

GOAL:  
Do NOT “search and fix.”  
Do NOT redesign.  
Do NOT invent.  
Make the repo satisfy the exact acceptance criteria below.

\============================================================  
A. PAKISTAN-FOCUSED PRODUCT FIT — TARGET 100%  
CURRENT ≈ 78%  
\============================================================

100% MEANS:  
1\. Pakistan payroll rules are executable, tested, and used in runtime  
2\. FBR, EOBI, and PESSI/SESSI flows exist as real service paths  
3\. Province-aware compliance branching works at runtime  
4\. Bank/Raast disbursement path is runnable  
5\. Pakistan employee identifiers / statutory validation are enforced before payroll

REQUIRED REPO DELTAS:  
A1. Ensure a real runtime compliance orchestration path exists:  
    \- create/fix compliance\_service.py  
    \- compliance\_service must:  
      \-\> validate employee statutory completeness  
      \-\> call country adapter  
      \-\> produce FBR/EOBI/PESSI outputs  
      \-\> expose submission state transitions

A2. Ensure province-aware branching is runtime, not docs-only:  
    \- country/pakistan/compliance\_engine.py  
    \- support:  
      \-\> Punjab → PESSI  
      \-\> Sindh  → SESSI  
      \-\> KP     → extensible placeholder or rules module  
    \- province source must come from organization/legal entity/location data

A3. Ensure payroll precheck blocks invalid runs:  
    \- payroll\_service.py must refuse payroll finalization if:  
      \-\> CNIC missing/invalid  
      \-\> EOBI-required employee lacks required fields  
      \-\> province social security mapping missing  
      \-\> bank details missing for disbursement mode

A4. Make Pakistan banking path runnable:  
    \- fix bank\_service.py imports  
    \- implement minimal live path:  
      \-\> salary file generation  
      \-\> Raast payload generation  
      \-\> reconciliation stub with status values

A5. Add tests:  
    \- Pakistan tax calculation test  
    \- FBR output generation test  
    \- EOBI output generation test  
    \- province branching test  
    \- payroll block-on-invalid-statutory-data test

DONE WHEN:  
\- payroll \-\> compliance \-\> bank path runs without import failure  
\- Pakistan tests pass  
\- invalid statutory data blocks payroll

\============================================================  
B. CAPABILITY-DRIVEN PRODUCT DESIGN — TARGET 100%  
CURRENT ≈ 84%  
\============================================================

100% MEANS:  
1\. Every claimed capability exists either as:  
   \-\> real service/module  
   \-\> explicit non-core/add-on module  
2\. No fake services in docs  
3\. No orphan services in code  
4\. Service map, docs, and code match exactly

REQUIRED REPO DELTAS:  
B1. Normalize service inventory against canon:  
    REQUIRED CORE:  
    \- payroll-service  
    \- compliance-service  
    \- attendance-service  
    \- employee-service  
    \- bank-service  
    \- decision-service

    REQUIRED SUPPORT:  
    \- automation-service  
    \- whatsapp-service

    OPTIONAL / ADD-ON:  
    \- helpdesk-service  
    \- expense-service  
    \- ewa-financial-service

B2. For each service in docs/canon/service-map.md:  
    choose exactly one:  
    \- IMPLEMENTED  
    \- ADD-ON  
    \- NOT IN CURRENT RELEASE

B3. Remove doc drift:  
    \- if service is not implemented, mark it explicitly as:  
      "planned / add-on / future"  
    \- do not list it as live runtime service

B4. Make decision-service real:  
    \- create decision\_service.py if missing  
    \- it must NOT live inside payroll only  
    \- it must accept signals from payroll/attendance/compliance  
    \- output:  
      \-\> action  
      \-\> confidence  
      \-\> explanation  
      \-\> expires\_at  
      \-\> reversibility

B5. Make compliance-service real:  
    \- not docs-only  
    \- not alias-only  
    \- actual orchestration service file must exist

DONE WHEN:  
\- every documented service has a matching runtime state  
\- no “paper services” remain  
\- decision and compliance exist as real service units

\============================================================  
C. COUNTRY-AGNOSTIC ARCHITECTURE — TARGET 100%  
CURRENT ≈ 68%  
\============================================================

100% MEANS:  
1\. No service contains country-specific imports  
2\. No service contains "PK", "pakistan", or country rules  
3\. Resolver is config/data-driven  
4\. All statutory rules live only in country/{country}/  
5\. Adding a second country requires:  
   \-\> new adapter only  
   \-\> no service changes

REQUIRED REPO DELTAS:  
C1. Fix resolver completely:  
    \- core/country\_resolver.py  
    \- remove hardcoded org-country assumptions  
    \- resolver source must be:  
      \-\> config  
      or  
      \-\> org/legal\_entity metadata

C2. Enforce adapter-only country access:  
    \- services must call only:  
      adapter \= resolver.get\_adapter(org\_id)

C3. Remove all country leakage from services:  
    SEARCH AND ELIMINATE outside country/pakistan/:  
    \- "PK"  
    \- "pakistan"  
    \- direct imports from country.pakistan.\*  
    \- direct tax/compliance calculations

C4. Make country/base interfaces authoritative:  
    required interfaces:  
    \- tax engine  
    \- compliance engine  
    \- payroll rules

C5. Add a second dummy country to prove architecture:  
    \- country/dummy/  
      \-\> adapter.py  
      \-\> tax\_engine.py  
      \-\> compliance\_engine.py  
    \- minimal placeholder implementation  
    \- no service code changes allowed

C6. Add test:  
    \- resolver returns PK adapter for Pakistan org  
    \- resolver returns dummy adapter for dummy org  
    \- payroll\_service works with both without code change

DONE WHEN:  
\- grep of services shows no country-specific imports or literals  
\- second country adapter works without touching services

\============================================================  
D. CORE DEVELOPMENT MATURITY — TARGET 100%  
CURRENT ≈ 61%  
\============================================================

100% MEANS:  
1\. Top-level runtime paths import cleanly  
2\. Core services are executable  
3\. Tests pass  
4\. No broken references to non-existent packages  
5\. No half-refactored modules remain

REQUIRED REPO DELTAS:  
D1. Fix import integrity:  
    currently broken areas must be made import-clean:  
    \- payroll\_service.py  
    \- payroll\_api.py  
    \- compliance\_api.py  
    \- decision\_api.py  
    \- bank\_service.py  
    \- banking\_api.py  
    \- whatsapp\_service.py  
    \- whatsapp\_api.py

D2. Resolve missing package references:  
    if code imports:  
    \- services.\*  
    \- integrations.\*  
    then either:  
    \-\> create those packages properly  
    OR  
    \-\> rewrite imports to actual existing modules

D3. Remove alias-only anti-patterns:  
    examples:  
    \- service file that only re-exports another Pakistan-specific class  
    replace with actual orchestration module

D4. Make test collection pass first:  
    \- fix test\_payroll\_service.py import path  
    \- make pytest collect without crashing

D5. Add import-health smoke test:  
    \- tests/test\_import\_health.py  
    \- import all top-level service/api modules

DONE WHEN:  
\- top-level modules import without failure  
\- pytest runs and collects cleanly  
\- no missing package references remain

\============================================================  
E. DOCS ↔ CODE ↔ DEPLOYMENT ALIGNMENT — TARGET 100%  
CURRENT ≈ 49%  
\============================================================

100% MEANS:  
1\. docs/canon matches actual runtime services  
2\. docker-compose matches actual runnable services  
3\. README does not promise non-existent services  
4\. release scope is explicit

REQUIRED REPO DELTAS:  
E1. Reconcile docs/canon/service-map.md with actual code:  
    for every service, mark:  
    \- implemented  
    \- add-on  
    \- planned  
    \- deprecated

E2. Reconcile docker-compose.yml:  
    remove or disable services that do not exist  
    OR  
    implement the minimal service entrypoint

E3. Reconcile README:  
    do not claim runtime support for services that are only conceptual

E4. Add release manifest:  
    create docs/canon/release-scope.md  
    include:  
    \- core release services  
    \- add-ons  
    \- future services

DONE WHEN:  
\- docs, compose, and code all enumerate the same service reality

\============================================================  
F. RUNTIME INTEGRITY / IMPORT HEALTH — TARGET 100%  
CURRENT ≈ 42%  
\============================================================

100% MEANS:  
1\. zero module import failures in core runtime  
2\. all critical APIs can start  
3\. no missing internal dependencies

REQUIRED REPO DELTAS:  
F1. Fix all broken imports exactly, not heuristically  
F2. For each broken service, choose one:  
    \- repair dependency chain  
    \- create minimal dependency module  
    \- remove dead dependency and replace with local implementation

F3. For:  
    \- bank\_service.py  
    \- whatsapp\_service.py  
    \- payroll\_service.py  
    create the missing dependency chain explicitly

F4. Add startup smoke script:  
    \- script/import\_smoke.py  
    \- import all critical services/apis  
    \- exit nonzero on failure

DONE WHEN:  
\- import smoke passes  
\- all critical APIs start

\============================================================  
G. PRODUCTION READINESS — TARGET 100%  
CURRENT ≈ 38%  
\============================================================

100% MEANS:  
1\. end-to-end payroll run works  
2\. compliance validation and output works  
3\. bank disbursement output works  
4\. failure states are explicit  
5\. audit trail exists  
6\. no fake runtime dependencies

REQUIRED REPO DELTAS:  
G1. End-to-end happy path:  
    payroll \-\> compliance \-\> bank \-\> audit record

G2. End-to-end failure path:  
    statutory invalid \-\> payroll blocked \-\> reason returned

G3. Submission lifecycle:  
    DRAFT  
    VALIDATED  
    SUBMITTED  
    ACKNOWLEDGED  
    FAILED  
    RETRY

G4. Audit logging:  
    payroll run id  
    org id  
    country  
    compliance outputs generated  
    bank output generated  
    actor/system source  
    timestamp

G5. Minimal operational status enums for:  
    \- payroll run  
    \- compliance submission  
    \- bank disbursement  
    \- decision review

DONE WHEN:  
\- one scripted end-to-end scenario succeeds  
\- one invalid scenario fails correctly  
\- artifacts/statuses are recorded

\============================================================  
H. EXACT FILE-LEVEL SURGICAL TASKS  
\============================================================

1\. core/country\_resolver.py  
   \- remove hardcoded default behavior  
   \- make adapter resolution config/data-driven  
   \- add second-country proof path

2\. payroll\_service.py  
   \- fix imports  
   \- remove direct/missing service dependencies  
   \- orchestrate:  
     resolver \-\> adapter \-\> tax/compliance \-\> bank handoff  
   \- no country literals

3\. compliance\_service.py  
   \- create/fix as real orchestration service  
   \- no Pakistan-specific import leakage in service interface  
   \- use adapter internally through resolver

4\. decision\_service.py  
   \- create if missing  
   \- make standalone cross-domain service  
   \- minimal output schema required

5\. bank\_service.py  
   \- fix missing integrations imports  
   \- ensure runnable salary output \+ Raast output \+ reconciliation status stub

6\. whatsapp\_service.py  
   \- fix missing integration chain  
   \- provide minimal runnable service, even if capability is limited

7\. docs/canon/service-map.md  
   \- mark truthfully implemented vs add-on vs planned

8\. docker-compose.yml  
   \- remove dead services or wire actual existing entrypoints

9\. README.md  
   \- stop over-claiming runtime scope

10\. tests/  
   add:  
   \- test\_import\_health.py  
   \- test\_country\_resolver\_dual\_country.py  
   \- test\_pakistan\_compliance\_flow.py  
   \- test\_payroll\_block\_invalid\_statutory.py  
   \- test\_payroll\_to\_bank\_happy\_path.py

\============================================================  
I. NON-NEGOTIABLE ACCEPTANCE TESTS  
\============================================================

The repo is NOT at 100% until ALL of these pass:

T1. All top-level services and APIs import successfully  
T2. pytest collection succeeds  
T3. Pakistan payroll happy path succeeds  
T4. Invalid statutory data blocks payroll  
T5. Province-aware compliance branching works  
T6. Bank/Raast output path works  
T7. Services contain no country-specific imports/literals  
T8. Second country adapter can be added without service changes  
T9. docs/canon, compose, and code list the same live services  
T10. decision\_service exists and runs as cross-domain service

\============================================================  
J. CLAUDE EXECUTION INSTRUCTION  
\============================================================

Do NOT "search around the repo and fix things."  
Do NOT redesign.  
Do NOT add product surface area.

Apply ONLY the surgical deltas above.

For every section A–J:  
\- make the exact change  
\- prove completion with tests or direct artifact evidence

Output format required from Claude:  
1\. changed files  
2\. exact issue fixed per file  
3\. tests added/updated  
4\. acceptance criteria satisfied  
5\. remaining gaps, if any

END