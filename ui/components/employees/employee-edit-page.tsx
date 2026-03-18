'use client'

import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'

import { EmployeeForm, getDefaultEmployeeFormValues, toApiPayload } from '@/components/employees/employee-form'
import { getEmployee, updateEmployee } from '@/lib/employees/api'

export function EmployeeEditPage({ employeeId }: { employeeId: string }) {
  const router = useRouter()
  const query = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => getEmployee(employeeId),
  })

  if (query.isLoading) {
    return <div className="rounded-3xl border border-slate-200 bg-white p-10 text-sm text-slate-500">Loading employee record…</div>
  }

  if (query.isError) {
    return <div className="rounded-3xl border border-slate-200 bg-white p-10 text-sm text-rose-600">{query.error.message}</div>
  }

  return (
    <EmployeeForm
      mode="edit"
      employee={query.data.data}
      initialValues={getDefaultEmployeeFormValues(query.data.data)}
      onCancel={() => router.push(`/employees/${employeeId}`)}
      onSubmit={async (values) => {
        await updateEmployee(employeeId, toApiPayload(values, 'edit'))
        router.push(`/employees/${employeeId}`)
      }}
    />
  )
}
