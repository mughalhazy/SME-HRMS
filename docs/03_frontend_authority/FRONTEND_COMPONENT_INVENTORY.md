# FRONTEND COMPONENT INVENTORY

Status: Complete
Created: 2026-06-17
Phase: 3 — Frontend Authority Capture
Source: archetype-system-v1.md (all archetypes), FRONTEND_SCREEN_CATALOG.md, FRONTEND_PERMISSION_MATRIX.md

---

## PURPOSE

Identifies every required UI component derived from the archetype system and the confirmed screen catalog. This is an authority inventory — not implementation code. Every component is justified by at least one archetype or screen requirement.

**Framework:** Next.js 15, App Router, TypeScript, Tailwind CSS, TanStack React Query.
**Component structure:** Use React Server Components (RSC) where possible; interactive components are Client Components (`"use client"`).

---

## SECTION 1: LAYOUT COMPONENTS

### L-001: AppShell

**Archetype:** All H01–H13
**Purpose:** Full-page frame with sidebar + topbar + content area
**Props:** `children`, `role` (for role-based sidebar variant)
**Contains:** Sidebar, Topbar, main content slot
**Notes:** Sidebar collapses at 768px breakpoint; localStorage tracks collapse state

---

### L-002: Sidebar

**Archetype:** All H01–H13
**Purpose:** Role-based navigation sidebar
**Props:** `role`, `collapsed`, `onToggle`, `activePath`
**Dimensions:** 54px collapsed / 216px expanded
**Contains:** SidebarSection (per nav group), SidebarItem (per nav link), collapse toggle button
**Behavior:** Renders only nav items the current role can access (see FRONTEND_NAVIGATION_MODEL.md)

---

### L-003: SidebarSection

**Purpose:** Grouped section heading in sidebar (e.g., "People & Org", "Analytics")
**Props:** `label`, `children`, `collapsed`
**Notes:** Label hidden when sidebar is collapsed; section still visible as icon group

---

### L-004: SidebarItem

**Purpose:** Individual navigation link
**Props:** `label`, `icon`, `href`, `active`, `badge?` (count badge)
**Notes:** Shows icon-only when sidebar collapsed; badge for pending counts (e.g., Approvals)

---

### L-005: Topbar

**Archetype:** All H01–H13
**Purpose:** Fixed top navigation bar
**Props:** `tenantName`, `user` (name, role, avatar)
**Contains:** Logo/tenant name, GlobalSearchTrigger, NotificationsBell, ApprovalsBadge (Admin/Manager), UserMenu
**Dimensions:** 52px height, full width

---

### L-006: UserMenu

**Purpose:** Topbar dropdown — profile, settings, logout
**Props:** `user`
**Items:** View Profile → `/employees/[own-id]`, Account Settings (chrome), Logout

---

### L-007: Breadcrumbs

**Archetype:** H02, H03, H04, H05, H07, H10, H11
**Purpose:** Page-level breadcrumb trail
**Props:** `items: {label, href?}[]`
**Notes:** All segments except the last are links; last segment is plain text

---

### L-008: PageHeader

**Purpose:** Standard page header with title, subtitle, breadcrumbs, and action slot
**Props:** `title`, `subtitle?`, `breadcrumbs?`, `actions?` (ReactNode slot for buttons)

---

## SECTION 2: DATA DISPLAY COMPONENTS

### D-001: DataTable

**Archetype:** H02 (all 11 list screens)
**Purpose:** Sortable, filterable, paginated table
**Props:** `columns`, `data`, `isLoading`, `pagination`, `onSort`, `onFilter`, `selectedRows?`, `onRowClick`
**Features:** Column sort (click header), row click navigation, bulk selection checkbox, empty state slot, loading skeleton, sticky header
**Notes:** JetBrains Mono for numeric columns (IDs, amounts, counts)

---

### D-002: TablePagination

**Purpose:** Pagination controls for DataTable
**Props:** `page`, `pageSize`, `total`, `onPageChange`, `onPageSizeChange`
**Options:** 10, 25, 50, 100 per page

---

