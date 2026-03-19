'use client'

import type { ComponentType } from 'react'
import { useMemo, useState } from 'react'
import { ArrowUpRight, BellRing, Building2, Clock3, CreditCard, Handshake, Palette, Save, Settings2, ShieldCheck, Upload, Workflow } from 'lucide-react'

import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input, Select } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { Switch } from '@/components/ui/switch'
import { cn } from '@/lib/utils'

type SettingsSection = {
  id: string
  label: string
  description: string
  icon: ComponentType<{ className?: string }>
}

const sidebarSections: SettingsSection[] = [
  {
    id: 'company-settings',
    label: 'Company Settings',
    description: 'Profile, branding, and operating defaults.',
    icon: Building2,
  },
  {
    id: 'roles-permissions',
    label: 'Roles & Permissions',
    description: 'Access rules and role templates.',
    icon: ShieldCheck,
  },
  {
    id: 'attendance-rules',
    label: 'Attendance Rules',
    description: 'Schedules, grace periods, and alerts.',
    icon: Clock3,
  },
  {
    id: 'leave-policies',
    label: 'Leave Policies',
    description: 'Time-off setup and accrual controls.',
    icon: Workflow,
  },
  {
    id: 'payroll-settings',
    label: 'Payroll Settings',
    description: 'Cycles, approvals, and deductions.',
    icon: CreditCard,
  },
  {
    id: 'notifications',
    label: 'Notifications',
    description: 'Channel preferences and reminders.',
    icon: BellRing,
  },
  {
    id: 'integrations',
    label: 'Integrations',
    description: 'Connected apps and sync health.',
    icon: Handshake,
  },
]

const auditTimeline = [
  { label: 'Last updated', value: 'March 19, 2026 at 10:42 AM UTC' },
  { label: 'Updated by', value: 'Monica Reyes · HR Operations Lead' },
]

const connectedApps = [
  'Slack · workforce notifications active',
  'QuickBooks · payroll sync healthy',
  'Google Workspace · employee identity mapping live',
]

function FieldLabel({ title, hint }: { title: string; hint?: string }) {
  return (
    <div className="space-y-1">
      <label className="text-sm font-medium text-slate-700">{title}</label>
      {hint ? <p className="text-xs leading-5 text-slate-500">{hint}</p> : null}
    </div>
  )
}

function SidebarCard({ activeSection, onSelect }: { activeSection: string; onSelect: (id: string) => void }) {
  return (
    <Card className="border-slate-200 bg-white shadow-sm">
      <CardHeader className="gap-2 border-b border-slate-100 pb-4">
        <CardTitle className="text-base text-slate-950">Settings</CardTitle>
        <CardDescription>Manage workspace configuration with a focused, light-theme control panel.</CardDescription>
      </CardHeader>
      <CardContent className="p-3">
        <nav aria-label="Settings sections" className="space-y-1.5">
          {sidebarSections.map((section) => {
            const Icon = section.icon
            const active = activeSection === section.id

            return (
              <button
                key={section.id}
                className={cn(
                  'flex w-full items-start gap-3 rounded-2xl border px-3.5 py-3 text-left transition-colors',
                  active ? 'border-blue-100 bg-blue-50' : 'border-transparent hover:border-slate-200 hover:bg-slate-50',
                )}
                type="button"
                onClick={() => onSelect(section.id)}
              >
                <span className={cn('mt-0.5 rounded-xl p-2', active ? 'bg-white text-blue-700' : 'bg-slate-100 text-slate-500')}>
                  <Icon className="h-4 w-4" />
                </span>
                <span className="min-w-0 space-y-1">
                  <span className="block text-sm font-semibold text-slate-900">{section.label}</span>
                  <span className="block text-xs leading-5 text-slate-500">{section.description}</span>
                </span>
              </button>
            )
          })}
        </nav>
      </CardContent>
    </Card>
  )
}

