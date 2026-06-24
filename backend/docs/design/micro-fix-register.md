MICRO FIX REGISTER — HRMS UI  
VERSION: V1  
STATUS: ACTIVE  

--------------------------------------------------
PURPOSE
--------------------------------------------------

Capture repeatable UI fixes and convert them into system rules.  
All future UI prompts, refinements, and QC passes must anchor to this file.  

If a fix exists here, it is considered a system rule — not a suggestion.

--------------------------------------------------
USAGE RULE
--------------------------------------------------

All UI prompts MUST include:

ANCHOR:
- docs/design/design-system-anchor.md
- docs/design/micro-fix-register.md

--------------------------------------------------
FIX-001 — NAV OVERFLOW + DROPDOWN
--------------------------------------------------

PROBLEM  
Tabs overflow causing truncation and loss of access  

ROOT CAUSE  
No overflow handling + no priority system  

FIX  
- Introduced "More" dropdown  
- Priority-based tab ordering  
- Dynamic overflow handling  
- Router-based dropdown navigation  

RULE  
No navigation item may disappear without accessible alternative  

APPLIES TO  
All top navigation systems  

--------------------------------------------------
FIX-002 — KPI CARD MISALIGNMENT
--------------------------------------------------

PROBLEM  
KPI cards misaligned and uneven height  

ROOT CAUSE  
Inconsistent layout structure + padding differences  

FIX  
- Grid system enforced  
- Equal height cards  
- Standardized padding  
- Flex column structure  

RULE  
All metric cards must maintain equal height and consistent spacing  

APPLIES TO  
All metric / dashboard components  

--------------------------------------------------
EXTENSION RULE
--------------------------------------------------

All new fixes must follow the same structure:

FIX-XXX  
PROBLEM  
ROOT CAUSE  
FIX  
RULE  
APPLIES TO  

Append only — never modify past fixes unless upgrading version.

--------------------------------------------------
QC
--------------------------------------------------

✔ file exists at correct path  
✔ formatting clean and readable  
✔ no duplication  
✔ anchors clearly defined  
✔ future fixes can be appended safely  

--------------------------------------------------
OUTPUT
--------------------------------------------------

- create or update file
- no extra commentary
- no additional files
