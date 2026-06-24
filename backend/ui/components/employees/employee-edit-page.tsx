'use client'

import { useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'

import { EmployeeForm, getDefaultEmployeeFormValues, toApiPayload } from '@/components/employees/employee-form'
import { ErrorState, SurfaceSkeleton } from '@/components/base/feedback'
import { getEmployee, updateEmployee } from '@/lib/employees/api'

export function EmployeeEditPage({ employeeId }: { employeeId: string }) {
  const router = useRouter()
  const query = useQuery({
    queryKey: ['employee', employeeId],
    queryFn: () => getEmployee(employeeId),
  })

  if (query.isLoading) {
    return <SurfaceSkeleton lines={8} />
  }

  if (query.isError) {
    return <ErrorState title="Unable to load employee record" message={query.error.message} onRetry={() => query.refetch()} />
  }

  if (!query.data) {
    return null
  }

  const employee = query.data.data

  return (
    <EmployeeForm
      mode="edit"
      employee={employee}
      initialValues={getDefaultEmployeeFormValues(employee)}
      onCancel={() => router.push(`/employees/${employeeId}`)}
      onSubmit={async (values) => {
        await updateEmployee(employeeId, toApiPayload(values, 'edit'))
        router.push(`/employees/${employeeId}`)
      }}
    />
  )
}
