import { useEffect, useState } from "react";
import { getEmployeeFilters, getEmployees } from "../api/client.js";

const PAGE_SIZE = 25;

function formatSalary(salary) {
  if (!salary) return "Not recorded";
  try {
    const formatter = new Intl.NumberFormat(undefined, {
      style: "currency",
      currency: salary.currency_code,
    });
    const fractionDigits = formatter.resolvedOptions().maximumFractionDigits;
    return formatter.format(salary.amount_minor / 10 ** fractionDigits);
  } catch {
    return `${salary.amount_minor.toLocaleString()} ${salary.currency_code}`;
  }
}

function formatDate(value) {
  if (!value) return "—";
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric",
    month: "short",
    year: "numeric",
    timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function SearchIcon() {
  return (
    <svg aria-hidden="true" viewBox="0 0 20 20" className="search-icon">
      <circle cx="8.7" cy="8.7" r="5.5" fill="none" stroke="currentColor" strokeWidth="1.6" />
      <path d="m12.8 12.8 4 4" fill="none" stroke="currentColor" strokeLinecap="round" strokeWidth="1.6" />
    </svg>
  );
}

export default function EmployeeDirectory({ onOpenEmployee }) {
  const [searchText, setSearchText] = useState("");
  const [debouncedSearch, setDebouncedSearch] = useState("");
  const [country, setCountry] = useState("");
  const [department, setDepartment] = useState("");
  const [page, setPage] = useState(1);
  const [employees, setEmployees] = useState([]);
  const [total, setTotal] = useState(0);
  const [filters, setFilters] = useState({ countries: [], departments: [] });
  const [filterError, setFilterError] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const timer = window.setTimeout(() => setDebouncedSearch(searchText.trim()), 250);
    return () => window.clearTimeout(timer);
  }, [searchText]);

  useEffect(() => {
    const controller = new AbortController();
    getEmployeeFilters({ signal: controller.signal })
      .then((data) => setFilters(data))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setFilterError("Filter options are unavailable.");
      });
    return () => controller.abort();
  }, []);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    getEmployees(
      {
        search: debouncedSearch,
        country,
        department,
        page,
        page_size: PAGE_SIZE,
      },
      { signal: controller.signal },
    )
      .then((data) => {
        setEmployees(data.items);
        setTotal(data.total);
      })
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [debouncedSearch, country, department, page, reload]);

  const pageCount = Math.max(1, Math.ceil(total / PAGE_SIZE));
  const firstVisible = total === 0 ? 0 : (page - 1) * PAGE_SIZE + 1;
  const lastVisible = Math.min(page * PAGE_SIZE, total);
  const hasFilters = Boolean(debouncedSearch || country || department);

  function resetFilters() {
    setSearchText("");
    setDebouncedSearch("");
    setCountry("");
    setDepartment("");
    setPage(1);
  }

  return (
    <section className="directory" aria-labelledby="directory-title">
      <div className="directory__intro">
        <div>
          <div className="section-eyebrow">PEOPLE DIRECTORY</div>
          <h2 id="directory-title">Employee records</h2>
          <p>Find a colleague and review their current profile and pay.</p>
        </div>
        <div className="directory-count">
          <strong>{total.toLocaleString()}</strong>
          <span>{total === 1 ? "employee" : "employees"}</span>
        </div>
      </div>

      <div className="directory-toolbar">
        <label className="search-field">
          <SearchIcon />
          <span className="visually-hidden">Search employees</span>
          <input
            type="search"
            value={searchText}
            onChange={(event) => {
              setSearchText(event.target.value);
              setPage(1);
            }}
            placeholder="Search name, email, or employee ID"
          />
        </label>
        <label className="filter-field">
          <span className="visually-hidden">Filter by country</span>
          <select value={country} onChange={(event) => { setCountry(event.target.value); setPage(1); }}>
            <option value="">All countries</option>
            {filters.countries.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        <label className="filter-field">
          <span className="visually-hidden">Filter by department</span>
          <select value={department} onChange={(event) => { setDepartment(event.target.value); setPage(1); }}>
            <option value="">All departments</option>
            {filters.departments.map((value) => <option key={value} value={value}>{value}</option>)}
          </select>
        </label>
        {hasFilters && <button className="clear-filters" type="button" onClick={resetFilters}>Clear filters</button>}
      </div>
      {filterError && <p className="inline-warning" role="status">{filterError}</p>}

      {error ? (
        <div className="directory-state directory-state--error" role="alert">
          <strong>We couldn’t load employees.</strong>
          <span>{error}</span>
          <button type="button" onClick={() => setReload((value) => value + 1)}>Try again</button>
        </div>
      ) : (
        <>
          <div className="table-card">
            <div className="table-scroll">
              <table className="employee-table">
                <thead>
                  <tr>
                    <th scope="col">Employee</th>
                    <th scope="col">Employee ID</th>
                    <th scope="col">Department</th>
                    <th scope="col">Country</th>
                    <th scope="col">Latest salary</th>
                    <th scope="col"><span className="visually-hidden">Profile</span></th>
                  </tr>
                </thead>
                <tbody>
                  {loading ? (
                    <tr><td className="table-message" colSpan="6">Loading employee records…</td></tr>
                  ) : employees.length === 0 ? (
                    <tr>
                      <td className="table-message" colSpan="6">
                        <strong>{hasFilters ? "No employees match these filters" : "No employees yet"}</strong>
                        <span>{hasFilters ? "Try a different search or clear the filters." : "Employee records will appear here."}</span>
                      </td>
                    </tr>
                  ) : employees.map((employee) => (
                    <tr key={employee.id}>
                      <td>
                        <div className="employee-name">{employee.name}</div>
                        <div className="employee-email">{employee.email}</div>
                      </td>
                      <td><span className="employee-number">{employee.employee_number}</span></td>
                      <td>{employee.department}</td>
                      <td>{employee.country}</td>
                      <td>
                        <div className="salary-value">{formatSalary(employee.latest_salary)}</div>
                        <div className="salary-date">
                          {employee.latest_salary ? `Effective ${formatDate(employee.latest_salary.effective_date)}` : "No salary record"}
                        </div>
                      </td>
                      <td>
                        <button className="view-profile" type="button" onClick={() => onOpenEmployee(employee.id)}>
                          View <span className="visually-hidden">{employee.name}</span>
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <div className="table-footer">
              <span>Showing {firstVisible.toLocaleString()}–{lastVisible.toLocaleString()} of {total.toLocaleString()}</span>
              <div className="pagination" aria-label="Employee pages">
                <button type="button" disabled={page <= 1 || loading} onClick={() => setPage((value) => value - 1)} aria-label="Previous page">‹</button>
                <span>Page {page} of {pageCount}</span>
                <button type="button" disabled={page >= pageCount || loading} onClick={() => setPage((value) => value + 1)} aria-label="Next page">›</button>
              </div>
            </div>
          </div>
        </>
      )}
    </section>
  );
}
