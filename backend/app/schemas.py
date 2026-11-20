"""Validated request and response models for the HTTP API."""

from datetime import date
import re

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class APIModel(BaseModel):
    """Base API model that rejects undeclared input fields."""

    model_config = ConfigDict(extra="forbid")


class EmployeeFields(APIModel):
    employee_number: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=160)
    email: str = Field(min_length=3, max_length=254)
    country: str = Field(min_length=2, max_length=100)
    department: str = Field(min_length=1, max_length=100)
    job_title: str = Field(min_length=1, max_length=120)
    hire_date: date

    @field_validator("employee_number", "name", "country", "department", "job_title")
    @classmethod
    def strip_required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        value = value.strip()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("must be a valid email address")
        return value


class EmployeeCreate(EmployeeFields):
    """Fields required to create an employee."""


class EmployeeUpdate(APIModel):
    """Fields that can be changed on an existing employee."""

    name: str | None = Field(default=None, min_length=1, max_length=160)
    email: str | None = Field(default=None, min_length=3, max_length=254)
    country: str | None = Field(default=None, min_length=2, max_length=100)
    department: str | None = Field(default=None, min_length=1, max_length=100)
    job_title: str | None = Field(default=None, min_length=1, max_length=120)
    hire_date: date | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> "EmployeeUpdate":
        if not self.model_fields_set:
            raise ValueError("at least one field must be provided")
        if any(getattr(self, field) is None for field in self.model_fields_set):
            raise ValueError("provided fields must not be null")
        return self

    @field_validator("name", "country", "department", "job_title")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("must not be blank")
        return value

    @field_validator("email")
    @classmethod
    def validate_optional_email(cls, value: str | None) -> str | None:
        if value is None:
            return value
        value = value.strip()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", value):
            raise ValueError("must be a valid email address")
        return value


class SalaryRecordCreate(APIModel):
    """Salary amount is expressed in the currency's minor unit (e.g. cents)."""

    amount_minor: int = Field(gt=0, le=10**12)
    currency_code: str = Field(pattern=r"^[A-Z]{3}$")
    effective_date: date


class EmployeeResponse(APIModel):
    id: int
    employee_number: str
    name: str
    email: str
    country: str
    department: str
    job_title: str
    hire_date: date


class SalaryRecordResponse(APIModel):
    id: int
    employee_id: int
    amount_minor: int
    currency_code: str
    effective_date: date


class EmployeeDetailResponse(EmployeeResponse):
    latest_salary: SalaryRecordResponse | None
    salary_history: list[SalaryRecordResponse]


class EmployeeListResponse(APIModel):
    items: list[EmployeeResponse]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total: int = Field(ge=0)


class HeadcountByCountry(APIModel):
    country: str
    employee_count: int = Field(ge=0)


class HeadcountByDepartment(APIModel):
    department: str
    employee_count: int = Field(ge=0)


class CompensationByCurrency(APIModel):
    currency_code: str
    employee_count: int = Field(ge=0)
    average_salary_minor: int = Field(ge=0)
    minimum_salary_minor: int = Field(ge=0)
    maximum_salary_minor: int = Field(ge=0)


class CompensationByCountry(APIModel):
    country: str
    currency_code: str
    employee_count: int = Field(ge=0)
    average_salary_minor: int = Field(ge=0)
    minimum_salary_minor: int = Field(ge=0)
    maximum_salary_minor: int = Field(ge=0)


class CompensationByDepartment(APIModel):
    department: str
    currency_code: str
    employee_count: int = Field(ge=0)
    average_salary_minor: int = Field(ge=0)
    minimum_salary_minor: int = Field(ge=0)
    maximum_salary_minor: int = Field(ge=0)


class AnalyticsSummaryResponse(APIModel):
    headcount: int = Field(ge=0)
    headcount_by_country: list[HeadcountByCountry]
    headcount_by_department: list[HeadcountByDepartment]
    compensation_by_currency: list[CompensationByCurrency]
    compensation_by_country: list[CompensationByCountry]
    compensation_by_department: list[CompensationByDepartment]
