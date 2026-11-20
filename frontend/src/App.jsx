import { useEffect, useState } from "react";
import { getAnalyticsSummary, getHealth } from "./api/client.js";
import EmployeeDirectory from "./components/EmployeeDirectory.jsx";
import EmployeeDetails from "./components/EmployeeDetails.jsx";

const navigation = [
  { id: "overview", label: "Overview", marker: "OV" },
  { id: "employees", label: "Employees", marker: "EM" },
];

function BackendStatus() {
  const [state, setState] = useState({ status: "loading", message: "Connecting to API" });

  useEffect(() => {
    const controller = new AbortController();
    getHealth({ signal: controller.signal })
      .then(() => setState({ status: "online", message: "API connected" }))
      .catch((error) => {
        if (error.name !== "AbortError") {
          setState({ status: "offline", message: "API unavailable" });
        }
      });
    return () => controller.abort();
  }, []);

  return (
    <div className={`connection connection--${state.status}`} role="status" aria-live="polite">
      <span className="connection__dot" aria-hidden="true" />
      <span>{state.message}</span>
    </div>
  );
}

function OverviewPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    getAnalyticsSummary({ signal: controller.signal })
      .then((data) => setSummary(data))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [reload]);

  if (loading) {
    return <div className="analytics-loading" role="status">Loading compensation insights…</div>;
  }

  if (error) {
    return (
      <section className="analytics-error" role="alert">
        <strong>We couldn’t load compensation insights.</strong>
        <span>{error}</span>
        <button className="button-primary" type="button" onClick={() => setReload((value) => value + 1)}>Try again</button>
      </section>
    );
  }

  const currencyGroups = summary.compensation_by_currency;
  const employeesWithSalary = currencyGroups.reduce((total, item) => total + item.employee_count, 0);
  const countries = summary.headcount_by_country.length;
  const departments = summary.headcount_by_department.length;

  return (
    <section className="analytics-dashboard" aria-labelledby="analytics-title">
      <div className="analytics-heading">
        <div>
          <div className="section-eyebrow">WORKFORCE COMPENSATION</div>
          <h2 id="analytics-title">Compensation overview</h2>
          <p>Current effective salaries across the organization, grouped by currency.</p>
        </div>
        <button className="button-secondary refresh-button" type="button" onClick={() => setReload((value) => value + 1)}>
          <span aria-hidden="true">↻</span> Refresh
        </button>
      </div>

      <div className="metric-grid">
        <MetricCard label="Total employees" value={summary.headcount.toLocaleString()} hint="All active employee records" icon="EM" tone="green" />
        <MetricCard label="With salary records" value={employeesWithSalary.toLocaleString()} hint="Current effective salary on file" icon="SR" tone="blue" />
        <MetricCard label="Currencies" value={currencyGroups.length.toLocaleString()} hint="Shown as separate groups" icon="FX" tone="gold" />
        <MetricCard label="Countries" value={countries.toLocaleString()} hint={`${departments} departments represented`} icon="GL" tone="violet" />
      </div>

      <section className="analytics-panel" aria-labelledby="currency-summary-title">
        <div className="analytics-panel__heading">
          <div><h3 id="currency-summary-title">Salary summary by currency</h3><p>Latest effective salary per employee, formatted in its own currency.</p></div>
          <span className="panel-badge">CURRENT RECORDS</span>
        </div>
        <CurrencySummaryTable groups={currencyGroups} />
      </section>

      <div className="analytics-breakdowns">
        <BreakdownTable
          title="Compensation by country"
          dimension="country"
          headcount={summary.headcount_by_country}
          compensation={summary.compensation_by_country}
        />
        <BreakdownTable
          title="Compensation by department"
          dimension="department"
          headcount={summary.headcount_by_department}
          compensation={summary.compensation_by_department}
        />
      </div>

      <p className="analytics-footnote">
        Each compensation row shows one currency. Salary records in different currencies are never combined.
      </p>
    </section>
  );
}

function MetricCard({ label, value, hint, icon, tone }) {
  return (
    <article className="metric-card">
      <div className={`metric-card__icon metric-card__icon--${tone}`} aria-hidden="true">{icon}</div>
      <div className="metric-card__label">{label}</div>
      <div className="metric-card__value">{value}</div>
      <div className="metric-card__hint">{hint}</div>
    </article>
  );
}

function formatMoney(amountMinor, currencyCode) {
  try {
    const formatter = new Intl.NumberFormat(undefined, { style: "currency", currency: currencyCode });
    const fractionDigits = formatter.resolvedOptions().maximumFractionDigits;
    return formatter.format(amountMinor / 10 ** fractionDigits);
  } catch {
    return `${amountMinor.toLocaleString()} ${currencyCode}`;
  }
}

