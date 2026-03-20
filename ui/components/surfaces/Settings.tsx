'use client'

import type { ReactNode } from 'react'
import { Save, Settings2 } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Input, Select } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'

type SectionProps = {
  id: string
  title: string
  description: string
  children: ReactNode
}

const auditTimeline = [
  { label: 'Last updated', value: 'March 19, 2026 at 10:42 AM UTC' },
  { label: 'Updated by', value: 'Monica Reyes · HR Operations Lead' },
]

const connectedApps = [
  'Slack · workforce notifications active',
  'QuickBooks · payroll sync healthy',
  'Google Workspace · employee identity mapping live',
]

const surfaceClassName = 'rounded-[var(--radius-surface)] border border-[var(--border)] bg-[var(--surface)] shadow-none'
const sectionGridClassName = 'grid gap-6 xl:grid-cols-12'
const sectionIntroClassName = 'space-y-2 xl:col-span-4'
const sectionBodyClassName = 'space-y-6 xl:col-span-8'
const fieldGridClassName = 'grid gap-6 md:grid-cols-2'

function FieldLabel({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="space-y-2">
      <label className="block text-sm font-medium text-slate-900">{title}</label>
      {hint ? <p className="text-sm leading-6 text-slate-500">{hint}</p> : null}
    </div>
  )
}

function SettingsField({ title, hint, children }: { title: string; hint?: string; children: ReactNode }) {
  return (
    <div className="space-y-3">
      <FieldLabel title={title} hint={hint} />
      {children}
    </div>
  )
}

function ToggleRow({ title, description, defaultChecked = false }: { title: string; description: string; defaultChecked?: boolean }) {
  return (
    <div className="flex min-h-16 items-start justify-between gap-4 rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-subtle)] px-4 py-4">
      <div className="space-y-2 pr-4">
        <p className="text-sm font-medium text-slate-900">{title}</p>
        <p className="text-sm leading-6 text-slate-500">{description}</p>
      </div>
      <Switch aria-label={title} defaultChecked={defaultChecked} className="mt-0.5 shrink-0" />
    </div>
  )
}

function SettingsSection({ id, title, description, children }: SectionProps) {
  return (
    <section id={id} className={`${surfaceClassName} p-6`}>
      <div className={sectionGridClassName}>
        <div className={sectionIntroClassName}>
          <h2 className="text-lg font-semibold text-slate-950">{title}</h2>
          <p className="text-sm leading-6 text-slate-500">{description}</p>
        </div>
        <div className={sectionBodyClassName}>{children}</div>
      </div>
    </section>
  )
}

