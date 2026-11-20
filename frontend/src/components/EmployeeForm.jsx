import { useState } from "react";
import { createEmployee, updateEmployee } from "../api/client.js";

const profileFields = [
  { key: "employee_number", label: "Employee number", type: "text", maxLength: 40, createOnly: true },
  { key: "name", label: "Full name", type: "text", maxLength: 160 },
  { key: "email", label: "Work email", type: "email", maxLength: 254 },
  { key: "country", label: "Country", type: "text", maxLength: 100 },
  { key: "department", label: "Department", type: "text", maxLength: 100 },
  { key: "job_title", label: "Job title", type: "text", maxLength: 120 },
  { key: "hire_date", label: "Hire date", type: "date" },
];

export default function EmployeeForm({ mode, initialValues = {}, onSaved, onCancel }) {
  const isCreate = mode === "create";
  const [values, setValues] = useState(() => Object.fromEntries(
    profileFields
      .filter((field) => isCreate || !field.createOnly)
      .map((field) => [field.key, initialValues[field.key] ?? ""]),
  ));
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");

  function updateField(key, value) {
    setValues((current) => ({ ...current, [key]: value }));
  }

  async function submit(event) {
    event.preventDefault();
    setSaving(true);
    setError("");
    try {
      const employee = isCreate
        ? await createEmployee(values)
        : await updateEmployee(initialValues.id, values);
      await onSaved(employee);
    } catch (requestError) {
      setError(requestError.message || "We couldn’t save this employee.");
    } finally {
      setSaving(false);
    }
  }

  return (
    <form className="form-stack" onSubmit={submit}>
      <div className="form-grid">
        {profileFields.filter((field) => isCreate || !field.createOnly).map((field) => (
          <label className="form-field" key={field.key}>
            <span>{field.label}</span>
            <input
              autoComplete={field.key === "email" ? "email" : field.key === "name" ? "name" : "off"}
              type={field.type}
              value={values[field.key]}
              onChange={(event) => updateField(field.key, event.target.value)}
              required
              maxLength={field.maxLength}
            />
          </label>
        ))}
      </div>
      {error && <p className="form-error" role="alert">{error}</p>}
      <div className="form-actions">
        <button className="button-secondary" type="button" onClick={onCancel} disabled={saving}>Cancel</button>
        <button className="button-primary" type="submit" disabled={saving}>
          {saving ? "Saving…" : isCreate ? "Create employee" : "Save changes"}
        </button>
      </div>
    </form>
  );
}