### D-003: KPICard

**Archetype:** H01 (all 4 dashboards)
**Purpose:** Single metric display: label + value + optional trend
**Props:** `label`, `value`, `trend?` (`{direction: "up"|"down"|"neutral", percent, period}`), `icon?`, `linkTo?`
**Notes:** Value rendered in JetBrains Mono; trend shows colored arrow

---

### D-004: StatusBadge

**Archetype:** H02, H03, H05
**Purpose:** Colored status indicator
**Props:** `status`, `size?`
**Values and colors:**

| Status | Color |
|--------|-------|
| active | green |
| draft | grey |
| pending | yellow |
| approved | green |
| rejected | red |
| on_leave | blue |
| suspended | orange |
| terminated | red |
| processing | blue |
| disbursed | green |
| completed | green |
| failed | red |
| open | green (job posting) |
| closed | grey (job posting) |
| filled | blue (job posting) |

---

### D-005: EmployeeCard

**Archetype:** H01 dashboard "Recent Employees" widget
**Purpose:** Compact employee summary card
**Props:** `employee` (name, id, role, dept, avatar)
**Actions:** Click → navigate to `/employees/[id]`

---

### D-006: CandidateCard

**Archetype:** H13
**Purpose:** Kanban card for candidate pipeline
**Props:** `candidate` (name, posting, days in stage, stage), `isDragging`
**Actions:** Click → open candidate detail slide-over; drag → advance stage

---

### D-007: NotificationItem

**Archetype:** H09
**Purpose:** Single notification in inbox
**Props:** `notification` (type, title, body, timestamp, read), `onMarkRead`, `onStar`, `onArchive`
**Notes:** Unread items have bold title + accent dot

---

### D-008: ApprovalCard

**Archetype:** H05
**Purpose:** Pending approval item in the left list panel of approval inbox
**Props:** `workflow` (type, employee, description, created_at, priority), `active`
**Actions:** Click → load detail in right panel

---

### D-009: DecisionCard

**Purpose:** AI-generated decision card
**Props:** `decision` (trigger, impact, confidence, recommended_action, severity, expires_at, source_domain), `onResolve?`
**Severity colors:** critical=red, notify=yellow, passive=grey
**Notes:** In-memory source — expired cards must show expiry indicator

---

### D-010: TimelineEntry

**Archetype:** H06 (attendance timeline)
**Purpose:** Single row in Gantt-style attendance timeline
**Props:** `employee`, `entries: {start, end, status}[]`, `dateRange`

---

### D-011: CalendarEventBlock

**Archetype:** H06 (leave calendar)
**Purpose:** Leave event block on monthly calendar
**Props:** `event` (employee, type, start, end, status), `color`
**Actions:** Click → open leave request detail

---

### D-012: ChartWidget

**Archetype:** H01, H07
**Purpose:** Chart wrapper for dashboard analytics
**Props:** `type: "line"|"bar"|"pie"|"funnel"|"heatmap"`, `data`, `title`, `isLoading`, `error?`
**Notes:** Chart library TBD by implementer (Recharts, Nivo, Chart.js); this document specifies data requirements, not library

---

### D-013: WorkflowStepIndicator

**Archetype:** H04 multi-step forms
**Purpose:** Step progress indicator for multi-step forms
**Props:** `steps: {label, status: "completed"|"active"|"upcoming"}[]`, `currentStep`

---

### D-014: EntityDetailTab

**Archetype:** H03 (Employee Profile tabs)
**Purpose:** Tab navigation for detail screens
**Props:** `tabs: {label, key, count?}[]`, `activeTab`, `onTabChange`

---

### D-015: SplitView

**Archetype:** H05 (Approval Inbox)
**Purpose:** 340px fixed list panel + flex detail panel layout
**Props:** `listPanel: ReactNode`, `detailPanel: ReactNode`, `emptyDetail: ReactNode`
**Notes:** On mobile: full-width list; detail opens as sheet/modal

---

### D-016: KanbanBoard

