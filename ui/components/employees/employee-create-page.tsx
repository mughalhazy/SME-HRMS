'use client'

import { useRouter } from 'next/navigation'

import { EmployeeForm, getDefaultEmployeeFormValues, toApiPayload } from '@/components/employees/employee-form'
import { createEmployee } from '@/lib/employees/api'

export function EmployeeCreatePage() {
  const router = useRouter()

  return (
    <EmployeeForm
      mode="create"
      initialValues={getDefaultEmployeeFormValues()}
      onCancel={() => router.push('/employees')}
      onSubmit={async (values) => {
        const response = await createEmployee(toApiPayload(values, 'create'))
        router.push(`/employees/${response.data.employee_id}`)
      }}
    />
  )
}
