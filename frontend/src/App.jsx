import { useEffect, useState } from "react";
import { getHealth } from "./api/client.js";
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
  return (
    <section className="welcome-panel">
      <div className="welcome-panel__eyebrow">WORKFORCE COMPENSATION</div>
      <h2>Your people, clearly in view.</h2>
      <p>
        A central place to maintain employee profiles, follow salary history, and understand how
        compensation is distributed across ACME.
      </p>
      <div className="welcome-panel__note">
        <span className="note-icon" aria-hidden="true">i</span>
        <span>Salary summaries will always keep currencies separate.</span>
      </div>
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
