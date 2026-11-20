import { beforeEach, describe, expect, it, vi } from "vitest";
import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";

vi.mock("../api/client.js", () => ({
  getEmployeeFilters: vi.fn(),
  getEmployees: vi.fn(),
}));

import { getEmployeeFilters, getEmployees } from "../api/client.js";
import EmployeeDirectory from "./EmployeeDirectory.jsx";

const employee = {
  id: 7,
  employee_number: "AC-000007",
  name: "Jordan Lee",
  email: "jordan.lee@example.test",
  country: "India",
  department: "Engineering",
  job_title: "Software Engineer",
  hire_date: "2024-03-15",
  latest_salary: {
    id: 21,
    employee_id: 7,
    amount_minor: 8250000,
    currency_code: "INR",
    effective_date: "2025-04-01",
  },
};

function directoryResponse(overrides = {}) {
  return { items: [employee], page: 1, page_size: 25, total: 26, ...overrides };
}

describe("EmployeeDirectory", () => {
  beforeEach(() => {
    getEmployeeFilters.mockResolvedValue({
      countries: ["India", "United States"],
      departments: ["Engineering", "Finance"],
    });
    getEmployees.mockResolvedValue(directoryResponse());
  });

  it("shows employee details, latest salary, and opens the selected profile", async () => {
    const user = userEvent.setup();
    const onOpenEmployee = vi.fn();
    render(<EmployeeDirectory onOpenEmployee={onOpenEmployee} />);

    expect(await screen.findByRole("button", { name: "View Jordan Lee" })).toBeTruthy();
    expect(screen.getByText("AC-000007")).toBeTruthy();
    expect(screen.getAllByText("Engineering").length).toBeGreaterThan(0);
    expect(screen.getAllByText("India").length).toBeGreaterThan(0);
    expect(screen.getByText("₹82,500.00")).toBeTruthy();

    await user.click(screen.getByRole("button", { name: "View Jordan Lee" }));
    expect(onOpenEmployee).toHaveBeenCalledWith(7);
  });

  it("applies server filters and resets to the first page when search changes", async () => {
    const user = userEvent.setup();
    render(<EmployeeDirectory onOpenEmployee={vi.fn()} />);
    await screen.findByRole("button", { name: "View Jordan Lee" });

    await user.selectOptions(screen.getByLabelText("Filter by country"), "India");
    await waitFor(() => {
      expect(getEmployees).toHaveBeenLastCalledWith(
        expect.objectContaining({ country: "India", page: 1 }),
        expect.objectContaining({ signal: expect.any(AbortSignal) }),
      );
    });

    await user.click(screen.getByRole("button", { name: "Next page" }));
    await waitFor(() => expect(getEmployees).toHaveBeenLastCalledWith(
      expect.objectContaining({ country: "India", page: 2 }),
      expect.anything(),
    ));

    await user.type(screen.getByRole("searchbox", { name: "Search employees" }), "Jordan");
    await waitFor(() => expect(getEmployees).toHaveBeenLastCalledWith(
      expect.objectContaining({ search: "Jordan", country: "India", page: 1 }),
      expect.anything(),
    ), { timeout: 1500 });
  });

  it("shows a retry action when the directory request fails", async () => {
    getEmployees.mockRejectedValueOnce(new Error("Service unavailable"));
    render(<EmployeeDirectory onOpenEmployee={vi.fn()} />);

    expect(await screen.findByRole("alert")).toBeTruthy();
    expect(screen.getByText("Service unavailable")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Try again" })).toBeTruthy();
  });
});
