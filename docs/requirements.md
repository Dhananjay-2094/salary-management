# ACME Salary Management — Requirements

## Goal and user

Replace spreadsheet-based salary tracking for ACME’s 10,000 employees across multiple countries with a simple web application. The primary user is an HR manager who needs to maintain employee and salary records and answer basic questions about compensation.

## Scope and features

- **Employee directory:** browse employees with server-side search, country and department filters, and pagination; open an employee profile.
- **Employee records:** create an employee and update their profile details, including employee number, name, email, country, department, job title, and hire date.
- **Salary records:** add a salary amount with currency and effective date; view the employee’s salary history and identify the latest effective record.
- **Compensation overview:** view headcount and salary summaries, including min/average/max salary, grouped by currency and broken down by country and department. Currency must remain visible; amounts in different currencies must never be combined into one statistic.
- **Usable feedback:** show loading, empty, validation, success, and error states in the interface.
- **Demo data:** provide a repeatable seed command for exactly 10,000 synthetic employees, with salary data and enough variation to exercise search, filters, history, and summaries.

## Assumptions and constraints

- This is an assessment demo for one trusted HR manager. **Authentication and role management are out of scope**; there is no login flow.
- The backend uses Python, the database uses SQLite, and the frontend uses React, as required by the assignment.
- Seeded records are synthetic and must not represent real employees.
- Salary changes are represented as effective-dated records so prior values remain visible. A correction in the demo is added as a new record.
- Compensation summaries are grouped by currency. No foreign exchange conversion is performed.

## Deliberately out of scope

- Payroll runs, salary payments, tax calculations, benefits, and accounting integrations: these are separate workflows and are not needed to manage records or demonstrate compensation insights.
- Excel import/export: prioritize correct employee and salary workflows; a validated import can be considered after the core app is complete.
- Foreign exchange rates and cross-currency totals: rates require a source and effective-date policy; presenting an unsupported conversion could mislead.
- Authentication, multi-role permissions, and enterprise identity integration: no access-control behavior is required to demonstrate this single-user assignment.
- Microservices or a distributed database: a small Python service and SQLite keep the assessment solution straightforward to run. Deployment documentation should note the need for persistent storage for the SQLite file.

## Acceptance criteria

1. A fresh local setup can initialize the SQLite database, start the Python API and React UI, and load the application using documented instructions.
2. The seed command creates exactly 10,000 synthetic employees and salary records reproducibly.
3. The HR user can search, filter, and paginate the directory, then open an employee profile.
4. The HR user can create an employee, edit profile details, add an effective-dated salary record, and view salary history.
5. The overview reports headcount and compensation summaries by currency, with breakdowns by country and department; it never combines unlike currencies.
6. Core validation, employee/salary workflows, and analytics have fast, deterministic automated tests.
7. The README explains setup, seeding, running, and testing. The submitted solution includes a deployed demo and a short video walkthrough, or clearly documents any hosting limitation.
