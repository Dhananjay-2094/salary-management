import { useEffect, useState } from "react";
import { addSalaryRecord, getEmployee } from "../api/client.js";
import EmployeeForm from "./EmployeeForm.jsx";

function formatSalary(salary) {
  if (!salary) return "No salary recorded";
  try {
    const formatter = new Intl.NumberFormat(undefined, { style: "currency", currency: salary.currency_code });
    const digits = formatter.resolvedOptions().maximumFractionDigits;
    return formatter.format(salary.amount_minor / 10 ** digits);
  } catch {
    return `${salary.amount_minor.toLocaleString()} ${salary.currency_code}`;
  }
}

function formatDate(value) {
  return new Intl.DateTimeFormat(undefined, {
    day: "numeric", month: "short", year: "numeric", timeZone: "UTC",
  }).format(new Date(`${value}T00:00:00Z`));
}

function minorUnitAmount(value, currency) {
  if (!/^\d+(\.\d*)?$/.test(value.trim())) throw new Error("Enter a valid positive salary amount.");
  let formatter;
  try {
    formatter = new Intl.NumberFormat(undefined, { style: "currency", currency });
  } catch {
    throw new Error("Enter a valid three-letter currency code, such as USD.");
  }
  const digits = formatter.resolvedOptions().maximumFractionDigits;
  const [whole, fraction = ""] = value.trim().split(".");
  if (fraction.length > digits) {
    throw new Error(`${currency} allows up to ${digits} decimal places.`);
  }
  const scale = 10n ** BigInt(digits);
  const minor = BigInt(whole) * scale + BigInt(fraction.padEnd(digits, "0") || "0");
  if (minor <= 0n || minor > 1_000_000_000_000n) {
    throw new Error("Salary must be positive and within the supported limit.");
  }
  return Number(minor);
}

function initialEffectiveDate(minimumDate) {
  const today = new Date().toISOString().slice(0, 10);
  return minimumDate && minimumDate > today ? minimumDate : today;
}