function CurrencySummaryTable({ groups }) {
  if (groups.length === 0) return <div className="analytics-empty">Salary summaries appear after salary records are added.</div>;
  return (
    <div className="analytics-table-wrap">
      <table className="analytics-table">
        <thead><tr><th scope="col">Currency</th><th scope="col">Employees</th><th scope="col">Average salary</th><th scope="col">Range</th></tr></thead>
        <tbody>{groups.map((group) => (
          <tr key={group.currency_code}>
            <td><span className="currency-name"><span className="currency-square">{group.currency_code.slice(0, 1)}</span><strong>{group.currency_code}</strong></span></td>
            <td>{group.employee_count.toLocaleString()}</td>
            <td className="analytics-average">{formatMoney(group.average_salary_minor, group.currency_code)}</td>
            <td>{formatMoney(group.minimum_salary_minor, group.currency_code)} <span className="range-separator">to</span> {formatMoney(group.maximum_salary_minor, group.currency_code)}</td>
          </tr>
        ))}</tbody>
      </table>
    </div>
  );
}

function BreakdownTable({ title, dimension, headcount, compensation }) {
  const groups = new Map(headcount.map((item) => [item[dimension], { ...item, salaryGroups: [] }]));
  for (const item of compensation) {
    if (!groups.has(item[dimension])) groups.set(item[dimension], { [dimension]: item[dimension], employee_count: 0, salaryGroups: [] });
    groups.get(item[dimension]).salaryGroups.push(item);
  }
  const rows = [...groups.values()].sort((left, right) => right.employee_count - left.employee_count || left[dimension].localeCompare(right[dimension]));

  return (
    <section className="analytics-panel breakdown-panel" aria-labelledby={`${dimension}-breakdown-title`}>
      <div className="analytics-panel__heading">
        <div><h3 id={`${dimension}-breakdown-title`}>{title}</h3><p>Pay statistics stay separate for each currency.</p></div>
      </div>
      {rows.length === 0 ? <div className="analytics-empty">No employee records yet.</div> : (
        <div className="analytics-table-wrap">
          <table className="analytics-table breakdown-table">
            <thead><tr><th scope="col">{dimension === "country" ? "Country" : "Department"}</th><th scope="col">Headcount</th><th scope="col">Pay group</th><th scope="col">Average salary</th></tr></thead>
            <tbody>{rows.flatMap((group) => {
              if (group.salaryGroups.length === 0) {
                return [<tr key={`${group[dimension]}-no-salary`}><td>{group[dimension]}</td><td>{group.employee_count.toLocaleString()}</td><td colSpan="2" className="no-salary-cell">No salary records</td></tr>];
              }
              return group.salaryGroups.map((salary) => (
                <tr key={`${group[dimension]}-${salary.currency_code}`}>
                  <td>{group[dimension]}</td>
                  <td>{group.employee_count.toLocaleString()}</td>
                  <td><span className="currency-tag">{salary.currency_code}</span><span className="pay-group-count">{salary.employee_count} paid</span></td>
                  <td className="analytics-average">{formatMoney(salary.average_salary_minor, salary.currency_code)}</td>
                </tr>
              ));
            })}</tbody>
          </table>
        </div>
      )}
    </section>
  );
}

export default function App() {
  const [activePage, setActivePage] = useState("overview");
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const activeItem = activePage === "employee"
    ? { label: "Employee profile" }
    : navigation.find((item) => item.id === activePage);

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <a className="brand" href="#overview" onClick={() => setActivePage("overview")}>
          <span className="brand__mark" aria-hidden="true">A</span>
          <span className="brand__copy">
            <strong>ACME</strong>
            <small>PEOPLE &amp; PAY</small>
          </span>
        </a>

        <div className="sidebar__section-label">WORKSPACE</div>
        <nav aria-label="Main navigation" className="navigation">
          {navigation.map((item) => (
            <button
              className={`navigation__item ${activePage === item.id ? "is-active" : ""}`}
              key={item.id}
              onClick={() => setActivePage(item.id)}
              type="button"
              aria-current={activePage === item.id ? "page" : undefined}
            >
              <span className="navigation__marker" aria-hidden="true">{item.marker}</span>
              <span>{item.label}</span>
            </button>
          ))}
        </nav>

        <div className="sidebar__bottom">
          <div className="user-avatar" aria-hidden="true">HR</div>
          <div className="user-copy">
            <strong>HR workspace</strong>
            <span>ACME organization</span>
          </div>
        </div>
      </aside>

      <main className="main-content">
        <header className="topbar">
          <div>
            <div className="breadcrumb">People &amp; Pay <span>/</span> {activeItem.label}</div>
            <h1>{activeItem.label}</h1>
          </div>
          <BackendStatus />
        </header>

        <div className="page-content">
          {activePage === "overview" && <OverviewPage />}
          {activePage === "employees" && (
            <EmployeeDirectory
              onOpenEmployee={(employeeId) => {
                setSelectedEmployeeId(employeeId);
                setActivePage("employee");
              }}
            />
          )}
          {activePage === "employee" && (
            <EmployeeDetails
              employeeId={selectedEmployeeId}
              onBack={() => setActivePage("employees")}
            />
          )}
        </div>
        <footer className="page-footer">ACME salary management <span>·</span> Assessment demo</footer>
      </main>
    </div>
  );
}
