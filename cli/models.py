"""Data models for job content and region mapping."""

import json
from dataclasses import dataclass, field


_JOB_KNOWN_FIELDS = {"title", "company", "salary_range", "description", "contact", "version"}


@dataclass
class JobContent:
    title: str
    company: str
    version: int = 1
    salary_range: str = ""
    description: str = ""
    contact: str = ""
    extra: dict = field(default_factory=dict)

    def to_json(self) -> str:
        data = {
            "title": self.title,
            "company": self.company,
            "version": self.version,
        }
        if self.salary_range:
            data["salary_range"] = self.salary_range
        if self.description:
            data["description"] = self.description
        if self.contact:
            data["contact"] = self.contact
        data.update(self.extra)
        return json.dumps(data, ensure_ascii=False)


def parse_job_content(raw_json: str) -> JobContent:
    data = json.loads(raw_json)
    if "title" not in data:
        raise ValueError("missing required field: title")
    if "company" not in data:
        raise ValueError("missing required field: company")
    extra = {k: v for k, v in data.items() if k not in _JOB_KNOWN_FIELDS}
    return JobContent(
        title=data["title"],
        company=data["company"],
        version=data.get("version", 1),
        salary_range=data.get("salary_range", ""),
        description=data.get("description", ""),
        contact=data.get("contact", ""),
        extra=extra,
    )


@dataclass
class RegionMapping:
    version: int
    provinces: dict[str, str]  # code -> name
    cities: dict[str, str]  # code -> name
    province_city: dict[str, list[int]]  # province_code -> [city_codes]

    def province_name_to_code(self, name: str) -> int | None:
        for code, n in self.provinces.items():
            if n == name:
                return int(code)
        return None

    def city_name_to_code(self, name: str) -> int | None:
        for code, n in self.cities.items():
            if n == name:
                return int(code)
        return None


def parse_region_mapping(raw_json: str) -> RegionMapping:
    data = json.loads(raw_json)
    return RegionMapping(
        version=data["version"],
        provinces=data.get("provinces", {}),
        cities=data.get("cities", {}),
        province_city=data.get("province_city", {}),
    )
