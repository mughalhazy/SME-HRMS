"use client";

import { useMemo, useState } from "react";
import {
  CalendarDays,
  CheckCircle2,
  Clock3,
  Download,
  TriangleAlert,
  UserRoundX,
} from "lucide-react";

import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Select } from "@/components/ui/input";
import { KpiGrid, PageStack, StatCard } from "@/components/ui/page";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

type AttendanceStatus = "Present" | "Late" | "Absent" | "Leave";
type AttendanceFlag =
  | "Late arrival"
  | "Missing check-in"
  | "Missing check-out"
  | "Attendance anomaly";

type AttendanceRow = {
  id: string;
  name: string;
  employeeId: string;
  department: string;
  checkIn: string;
  checkOut: string;
  status: AttendanceStatus;
  workHours: string;
  flags: AttendanceFlag[];
  note: string;
};

const attendanceRows: AttendanceRow[] = [
  {
    id: "1",
    name: "Ariana Flores",
    employeeId: "EMP-1042",
    department: "Operations",
    checkIn: "08:54 AM",
    checkOut: "05:31 PM",
    status: "Present",
    workHours: "8h 37m",
    flags: [],
    note: "On schedule with complete attendance logs for the day.",
  },
  {
    id: "2",
    name: "Darnell Price",
    employeeId: "EMP-1188",
    department: "Finance",
    checkIn: "09:17 AM",
    checkOut: "06:04 PM",
    status: "Late",
    workHours: "8h 47m",
    flags: ["Late arrival"],
    note: "Clock-in was 17 minutes after the scheduled start time.",
  },
  {
    id: "3",
    name: "Mei Nakamura",
    employeeId: "EMP-0964",
    department: "Engineering",
    checkIn: "08:41 AM",
    checkOut: "05:45 PM",
    status: "Present",
    workHours: "9h 04m",
    flags: [],
    note: "Attendance record is complete and within expected hours.",
  },
  {
    id: "4",
    name: "Jamal Carter",
    employeeId: "EMP-1215",
    department: "Customer Success",
    checkIn: "—",
    checkOut: "—",
    status: "Absent",
    workHours: "0h 00m",
    flags: ["Missing check-in"],
    note: "No attendance event has been recorded for the selected date.",
  },
  {
    id: "5",
    name: "Nina Patel",
    employeeId: "EMP-0871",
    department: "Human Resources",
    checkIn: "—",
    checkOut: "—",
    status: "Leave",
    workHours: "0h 00m",
    flags: [],
    note: "Approved leave on file for the selected date.",
  },
  {
    id: "6",
    name: "Carlos Mendes",
    employeeId: "EMP-1130",
    department: "Operations",
    checkIn: "09:11 AM",
    checkOut: "—",
    status: "Late",
    workHours: "7h 26m",
    flags: ["Late arrival", "Missing check-out"],
    note: "Late check-in and no end-of-day checkout recorded yet.",
  },
  {
    id: "7",
    name: "Elena Petrova",
    employeeId: "EMP-1029",
    department: "Engineering",
    checkIn: "08:48 AM",
    checkOut: "05:40 PM",
    status: "Present",
    workHours: "8h 52m",
    flags: [],
    note: "Complete attendance record with no exceptions detected.",
  },
  {
    id: "8",
    name: "Marcus Lee",
    employeeId: "EMP-1106",
    department: "Sales",
    checkIn: "08:59 AM",
    checkOut: "—",
    status: "Present",
    workHours: "7h 58m",
    flags: ["Missing check-out"],
    note: "Active attendance record remains open without checkout.",
  },
];

const departments = [
  "All departments",
  "Operations",
  "Finance",
  "Engineering",
  "Customer Success",
  "Human Resources",
  "Sales",
];
const statuses = ["All statuses", "Present", "Late", "Absent", "Leave"];

function formatDateLabel(value: string) {
  if (!value) {
    return "Select date";
  }

  return new Intl.DateTimeFormat("en-US", {
    weekday: "long",
    month: "long",
    day: "numeric",
    year: "numeric",
  }).format(new Date(`${value}T00:00:00`));
}

function getInitials(name: string) {
  return name
    .split(" ")
    .map((part) => part[0])
    .join("")
    .slice(0, 2)
    .toUpperCase();
}

function getStatusTone(status: AttendanceStatus) {
  switch (status) {
    case "Present":
      return {
        variant: "success" as const,
        className: "border-transparent bg-emerald-50 text-emerald-700",
      };
    case "Late":
      return {
        variant: "outline" as const,
        className: "border-amber-200 bg-amber-50 text-amber-700",
      };
    case "Absent":
      return {
        variant: "outline" as const,
        className: "border-rose-200 bg-rose-50 text-rose-700",
      };
    case "Leave":
      return {
        variant: "outline" as const,
        className: "border-sky-200 bg-sky-50 text-sky-700",
      };
  }
}