export function Settings() {
  const [activeSection, setActiveSection] = useState(sidebarSections[0]?.id ?? 'company-settings')

  const activeSectionMeta = useMemo(
    () => sidebarSections.find((section) => section.id === activeSection) ?? sidebarSections[0],
    [activeSection],
  )

  return (
    <div className="min-h-full bg-slate-50 text-slate-900">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <section className="flex flex-col gap-4 rounded-[28px] border border-slate-200 bg-white px-6 py-6 shadow-sm lg:flex-row lg:items-center lg:justify-between">
          <div className="space-y-2">
            <div className="inline-flex items-center gap-2 rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-blue-700">
              <Settings2 className="h-3.5 w-3.5" />
              Admin configuration
            </div>
            <div>
              <h2 className="text-3xl font-semibold tracking-tight text-slate-950">System Settings</h2>
              <p className="mt-1 max-w-2xl text-sm leading-6 text-slate-500">
                Review global HR configuration, keep policies aligned, and centralize operational defaults for every team.
              </p>
            </div>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <Button type="button" variant="outline">
              View change log
              <ArrowUpRight className="h-4 w-4" />
            </Button>
            <Button type="button">
              <Save className="h-4 w-4" />
              Save changes
            </Button>
          </div>
        </section>

        <section className="grid gap-6 xl:grid-cols-[280px_minmax(0,1fr)]">
          <div className="space-y-6 xl:sticky xl:top-6 xl:self-start">
            <SidebarCard activeSection={activeSection} onSelect={setActiveSection} />

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader className="gap-2 border-b border-slate-100 pb-4">
                <CardTitle className="text-base text-slate-950">Audit Info</CardTitle>
                <CardDescription>Track ownership and the last committed settings update.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-4">
                {auditTimeline.map((entry, index) => (
                  <div key={entry.label} className="space-y-2">
                    <div>
                      <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">{entry.label}</p>
                      <p className="mt-1 text-sm font-medium text-slate-700">{entry.value}</p>
                    </div>
                    {index < auditTimeline.length - 1 ? <Separator /> : null}
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>

          <div className="space-y-6">
            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader className="gap-2 border-b border-slate-100 pb-4">
                <div className="flex flex-col gap-3 lg:flex-row lg:items-start lg:justify-between">
                  <div>
                    <CardTitle className="text-xl text-slate-950">{activeSectionMeta.label}</CardTitle>
                    <CardDescription className="max-w-2xl">{activeSectionMeta.description} The primary panel below is configured for company-wide defaults and branding.</CardDescription>
                  </div>
                  <div className="rounded-2xl border border-slate-200 bg-slate-50 px-3 py-2 text-right">
                    <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Status</p>
                    <p className="mt-1 text-sm font-semibold text-slate-700">Draft changes not yet published</p>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-6 pt-5">
                <div className="grid gap-6 2xl:grid-cols-2">
                  <Card className="border-slate-200 bg-slate-50/70 shadow-none">
                    <CardHeader className="gap-1 pb-4">
                      <CardTitle className="text-base text-slate-950">Company Info</CardTitle>
                      <CardDescription>Foundational identity used across employee records, communications, and compliance outputs.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <FieldLabel title="Name" hint="Displayed on employee portals, payslips, and policy documents." />
                        <Input defaultValue="Northstar People Ops, Inc." placeholder="Company name" />
                      </div>
                      <div className="space-y-2">
                        <FieldLabel title="Address" hint="Primary office or legal entity address for HR correspondence." />
                        <Input defaultValue="1450 Market Street, Suite 800, San Francisco, CA 94103" placeholder="Company address" />
                      </div>
                      <div className="space-y-2">
                        <FieldLabel title="Timezone" hint="Used for attendance cutoffs, reminders, and automation schedules." />
                        <Select defaultValue="America/Los_Angeles">
                          <option value="America/Los_Angeles">Pacific Time (UTC-08:00)</option>
                          <option value="America/Denver">Mountain Time (UTC-07:00)</option>
                          <option value="America/Chicago">Central Time (UTC-06:00)</option>
                          <option value="America/New_York">Eastern Time (UTC-05:00)</option>
                        </Select>
                      </div>
                    </CardContent>
                  </Card>

                  <Card className="border-slate-200 bg-slate-50/70 shadow-none">
                    <CardHeader className="gap-1 pb-4">
                      <CardTitle className="text-base text-slate-950">HR Preferences</CardTitle>
                      <CardDescription>Default rules for work planning, leave assignment, and approval experience.</CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <div className="space-y-2">
                        <FieldLabel title="Work week" hint="Sets the expected working pattern for new employees and schedule templates." />
                        <Select defaultValue="mon-fri">
                          <option value="mon-fri">Monday to Friday</option>
                          <option value="sun-thu">Sunday to Thursday</option>
                          <option value="mon-sat">Monday to Saturday</option>
                          <option value="custom">Custom schedule template</option>
                        </Select>
                      </div>
                      <div className="space-y-2">
                        <FieldLabel title="Default leave policy" hint="Applied automatically during employee onboarding unless overridden." />
                        <Select defaultValue="standard-pto">
                          <option value="standard-pto">Standard PTO · 18 days annually</option>
                          <option value="flex-pto">Flexible PTO · manager approval</option>
                          <option value="regional">Regional statutory leave pack</option>
                        </Select>
                      </div>

                      <Separator />

                      <div className="space-y-3 rounded-2xl border border-slate-200 bg-white p-4">
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-slate-900">Auto-assign policy templates</p>
                            <p className="text-sm leading-6 text-slate-500">Apply the selected defaults when new departments or entities are created.</p>
                          </div>
                          <Switch defaultChecked aria-label="Toggle automatic policy assignment" />
                        </div>
                        <div className="flex items-start justify-between gap-3">
                          <div>
                            <p className="text-sm font-semibold text-slate-900">Require HR review for overrides</p>
                            <p className="text-sm leading-6 text-slate-500">Escalate manual changes to work week or leave defaults before publishing.</p>
                          </div>
                          <Switch defaultChecked aria-label="Toggle HR review for overrides" />
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>

                <Card className="border-slate-200 bg-slate-50/70 shadow-none">
                  <CardHeader className="gap-1 pb-4">
                    <div className="flex items-start gap-3">
                      <span className="rounded-2xl bg-white p-2 text-blue-700 shadow-sm">
                        <Palette className="h-4 w-4" />
                      </span>
                      <div>
                        <CardTitle className="text-base text-slate-950">Branding</CardTitle>
                        <CardDescription>Maintain brand consistency in internal portals, email templates, and exported HR documents.</CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="grid gap-6 lg:grid-cols-[minmax(0,1fr)_320px]">
                      <div className="space-y-4">
                        <div className="space-y-2">
                          <FieldLabel title="Logo upload" hint="Recommended size: 512×512 PNG with transparent background." />
                          <div className="flex flex-col gap-3 rounded-2xl border border-dashed border-slate-300 bg-white p-4 sm:flex-row sm:items-center sm:justify-between">
                            <div>
                              <p className="text-sm font-semibold text-slate-900">northstar-mark.png</p>
                              <p className="text-sm leading-6 text-slate-500">Current logo is used on the employee portal, payslips, and policy PDFs.</p>
                            </div>
                            <Button type="button" variant="outline">
                              <Upload className="h-4 w-4" />
                              Upload new logo
                            </Button>
                          </div>
                        </div>
                        <div className="space-y-2">
                          <FieldLabel title="Primary color" hint="Sets the accent color for buttons, highlights, and navigational emphasis." />
                          <div className="flex flex-col gap-3 sm:flex-row sm:items-center">
                            <Input aria-label="Primary brand color" className="h-11 w-full sm:w-32" defaultValue="#2347AA" type="color" />
                            <Input className="sm:max-w-xs" defaultValue="#2347AA" placeholder="#2347AA" />
                          </div>
                        </div>
                      </div>

                      <div className="rounded-[24px] border border-slate-200 bg-white p-4 shadow-sm">
                        <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-400">Preview</p>
                        <div className="mt-4 space-y-4 rounded-[20px] border border-slate-200 bg-slate-50 p-4">
                          <div className="flex items-center gap-3">
                            <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-[#2347AA] text-sm font-semibold text-white">NP</div>
                            <div>
                              <p className="text-sm font-semibold text-slate-900">Northstar People Ops</p>
                              <p className="text-xs text-slate-500">Brand appearance on employee touchpoints</p>
                            </div>
                          </div>
                          <Button className="w-full justify-center" type="button">
                            Preview primary action
                          </Button>
                          <div className="rounded-2xl bg-blue-50 p-3 text-sm text-blue-900">Announcements, onboarding workflows, and self-service prompts inherit this accent palette.</div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </CardContent>
            </Card>

            <Card className="border-slate-200 bg-white shadow-sm">
              <CardHeader className="gap-2 border-b border-slate-100 pb-4">
                <CardTitle className="text-base text-slate-950">Integrations snapshot</CardTitle>
                <CardDescription>Quick glance at connected platforms impacted by settings changes.</CardDescription>
              </CardHeader>
              <CardContent className="space-y-3 pt-5">
                {connectedApps.map((app) => (
                  <div key={app} className="flex items-center justify-between gap-3 rounded-2xl border border-slate-200 bg-slate-50 px-4 py-3">
                    <p className="text-sm font-medium text-slate-700">{app}</p>
                    <Button size="sm" type="button" variant="ghost">
                      Inspect
                    </Button>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </section>

        <div className="sticky bottom-4 z-20">
          <div className="flex flex-col gap-3 rounded-[24px] border border-slate-200 bg-white/95 px-5 py-4 shadow-lg backdrop-blur md:flex-row md:items-center md:justify-between">
            <div>
              <p className="text-sm font-semibold text-slate-900">You have unsaved settings changes</p>
              <p className="text-sm leading-6 text-slate-500">Publish updates to apply new company defaults, branding, and workflow rules across the HRMS workspace.</p>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <Button type="button" variant="outline">Discard</Button>
              <Button type="button">
                <Save className="h-4 w-4" />
                Save settings
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