**Archetype:** H13
**Purpose:** Multi-column drag-and-drop kanban
**Props:** `columns: {id, label, items}[]`, `onDrop` (drag handler), `onCardClick`
**Notes:** Use react-beautiful-dnd or dnd-kit. Column headers show stage name + item count.

---

### D-017: AuditLogRow

**Purpose:** Expandable row in audit log table
**Props:** `record` (user, action, entity, entity_id, before, after, timestamp), `expanded`, `onToggle`
**Notes:** Expanded state shows before/after JSON diff; AuditRecord is PROHIBITED from modification — no edit/delete controls

---

## SECTION 3: FORM COMPONENTS

### F-001: FormField

**Purpose:** Wrapper for all form inputs — label, input, error message, help text
**Props:** `label`, `required`, `error?`, `helpText?`, `children`

---

### F-002: TextInput

**Props:** `value`, `onChange`, `placeholder?`, `disabled?`, `error?`, `type?: "text"|"email"|"tel"|"number"`
**Notes:** JetBrains Mono for numeric ID fields

---

### F-003: DatePicker

**Archetype:** H04 (leave, hire date, etc.)
**Props:** `value`, `onChange`, `minDate?`, `maxDate?`, `disabled?`, `placeholder?`
**Notes:** Must handle `YYYY-MM-DD` ISO format for API compatibility

---

### F-004: DateRangePicker

**Purpose:** Start + end date pair selection
**Props:** `startDate`, `endDate`, `onChange`, `minDate?`, `maxDate?`
**Notes:** Used in leave request form, reporting filters

---

### F-005: Select

**Props:** `value`, `onChange`, `options: {value, label}[]`, `placeholder?`, `disabled?`, `searchable?`
**Notes:** Searchable variant for employee/role/dept dropdowns with large option sets

---

### F-006: MultiSelect

**Purpose:** Multiple option selection (e.g., permission set in role creation)
**Props:** `value: string[]`, `onChange`, `options: {value, label}[]`

---

### F-007: TextArea

**Props:** `value`, `onChange`, `rows?`, `placeholder?`, `maxLength?`
**Notes:** Used for rejection reasons, leave reasons, notes

---

### F-008: NumberInput

**Props:** `value`, `onChange`, `min?`, `max?`, `step?`, `prefix?` (currency symbol), `suffix?`
**Notes:** JetBrains Mono font; used for salary, leave days, etc.

---

### F-009: Toggle / Switch

**Props:** `checked`, `onChange`, `label?`, `disabled?`
**Notes:** Used for automation enable/disable, setting toggles

---

### F-010: SearchInput

**Archetype:** H02, H08
**Props:** `value`, `onChange`, `placeholder?`, `onClear`
**Notes:** Debounced (300ms) before API call

---

### F-011: FilterBar

**Archetype:** H02 (all list screens)
**Purpose:** Horizontal filter controls above tables
**Props:** `filters: FilterConfig[]` (type, options, value, onChange)
**Filter types:** Select, DateRange, MultiSelect, Toggle

---

### F-012: FileUpload

**Purpose:** File drag-and-drop or click upload
**Props:** `accept`, `maxSize`, `onUpload`, `value?`, `isLoading?`
**Notes:** Used in employee documents tab; may be deferred per screen implementation

---

### F-013: StepForm

**Archetype:** H04 (Add Employee, Create Job Posting)
**Purpose:** Multi-step form container with validation per step
**Props:** `steps: {label, component, validate}[]`, `onComplete`, `onStepChange`
**Contains:** WorkflowStepIndicator, step component slot, Next/Back navigation, Review summary

---

## SECTION 4: FEEDBACK AND STATE COMPONENTS

### S-001: SkeletonLoader

**Archetype:** All screens
**Purpose:** Loading placeholder matching content shape
**Variants:** `table` (rows), `card` (KPI shape), `list` (notification/approval list), `detail` (profile), `chart`

---

### S-002: EmptyState

**Archetype:** All screens
**Purpose:** No-data state with illustration, title, description, and optional CTA
**Props:** `title`, `description`, `cta?: {label, onClick|href}`

---