function getFlagTone(flag: AttendanceFlag) {
  switch (flag) {
    case "Late arrival":
      return "border-amber-200 bg-amber-50 text-amber-700";
    case "Missing check-in":
      return "border-rose-200 bg-rose-50 text-rose-700";
    case "Missing check-out":
      return "border-slate-200 bg-slate-100 text-slate-700";
    case "Attendance anomaly":
      return "border-sky-200 bg-sky-50 text-sky-700";
  }
}

export function Attendance() {
  const [selectedDate, setSelectedDate] = useState("2026-03-19");
  const [department, setDepartment] = useState("All departments");
  const [status, setStatus] = useState("All statuses");
  const [search, setSearch] = useState("");
  const [selectedRowId, setSelectedRowId] = useState("6");

  const filteredRows = useMemo(() => {
    return attendanceRows.filter((row) => {
      const matchesDepartment =
        department === "All departments" || row.department === department;
      const matchesStatus = status === "All statuses" || row.status === status;
      const matchesSearch =
        search.trim().length === 0 ||
        row.name.toLowerCase().includes(search.toLowerCase()) ||
        row.employeeId.toLowerCase().includes(search.toLowerCase());

      return matchesDepartment && matchesStatus && matchesSearch;
    });
  }, [department, search, status]);

  const selectedRow = useMemo(() => {
    return (
      filteredRows.find((row) => row.id === selectedRowId) ??
      filteredRows[0] ??
      null
    );
  }, [filteredRows, selectedRowId]);

  const summary = useMemo(() => {
    return filteredRows.reduce(
      (counts, row) => {
        if (row.status === "Present") {
          counts.present += 1;
        }

        if (row.status === "Absent") {
          counts.absent += 1;
        }

        if (row.status === "Late") {
          counts.late += 1;
        }

        if (row.flags.length > 0) {
          counts.exceptions += 1;
        }

        return counts;
      },
      { present: 0, absent: 0, late: 0, exceptions: 0 },
    );
  }, [filteredRows]);

  const exceptionRows = useMemo(
    () => filteredRows.filter((row) => row.flags.length > 0),
    [filteredRows],
  );

  return (
    <PageStack className="text-slate-900">
      <section className="grid gap-6 xl:grid-cols-12 xl:items-end">
        <div className="space-y-2 xl:col-span-8">
          <p className="text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">
            Attendance monitoring
          </p>
          <p className="max-w-3xl text-sm leading-6 text-slate-600">
            Use the daily register to focus on presence, missing time events,
            and exceptions that require immediate follow-up.
          </p>
        </div>

        <div className="flex flex-col gap-3 xl:col-span-4 xl:items-end">
          <Badge
            className="justify-center border-slate-200 bg-white px-3 py-1 text-slate-600"
            variant="outline"
          >
            {formatDateLabel(selectedDate)}
          </Badge>
          <Button className="w-full sm:w-auto" type="button">
            <Download className="h-4 w-4" />
            Export log
          </Button>
        </div>
      </section>

      <KpiGrid>
        <StatCard
          title="Present"
          value={String(summary.present)}
          hint="Employees with complete records for the selected date."
          icon={CheckCircle2}
        />
        <StatCard
          title="Absent"
          value={String(summary.absent)}
          hint="No attendance event captured for the active day."
          icon={UserRoundX}
        />
        <StatCard
          title="Late"
          value={String(summary.late)}
          hint="Clock-ins that started behind schedule and need review."
          icon={Clock3}
        />
        <StatCard
          title="Exceptions"
          value={String(summary.exceptions)}
          hint="Open anomalies or incomplete logs that need action."
          icon={TriangleAlert}
        />
      </KpiGrid>

      <section className="grid gap-6 xl:grid-cols-12">
        <div className="xl:col-span-12">
          <Card className="border-slate-200 bg-white">
            <CardContent className="p-4">
              <div className="grid gap-4 xl:grid-cols-[180px_180px_180px_minmax(0,1fr)_160px] xl:items-end">
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Date
                  </label>
                  <div className="relative">
                    <Input
                      className="pr-10"
                      type="date"
                      value={selectedDate}
                      onChange={(event) => setSelectedDate(event.target.value)}
                    />
                    <CalendarDays className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
                  </div>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Department
                  </label>
                  <Select
                    value={department}
                    onChange={(event) => setDepartment(event.target.value)}
                  >
                    {departments.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Status
                  </label>
                  <Select
                    value={status}
                    onChange={(event) => setStatus(event.target.value)}
                  >
                    {statuses.map((item) => (
                      <option key={item} value={item}>
                        {item}
                      </option>
                    ))}
                  </Select>
                </div>
                <div className="space-y-2">
                  <label className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Find employee
                  </label>
                  <Input
                    placeholder="Search by name or employee ID"
                    value={search}
                    onChange={(event) => setSearch(event.target.value)}
                  />
                </div>
                <Button
                  className="w-full xl:w-full"
                  type="button"
                  variant="outline"
                  onClick={() => {
                    setSelectedDate("2026-03-19");
                    setDepartment("All departments");
                    setStatus("All statuses");
                    setSearch("");
                  }}
                >
                  Reset filters
                </Button>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="xl:col-span-12">
          <Card className="border-slate-200 bg-white">
            <CardContent className="p-0">
              <div className="flex flex-col gap-3 px-4 py-4 sm:flex-row sm:items-end sm:justify-between">
                <div className="space-y-1">
                  <h2 className="text-lg font-semibold text-slate-950">
                    Daily attendance log
                  </h2>
                  <p className="text-sm text-slate-500">
                    Table-first view of attendance status, time records, and
                    operational flags.
                  </p>
                </div>
                <Badge
                  className="justify-center border-slate-200 bg-slate-50 px-3 py-1 text-slate-600"
                  variant="outline"
                >
                  {filteredRows.length} employees
                </Badge>
              </div>

              <Table className="table-fixed">
                <colgroup>
                  <col className="w-[32%]" />
                  <col className="w-[12%]" />
                  <col className="w-[12%]" />
                  <col className="w-[12%]" />
                  <col className="w-[12%]" />
                  <col className="w-[20%]" />
                </colgroup>
                <TableHeader>
                  <TableRow className="border-slate-100 hover:bg-transparent hover:shadow-none">
                    <TableHead className="px-6">Employee</TableHead>
                    <TableHead className="px-6">Status</TableHead>
                    <TableHead className="px-6">Check-in</TableHead>
                    <TableHead className="px-6">Check-out</TableHead>
                    <TableHead className="px-6">Hours worked</TableHead>
                    <TableHead className="px-6">Flags</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody className="[&_tr:nth-child(even)]:bg-transparent">
                  {filteredRows.length > 0 ? (
                    filteredRows.map((row) => {
                      const statusTone = getStatusTone(row.status);
                      const isSelected = selectedRow?.id === row.id;

                      return (
                        <TableRow
                          key={row.id}
                          className={cn(
                            "cursor-pointer border-slate-100 bg-white hover:bg-slate-50 hover:shadow-none",
                            isSelected && "bg-slate-50",
                          )}
                          onClick={() => setSelectedRowId(row.id)}
                        >
                          <TableCell className="px-6 py-4">
                            <div className="flex items-center gap-3">
                              <Avatar className="h-10 w-10 border border-slate-200 bg-slate-50">
                                <AvatarFallback>
                                  {getInitials(row.name)}
                                </AvatarFallback>
                              </Avatar>
                              <div className="min-w-0 space-y-1">
                                <p className="truncate text-sm font-semibold text-slate-950">
                                  {row.name}
                                </p>
                                <p className="truncate text-xs text-slate-500">
                                  {row.employeeId} · {row.department}
                                </p>
                              </div>
                            </div>
                          </TableCell>
                          <TableCell className="px-6 py-4 align-middle">
                            <Badge
                              className={cn(
                                "min-w-[88px] justify-center px-3 py-1 text-xs font-semibold",
                                statusTone.className,
                              )}
                              variant={statusTone.variant}
                            >
                              {row.status}
                            </Badge>
                          </TableCell>
                          <TableCell className="px-6 py-4 text-sm font-medium tabular-nums text-slate-700">
                            {row.checkIn}
                          </TableCell>
                          <TableCell className="px-6 py-4 text-sm font-medium tabular-nums text-slate-700">
                            {row.checkOut}
                          </TableCell>
                          <TableCell className="px-6 py-4 text-sm font-medium tabular-nums text-slate-700">
                            {row.workHours}
                          </TableCell>
                          <TableCell className="px-6 py-4">
                            <div className="flex min-h-8 flex-wrap items-center gap-2">
                              {row.flags.length > 0 ? (
                                row.flags.map((flag) => (
                                  <Badge
                                    key={flag}
                                    className={cn(
                                      "px-3 py-1 text-xs font-medium",
                                      getFlagTone(flag),
                                    )}
                                    variant="outline"
                                  >
                                    {flag}
                                  </Badge>
                                ))
                              ) : (
                                <span className="text-sm text-slate-400">
                                  No flags
                                </span>
                              )}
                            </div>
                          </TableCell>
                        </TableRow>
                      );
                    })
                  ) : (
                    <TableRow className="border-slate-100 bg-white hover:bg-white hover:shadow-none">
                      <TableCell className="px-6 py-12 text-center" colSpan={6}>
                        <div className="flex flex-col items-center gap-2">
                          <p className="text-sm font-medium text-slate-900">
                            No attendance records match the current filters.
                          </p>
                          <p className="text-sm text-slate-500">
                            Adjust date, department, or status filters to
                            restore the monitoring view.
                          </p>
                        </div>
                      </TableCell>
                    </TableRow>
                  )}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </div>

        <div className="grid gap-6 xl:col-span-12 xl:grid-cols-[minmax(0,1fr)_320px]">
          <Card className="border-slate-200 bg-white">
            <CardContent className="p-4">
              <div className="space-y-4">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-1">
                    <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                      Selected record
                    </p>
                    <h3 className="text-lg font-semibold text-slate-950">
                      {selectedRow?.name ?? "No employee selected"}
                    </h3>
                  </div>
                  {selectedRow ? (
                    <Badge
                      className={cn(
                        "min-w-[88px] justify-center px-3 py-1 text-xs font-semibold",
                        getStatusTone(selectedRow.status).className,
                      )}
                      variant={getStatusTone(selectedRow.status).variant}
                    >
                      {selectedRow.status}
                    </Badge>
                  ) : null}
                </div>

                {selectedRow ? (
                  <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                    <div className="space-y-2 rounded-[var(--radius-control)] bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                        Employee
                      </p>
                      <p className="text-sm font-medium text-slate-900">
                        {selectedRow.employeeId}
                      </p>
                      <p className="text-sm text-slate-500">
                        {selectedRow.department}
                      </p>
                    </div>
                    <div className="space-y-2 rounded-[var(--radius-control)] bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                        Check-in
                      </p>
                      <p className="text-sm font-medium tabular-nums text-slate-900">
                        {selectedRow.checkIn}
                      </p>
                    </div>
                    <div className="space-y-2 rounded-[var(--radius-control)] bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                        Check-out
                      </p>
                      <p className="text-sm font-medium tabular-nums text-slate-900">
                        {selectedRow.checkOut}
                      </p>
                    </div>
                    <div className="space-y-2 rounded-[var(--radius-control)] bg-slate-50 p-4">
                      <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                        Hours worked
                      </p>
                      <p className="text-sm font-medium tabular-nums text-slate-900">
                        {selectedRow.workHours}
                      </p>
                    </div>
                  </div>
                ) : null}

                <div className="space-y-2">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Operational note
                  </p>
                  <p className="text-sm leading-6 text-slate-600">
                    {selectedRow?.note ??
                      "Select a row to inspect attendance details and exceptions."}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          <Card className="border-slate-200 bg-white">
            <CardContent className="p-4">
              <div className="space-y-4">
                <div className="space-y-1">
                  <p className="text-xs font-semibold uppercase tracking-[0.14em] text-slate-500">
                    Exceptions
                  </p>
                  <h3 className="text-lg font-semibold text-slate-950">
                    Requires follow-up
                  </h3>
                </div>

                <div className="space-y-3">
                  {exceptionRows.length > 0 ? (
                    exceptionRows.map((row) => (
                      <button
                        key={row.id}
                        className="flex w-full items-start justify-between gap-3 rounded-[var(--radius-control)] bg-slate-50 p-4 text-left transition-colors hover:bg-slate-100"
                        type="button"
                        onClick={() => setSelectedRowId(row.id)}
                      >
                        <div className="min-w-0 space-y-1">
                          <p className="truncate text-sm font-medium text-slate-900">
                            {row.name}
                          </p>
                          <p className="truncate text-sm text-slate-500">
                            {row.employeeId} · {row.department}
                          </p>
                        </div>
                        <div className="flex max-w-[144px] flex-wrap justify-end gap-2">
                          {row.flags.map((flag) => (
                            <Badge
                              key={`${row.id}-${flag}`}
                              className={cn(
                                "px-3 py-1 text-xs font-medium",
                                getFlagTone(flag),
                              )}
                              variant="outline"
                            >
                              {flag}
                            </Badge>
                          ))}
                        </div>
                      </button>
                    ))
                  ) : (
                    <div className="rounded-[var(--radius-control)] bg-slate-50 p-4">
                      <p className="text-sm font-medium text-slate-900">
                        No attendance exceptions detected.
                      </p>
                      <p className="mt-1 text-sm text-slate-500">
                        Monitoring queue is clear for the current filter set.
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </section>
    </PageStack>
  );
}
