# Employee API

The local API runs at `http://127.0.0.1:8000`. Interactive OpenAPI documentation is available at `/docs`.

## Employee directory

`GET /api/employees?search=lee&country=India&department=Engineering&page=1&page_size=25`

All query parameters are optional. Search checks employee name, email, and employee number. Page numbers start at 1; page size is limited to 100. Response:

```json
{
  "items": [
    {
      "id": 1,
      "employee_number": "AC-1001",
      "name": "Jordan Lee",
      "email": "jordan.lee@example.test",
      "country": "India",
      "department": "Engineering",
      "job_title": "Software Engineer",
      "hire_date": "2024-03-15",
      "latest_salary": {
        "id": 14,
        "employee_id": 1,
        "amount_minor": 8250000,
        "currency_code": "INR",
        "effective_date": "2025-04-01"
      }
    }
  ],
  "page": 1,
  "page_size": 25,
  "total": 1
}
```

Employees without a salary record have `latest_salary: null`. `GET /api/employees/filters` returns distinct `countries` and `departments` for filter controls.

## Create and update employee

`POST /api/employees` accepts all profile fields: `employee_number`, `name`, `email`, `country`, `department`, `job_title`, and ISO `hire_date`. It returns the created profile with `201 Created`. Duplicate employee number or email returns `409 Conflict`.

`PATCH /api/employees/{id}` accepts one or more editable fields: `name`, `email`, `country`, `department`, `job_title`, or `hire_date`. An empty patch or explicit null is invalid. Duplicate email returns `409 Conflict`; an unknown employee returns `404 Not Found`.

## Employee detail and salary history

`GET /api/employees/{id}` returns the profile plus `latest_salary` (or null) and `salary_history`, ordered by effective date descending, then record ID descending. `GET /api/employees/{id}/salaries` returns that history as a list. Both return `404 Not Found` for an unknown employee.

`POST /api/employees/{id}/salaries` accepts `amount_minor` (positive integer in the currency's minor unit), uppercase three-letter `currency_code`, and ISO `effective_date`. It appends a salary record and returns it with `201 Created`. Records are retained as history; the newest effective date (then highest ID) is treated as current.

## Compensation analytics

`GET /api/analytics/summary` returns organization headcount, headcount by country and department, and salary statistics for current salary records grouped by currency, country plus currency, and department plus currency. Each compensation group includes employee count and average/minimum/maximum salary in minor units. Average values are rounded to the nearest minor unit, with half values rounded up. Employees without a salary record count toward headcount but not compensation statistics. Different currencies are never combined.
