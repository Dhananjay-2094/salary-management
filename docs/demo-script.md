# Demo Walkthrough Script

Target length: 3–4 minutes. Use only the seeded synthetic dataset. Start with a freshly seeded local or deployed demo database, and do not show personal accounts, tokens, or real employee data in the recording.

## Walkthrough

1. **Opening (15 sec):** “This is ACME People & Pay, an HR tool for maintaining employee profiles and salary history for a 10,000-person organization. This assessment demo assumes one trusted HR user and has no login flow.”
2. **Overview (45 sec):** Show total headcount and current salary coverage. Point out average and range rows grouped by currency, then the country and department breakdowns. Explain that no cross-currency total is displayed.
3. **Find an employee (45 sec):** Open Employees. Search by an employee name or ID, filter by country and department, and show that results are paginated. Open a profile.
4. **Profile and history (45 sec):** Show employee details, latest effective salary, and prior salary records. Call out currency and effective date on every salary entry.
5. **Change a record (45 sec):** Add a salary record in a chosen currency with an effective date on or after hire date. Show it at the top of history and reflected in the directory/overview after returning.
6. **Add an employee (30 sec):** Create a clearly synthetic employee and show the profile page; optionally add their initial salary record.
7. **Close (15 sec):** Mention the Python/FastAPI backend, SQLite storage, React UI, 10,000-row deterministic seed, and automated test commands.

Before recording, verify the app is seeded and the API status indicator is connected. Capture the browser window only, keep the screen at a readable resolution, and save the final recording as `artifacts/demo.mp4` or link it from the README if the hosting platform requires an uploaded video.