### S-003: ErrorState

**Archetype:** All screens
**Purpose:** API failure state with retry
**Props:** `title`, `description?`, `onRetry`, `compact?` (for widget-level errors)

---

### S-004: Toast / Notification

**Purpose:** Transient feedback after actions (save, approve, error)
**Variants:** success, error, warning, info
**Notes:** Auto-dismiss after 4s; persist error toasts until dismissed

---

### S-005: ConfirmDialog

**Purpose:** Confirmation modal for destructive actions (delete, reject, run payroll)
**Props:** `title`, `description`, `confirmLabel`, `cancelLabel`, `onConfirm`, `onCancel`, `variant?: "danger"|"warning"|"info"`

---

### S-006: LoadingSpinner

**Purpose:** Inline spinner for button-level loading states
**Props:** `size?: "sm"|"md"|"lg"`, `color?`

---

## SECTION 5: NAVIGATION COMPONENTS

### N-001: GlobalSearchTrigger

**Archetype:** H08 (from topbar)
**Purpose:** Search icon in topbar that opens search page or modal
**Actions:** Navigate to `/search`

---

### N-002: NotificationsBell

**Purpose:** Topbar notification icon with unread count badge
**Props:** `unreadCount`, `onClick`
**Notes:** Badge uses `GET /api/v1/notifications?unread=true&limit=1&count_only=true` on app init and periodic refresh

---

### N-003: ApprovalsBadge

**Purpose:** Topbar approvals pending count (Admin/Manager only)
**Props:** `pendingCount`, `onClick`
**Notes:** Links to `/approvals`

---

### N-004: RoleBadge

**Purpose:** Displays role chip (e.g., "Admin", "Manager") in topbar and user profile
**Props:** `role`
**Colors:** Admin=purple, Manager=blue, PayrollAdmin=teal, Recruiter=orange, Employee=grey

---

## SECTION 6: SPECIALIZED BUSINESS COMPONENTS

### B-001: LeaveBalanceBar

**Purpose:** Visual leave balance display: used days / total days per leave type
**Props:** `balances: {type, used, total}[]`
**Notes:** Color coding: green (plenty), yellow (low), red (exhausted)

---

### B-002: PayslipSummary

**Purpose:** Compact payslip card for employee dashboard
**Props:** `payslip` (period, gross, net, status)
**Notes:** JetBrains Mono for currency amounts

---

### B-003: AttendanceStatusDot

**Purpose:** Color-coded dot for attendance status in timeline and list
**Props:** `status: "present"|"late"|"absent"|"on_leave"`
**Colors:** present=green, late=yellow, absent=red, on_leave=blue

---

### B-004: CandidateStageActions

**Archetype:** H13
**Purpose:** Stage-specific action buttons in candidate detail slide-over
**Logic:** Shows "Schedule Interview" if in Screening, "Extend Offer" if in Interviewing, "Mark Hired" or "Reject" if at Offered

---

### B-005: PayrollRunProgress

**Purpose:** Step-by-step progress indicator for payroll run (validate → confirm → processing → complete)
**Props:** `status`, `warnings?: string[]`, `employeeCount?`

---

### B-006: WorkflowBuilder (Canvas)

**Archetype:** H11-01
**Purpose:** Drag-and-drop workflow designer canvas
**Props:** `definition`, `onChange`
**Notes:** Complex component — drag-and-drop step nodes, condition branches, approver assignment modals

---

### B-007: EnvelopeNormalizer

**Purpose:** Client-side utility (not a visible component) for normalizing non-standard API envelopes
**Handles:** `{status, data, service}` → normalized to `{status, data, meta: null}`
**Consumers:** All calls to compliance, decisions, banking, whatsapp APIs

---

## COMPONENT COUNT SUMMARY

| Category | Count |
|----------|-------|
| Layout | 8 |
| Data Display | 17 |
| Form | 13 |
| Feedback/State | 6 |
| Navigation | 4 |
| Specialized Business | 7 |
| **Total** | **55** |

All 55 components are justified by at least one archetype or screen requirement. No component is speculative.
