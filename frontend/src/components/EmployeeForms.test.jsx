import { beforeEach, describe, expect, it, vi } from "vitest";
import { fireEvent, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../api/client.js", () => ({
  createEmployee: vi.fn(),
  updateEmployee: vi.fn(),
  addSalaryRecord: vi.fn(),
}));

import { addSalaryRecord, createEmployee } from "../api/client.js";
import EmployeeForm from "./EmployeeForm.jsx";
import { SalaryForm } from "./EmployeeDetails.jsx";

describe("employee and salary forms", () => {
  beforeEach(() => {
    createEmployee.mockReset();
    addSalaryRecord.mockReset();
  });

  it("sends valid employee fields and displays a duplicate-record API error", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    createEmployee.mockRejectedValue(new Error("Employee number or email already exists"));
    render(<EmployeeForm mode="create" onSaved={onSaved} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText("Employee number"), "AC-0010");
    await user.type(screen.getByLabelText("Full name"), "Alex Morgan");
    await user.type(screen.getByLabelText("Work email"), "alex@example.test");
    await user.type(screen.getByLabelText("Country"), "India");
    await user.type(screen.getByLabelText("Department"), "Engineering");
    await user.type(screen.getByLabelText("Job title"), "Analyst");
    fireEvent.change(screen.getByLabelText("Hire date"), { target: { value: "2024-03-15" } });
    await user.click(screen.getByRole("button", { name: "Create employee" }));

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Employee number or email already exists")).toBeTruthy();
    expect(createEmployee).toHaveBeenCalledWith({
      employee_number: "AC-0010",
      name: "Alex Morgan",
      email: "alex@example.test",
      country: "India",
      department: "Engineering",
      job_title: "Analyst",
      hire_date: "2024-03-15",
    });
    expect(onSaved).not.toHaveBeenCalled();
  });

  it("rejects amounts with too many currency decimal places before submitting", async () => {
    const user = userEvent.setup();
    render(<SalaryForm employeeId={17} minimumDate="2024-01-01" onSaved={vi.fn()} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText("Annual salary"), "120.345");
    await user.click(screen.getByRole("button", { name: "Add salary record" }));

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("USD allows up to 2 decimal places.")).toBeTruthy();
    expect(addSalaryRecord).not.toHaveBeenCalled();
  });

  it("converts a valid amount to minor units and shows API errors", async () => {
    const user = userEvent.setup();
    const onSaved = vi.fn();
    addSalaryRecord.mockRejectedValue(new Error("Effective date cannot precede hire date"));
    render(<SalaryForm employeeId={17} minimumDate="2024-01-01" onSaved={onSaved} onCancel={vi.fn()} />);

    await user.type(screen.getByLabelText("Annual salary"), "120.34");
    fireEvent.change(screen.getByLabelText("Effective date"), { target: { value: "2025-01-01" } });
    await user.click(screen.getByRole("button", { name: "Add salary record" }));

    expect(await screen.findByText("Effective date cannot precede hire date")).toBeTruthy();
    expect(addSalaryRecord).toHaveBeenCalledWith(17, {
      amount_minor: 12034,
      currency_code: "USD",
      effective_date: "2025-01-01",
    });
    expect(onSaved).not.toHaveBeenCalled();
  });
});