function SalaryForm({ employeeId, minimumDate, onSaved, onCancel }) {
  const [amount, setAmount] = useState("");
  const [currency, setCurrency] = useState("USD");
  const [effectiveDate, setEffectiveDate] = useState(() => initialEffectiveDate(minimumDate));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  async function submit(event) {
    event.preventDefault();
    setError("");
    let amountMinor;
    try {
      amountMinor = minorUnitAmount(amount, currency.trim().toUpperCase());
    } catch (validationError) {
      setError(validationError.message);
      return;
    }

    setSaving(true);
    try {
      await addSalaryRecord(employeeId, {
        amount_minor: amountMinor,
        currency_code: currency.trim().toUpperCase(),
        effective_date: effectiveDate,
      });
      await onSaved();
    } catch (requestError) {
      setError(requestError.message || "We couldn’t add this salary record.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form-stack salary-form" onSubmit={submit}>
      <div className="salary-form__grid">
        <label className="form-field">
          <span>Annual salary</span>
          <input type="text" inputMode="decimal" placeholder="e.g. 85000.00" value={amount}
            onChange={(event) => setAmount(event.target.value)} required />
        </label>
        <label className="form-field">
          <span>Currency code</span>
          <input type="text" inputMode="text" autoCapitalize="characters" maxLength="3"
            pattern="[A-Za-z]{3}" title="Enter a three-letter currency code, such as USD."
            value={currency} onChange={(event) => setCurrency(event.target.value.toUpperCase())} required />
        </label>
        <label className="form-field">
          <span>Effective date</span>
          <input type="date" min={minimumDate} value={effectiveDate} onChange={(event) => setEffectiveDate(event.target.value)} required />
        </label>
      </div>
      <p className="form-hint">Enter the annual amount in major currency units. A new record is added to salary history.</p>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-actions">
        <button className="button-secondary" type="button" onClick={onCancel} disabled={saving}>Cancel</button>
        <button className="button-primary" type="submit" disabled={saving}>{saving ? "Saving…" : "Add salary record"}</button>
      </div>
    </form>
  );
}

export default function EmployeeDetails({ employeeId, onBack }) {
  const [employee, setEmployee] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [editing, setEditing] = useState(false);
  const [addingSalary, setAddingSalary] = useState(false);
  const [reload, setReload] = useState(0);

  useEffect(() => {
    const controller = new AbortController();
    setLoading(true);
    setError("");
    getEmployee(employeeId, { signal: controller.signal })
      .then((data) => setEmployee(data))
      .catch((requestError) => {
        if (requestError.name !== "AbortError") setError(requestError.message);
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false);
      });
    return () => controller.abort();
  }, [employeeId, reload]);

  if (loading) return <div className="directory-state" role="status">Loading employee profile…</div>;
  if (error) {
    return (
      <div className="directory-state directory-state--error" role="alert">
        <strong>We couldn’t load this employee.</strong><span>{error}</span>
        <button type="button" onClick={() => setReload((value) => value + 1)}>Try again</button>
        <button className="button-secondary" type="button" onClick={onBack}>Back to employees</button>
      </div>
    );
  }
  if (!employee) return null;

  const refresh = () => setReload((value) => value + 1);

  return (
    <section className="employee-detail" aria-labelledby="employee-detail-name">
      <button className="back-link" type="button" onClick={onBack}>‹ <span>All employees</span></button>
      <div className="employee-detail__heading">
        <div>
          <div className="section-eyebrow">EMPLOYEE PROFILE</div>
          <h2 id="employee-detail-name">{employee.name}</h2>
          <p>{employee.job_title} <span>·</span> {employee.department}</p>
        </div>
        <button className="button-secondary" type="button" onClick={() => setEditing(true)}>Edit profile</button>
      </div>

      <div className="detail-grid">
        <section className="detail-card" aria-labelledby="profile-card-title">
          <div className="detail-card__heading"><h3 id="profile-card-title">Profile details</h3><span className="employee-number">{employee.employee_number}</span></div>
          <dl className="profile-list">
            <div><dt>Email</dt><dd>{employee.email}</dd></div>
            <div><dt>Country</dt><dd>{employee.country}</dd></div>
            <div><dt>Department</dt><dd>{employee.department}</dd></div>
            <div><dt>Job title</dt><dd>{employee.job_title}</dd></div>
            <div><dt>Hire date</dt><dd>{formatDate(employee.hire_date)}</dd></div>
          </dl>
        </section>
        <section className="detail-card salary-summary-card" aria-labelledby="current-salary-title">
          <div className="detail-card__heading"><h3 id="current-salary-title">Current salary</h3><span className="status-pill">Latest effective record</span></div>
          <div className="current-salary">{formatSalary(employee.latest_salary)}</div>
          {employee.latest_salary ? (
            <p>Effective {formatDate(employee.latest_salary.effective_date)}</p>
          ) : (
            <p>No salary record has been added yet.</p>
          )}
          <button className="button-primary" type="button" onClick={() => setAddingSalary(true)}>
            {employee.latest_salary ? "Add salary change" : "Add first salary"}
          </button>
        </section>
      </div>

      <section className="detail-card history-card" aria-labelledby="salary-history-title">
        <div className="detail-card__heading">
          <div><h3 id="salary-history-title">Salary history</h3><p>Effective-dated salary records, newest first.</p></div>
          <span className="history-count">{employee.salary_history.length} {employee.salary_history.length === 1 ? "record" : "records"}</span>
        </div>
        {employee.salary_history.length === 0 ? (
          <div className="history-empty">Salary history will appear here after the first record is added.</div>
        ) : (
          <div className="history-table-wrap">
            <table className="history-table">
              <thead><tr><th scope="col">Effective date</th><th scope="col">Annual salary</th><th scope="col">Currency</th><th scope="col">Record</th></tr></thead>
              <tbody>{employee.salary_history.map((record, index) => (
                <tr key={record.id}>
                  <td>{formatDate(record.effective_date)}</td>
                  <td className="salary-value">{formatSalary(record)}</td>
                  <td><span className="currency-tag">{record.currency_code}</span></td>
                  <td>{index === 0 ? <span className="current-tag">Current</span> : "Previous"}</td>
                </tr>
              ))}</tbody>
            </table>
          </div>
        )}
      </section>

      {editing && (
        <div className="modal-backdrop">
          <section className="form-modal" role="dialog" aria-modal="true" aria-labelledby="edit-employee-title">
            <div className="form-modal__heading"><div><div className="section-eyebrow">EMPLOYEE PROFILE</div><h2 id="edit-employee-title">Edit details</h2></div>
              <button className="modal-close" type="button" aria-label="Close edit form" onClick={() => setEditing(false)}>×</button>
            </div>
            <EmployeeForm mode="edit" initialValues={employee} onCancel={() => setEditing(false)} onSaved={async () => { setEditing(false); refresh(); }} />
          </section>
        </div>
      )}

      {addingSalary && (
        <div className="modal-backdrop">
          <section className="form-modal" role="dialog" aria-modal="true" aria-labelledby="add-salary-title">
            <div className="form-modal__heading"><div><div className="section-eyebrow">COMPENSATION</div><h2 id="add-salary-title">Add salary record</h2></div>
              <button className="modal-close" type="button" aria-label="Close salary form" onClick={() => setAddingSalary(false)}>×</button>
            </div>
            <SalaryForm employeeId={employee.id} minimumDate={employee.hire_date} onCancel={() => setAddingSalary(false)} onSaved={async () => { setAddingSalary(false); refresh(); }} />
          </section>
        </div>
      )}
    </section>
  );
}
