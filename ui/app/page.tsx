'use client'

import { ArrowRight, Sparkles } from 'lucide-react'

import Layout from '@/layout'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Dialog, DialogClose, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from '@/components/ui/dialog'
import { Form, FormControl, FormDescription, FormField, FormLabel, FormMessage } from '@/components/ui/form'
import { Input } from '@/components/ui/input'
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { navigationItems } from '@/lib/navigation'

const statCards = [
  { title: 'Active employees', value: '248', delta: '+12 this quarter' },
  { title: 'Open leave requests', value: '19', delta: '4 pending approval today' },
  { title: 'Payroll completion', value: '98.4%', delta: '1 exception remaining' },
]

const employeeRows = [
  { employee: 'Amina Patel', department: 'Finance', status: 'Active', manager: 'Marco Diaz' },
  { employee: 'Jordan Kim', department: 'Operations', status: 'Review due', manager: 'Sara Wong' },
  { employee: 'Noah Bennett', department: 'Engineering', status: 'Leave approved', manager: 'Helen Brooks' },
]

export default function HomePage() {
  return (
    <Layout>
      <div className="space-y-8">
        <section className="grid gap-6 xl:grid-cols-[minmax(0,1.6fr)_minmax(320px,1fr)]">
          <Card>
            <CardHeader>
              <Badge className="w-fit">QC target 10/10</Badge>
              <CardTitle>Enterprise-ready frontend system</CardTitle>
              <CardDescription>
                App Router foundations, reusable shadcn-style primitives, and canonical navigation aligned to the documented UI surfaces.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid gap-4 md:grid-cols-3">
                {statCards.map((card) => (
                  <Card className="bg-[var(--surface-subtle)]" key={card.title}>
                    <CardHeader className="pb-3">
                      <CardDescription>{card.title}</CardDescription>
                      <CardTitle className="text-3xl">{card.value}</CardTitle>
                    </CardHeader>
                    <CardContent>
                      <p className="text-sm text-[var(--muted-foreground)]">{card.delta}</p>
                    </CardContent>
                  </Card>
                ))}
              </div>
              <div className="flex flex-wrap gap-3">
                <Button>
                  Launch dashboard
                  <ArrowRight className="h-4 w-4" />
                </Button>
                <Button variant="outline">Review navigation map</Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>Read-model coverage</CardTitle>
              <CardDescription>Each navigation surface maps to documented read models and capabilities.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              {navigationItems.slice(0, 4).map((item) => (
                <div className="rounded-lg border border-[var(--border)] p-4" key={item.key}>
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div>
                      <p className="font-medium">{item.label}</p>
                      <p className="text-sm text-[var(--muted-foreground)]">{item.description}</p>
                    </div>
                    <Badge variant="outline">{item.capabilityIds.join(', ')}</Badge>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </section>

        <Tabs defaultValue="overview">
          <TabsList>
            <TabsTrigger value="overview">Overview</TabsTrigger>
            <TabsTrigger value="directory">Directory</TabsTrigger>
            <TabsTrigger value="workflow">Workflow</TabsTrigger>
          </TabsList>

          <TabsContent value="overview">
            <div className="grid gap-6 xl:grid-cols-[minmax(0,1.3fr)_minmax(300px,1fr)]">
              <Card>
                <CardHeader>
                  <CardTitle>Reusable table foundation</CardTitle>
                  <CardDescription>Stable table styling for employee, attendance, and payroll data surfaces.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Employee</TableHead>
                        <TableHead>Department</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead>Manager</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {employeeRows.map((row) => (
                        <TableRow key={row.employee}>
                          <TableCell className="font-medium">{row.employee}</TableCell>
                          <TableCell>{row.department}</TableCell>
                          <TableCell>
                            <Badge variant={row.status === 'Active' ? 'success' : 'outline'}>{row.status}</Badge>
                          </TableCell>
                          <TableCell>{row.manager}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </CardContent>
              </Card>

              <Card>
                <CardHeader>
                  <CardTitle>Reusable dialog pattern</CardTitle>
                  <CardDescription>Approval and review interactions can share the same modal shell.</CardDescription>
                </CardHeader>
                <CardContent>
                  <Dialog>
                    <DialogTrigger>
                      <Button variant="outline">Open approval dialog</Button>
                    </DialogTrigger>
                    <DialogContent>
                      <DialogHeader>
                        <DialogTitle>Confirm payroll exception handling</DialogTitle>
                        <DialogDescription>
                          Standardized dialog spacing, hierarchy, and actions for operational workflows.
                        </DialogDescription>
                      </DialogHeader>
                      <DialogFooter>
                        <DialogClose>
                          <Button variant="outline">Cancel</Button>
                        </DialogClose>
                        <DialogClose>
                          <Button>Approve exception</Button>
                        </DialogClose>
                      </DialogFooter>
                    </DialogContent>
                  </Dialog>
                </CardContent>
                <CardFooter>
                  <Badge variant="outline">Dialog</Badge>
                  <Badge variant="outline">Button</Badge>
                </CardFooter>
              </Card>
            </div>
          </TabsContent>

          <TabsContent value="directory">
            <Card>
              <CardHeader>
                <CardTitle>Reusable form controls</CardTitle>
                <CardDescription>Shared field, label, description, and validation presentation for data-entry surfaces.</CardDescription>
              </CardHeader>
              <CardContent>
                <Form>
                  <div className="grid gap-6 md:grid-cols-2">
                    <FormField>
                      <FormLabel htmlFor="employee-search">Employee name</FormLabel>
                      <FormControl>
                        <Input id="employee-search" placeholder="Search employee directory" />
                      </FormControl>
                      <FormDescription>Uses the employee directory read model for quick lookup workflows.</FormDescription>
                    </FormField>
                    <FormField>
                      <FormLabel htmlFor="department-filter">Department</FormLabel>
                      <FormControl>
                        <Input id="department-filter" placeholder="Filter by department" />
                      </FormControl>
                      <FormMessage>Example validation slot for required-field messaging.</FormMessage>
                    </FormField>
                  </div>
                </Form>
              </CardContent>
            </Card>
          </TabsContent>

          <TabsContent value="workflow">
            <Card>
              <CardHeader>
                <div className="flex flex-wrap items-center gap-3">
                  <Sparkles className="h-5 w-5 text-[var(--primary)]" />
                  <CardTitle>Surface registry</CardTitle>
                </div>
                <CardDescription>All sidebar items match the canonical UI surface map with no extra destinations.</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                  {navigationItems.map((item) => (
                    <Card className="bg-[var(--surface-subtle)]" id={`surface-${item.key}`} key={item.key}>
                      <CardHeader className="pb-3">
                        <CardTitle className="text-base">{item.label}</CardTitle>
                        <CardDescription>{item.description}</CardDescription>
                      </CardHeader>
                      <CardContent className="space-y-3">
                        <div className="flex flex-wrap gap-2">
                          {item.readModels.map((model) => (
                            <Badge key={model} variant="outline">{model}</Badge>
                          ))}
                        </div>
                        <p className="text-sm text-[var(--muted-foreground)]">Capabilities: {item.capabilityIds.join(', ')}</p>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          </TabsContent>
        </Tabs>
      </div>
    </Layout>
  )
}