export function Settings() {
  return (
    <div className="mx-auto max-w-6xl space-y-6 text-slate-900">
      <section className={`${surfaceClassName} p-6`}>
        <div className="grid gap-6 xl:grid-cols-12 xl:items-start">
          <div className="space-y-4 xl:col-span-8">
            <div className="inline-flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
              <Settings2 className="h-3.5 w-3.5 text-blue-700" />
              System settings
            </div>
            <div className="space-y-2">
              <h1 className="text-3xl font-semibold tracking-tight text-slate-950">HRMS Settings</h1>
              <p className="max-w-3xl text-sm leading-6 text-slate-500">
                Configure company-wide HR defaults, keep system behavior controlled, and maintain a consistent setup for every team.
              </p>
            </div>
          </div>

          <div className="flex items-center justify-start gap-3 xl:col-span-4 xl:justify-end">
            <Button type="button" variant="ghost">
              Cancel
            </Button>
            <Button type="button">
              <Save className="h-4 w-4" />
              Save changes
            </Button>
          </div>
        </div>

        <Separator className="my-6" />

        <div className="grid gap-6 md:grid-cols-2">
          {auditTimeline.map((entry) => (
            <div key={entry.label} className="space-y-2">
              <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{entry.label}</p>
              <p className="text-sm font-medium text-slate-700">{entry.value}</p>
            </div>
          ))}
        </div>
      </section>

      <SettingsSection
        id="general-settings"
        title="General settings"
        description="Core system defaults used across attendance, payroll, leave, and workflow scheduling."
      >
        <div className={fieldGridClassName}>
          <SettingsField title="Organization name" hint="Displayed on employee records, policy documents, and payroll outputs.">
            <Input defaultValue="Northstar People Ops, Inc." placeholder="Organization name" />
          </SettingsField>
          <SettingsField title="Primary timezone" hint="Applies to reminders, approval timing, and attendance cutoffs.">
            <Select defaultValue="America/Los_Angeles">
              <option value="America/Los_Angeles">Pacific Time (UTC-08:00)</option>
              <option value="America/Denver">Mountain Time (UTC-07:00)</option>
              <option value="America/Chicago">Central Time (UTC-06:00)</option>
              <option value="America/New_York">Eastern Time (UTC-05:00)</option>
            </Select>
          </SettingsField>
        </div>

        <SettingsField title="Primary business address" hint="Used for official HR correspondence and default company profile details.">
          <Input defaultValue="1450 Market Street, Suite 800, San Francisco, CA 94103" placeholder="Business address" />
        </SettingsField>
      </SettingsSection>

      <SettingsSection
        id="organization-settings"
        title="Organization settings"
        description="Manage default operating rules for new hires, policies, and standard approval behavior."
      >
        <div className={fieldGridClassName}>
          <SettingsField title="Work week" hint="Sets the standard planning pattern for new employees and schedule templates.">
            <Select defaultValue="mon-fri">
              <option value="mon-fri">Monday to Friday</option>
              <option value="sun-thu">Sunday to Thursday</option>
              <option value="mon-sat">Monday to Saturday</option>
              <option value="custom">Custom schedule template</option>
            </Select>
          </SettingsField>
          <SettingsField title="Default leave policy" hint="Assigned during onboarding unless a department or entity override applies.">
            <Select defaultValue="standard-pto">
              <option value="standard-pto">Standard PTO · 18 days annually</option>
              <option value="flex-pto">Flexible PTO · manager approval</option>
              <option value="regional">Regional statutory leave pack</option>
            </Select>
          </SettingsField>
        </div>

        <div className="space-y-4">
          <ToggleRow
            title="Auto-assign policy templates"
            description="Apply selected defaults automatically when new departments or legal entities are created."
            defaultChecked
          />
          <ToggleRow
            title="Require dual approval for policy edits"
            description="Add a second reviewer for sensitive leave, attendance, and policy configuration changes."
            defaultChecked
          />
        </div>
      </SettingsSection>

      <SettingsSection
        id="notifications"
        title="Notifications"
        description="Control delivery preferences, reminders, and approval expectations without adding noise to the workflow."
      >
        <div className={fieldGridClassName}>
          <SettingsField title="Primary support inbox" hint="Default sender and reply channel for HR-related notifications.">
            <Input defaultValue="peopleops@northstarhr.com" />
          </SettingsField>
          <SettingsField title="Payroll approval SLA" hint="Expected turnaround time for payroll approvals before reminders escalate.">
            <Select defaultValue="24-hours">
              <option value="12-hours">12 hours</option>
              <option value="24-hours">24 hours</option>
              <option value="48-hours">48 hours</option>
            </Select>
          </SettingsField>
        </div>

        <div className="space-y-4">
          <ToggleRow
            title="Manager reminders"
            description="Send follow-up reminders for pending leave, attendance, and review approvals."
            defaultChecked
          />
          <ToggleRow
            title="Employee weekly digest"
            description="Share a weekly summary of policy updates, payroll notices, and time-off changes."
            defaultChecked
          />
        </div>
      </SettingsSection>

      <SettingsSection
        id="permissions-integrations"
        title="Permissions and integrations"
        description="Keep sensitive changes controlled and confirm the connected systems that support HR operations."
      >
        <div className="space-y-4">
          <ToggleRow
            title="Restrict settings edits to HR administrators"
            description="Limit configuration changes to designated administrators and approved operations leads."
            defaultChecked
          />
          <ToggleRow
            title="Require confirmation before publishing changes"
            description="Prompt administrators to review updates before configuration changes apply across the workspace."
            defaultChecked
          />
        </div>

        <div className="space-y-4 rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface-subtle)] p-4">
          <div className="space-y-2">
            <h3 className="text-sm font-semibold text-slate-950">Connected applications</h3>
            <p className="text-sm leading-6 text-slate-500">Critical integrations currently linked to notifications, payroll sync, and identity management.</p>
          </div>
          <div className="space-y-3">
            {connectedApps.map((app) => (
              <div key={app} className="rounded-[var(--radius-control)] border border-[var(--border)] bg-[var(--surface)] px-4 py-3 text-sm font-medium text-slate-700">
                {app}
              </div>
            ))}
          </div>
        </div>
      </SettingsSection>
    </div>
  )
}
