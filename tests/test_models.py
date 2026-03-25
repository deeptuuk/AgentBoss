import json
import pytest
from cli.models import JobContent, RegionMapping, parse_job_content, parse_region_mapping


class TestJobContent:
    def test_parse_valid_job(self):
        raw = json.dumps({
            "title": "Python Developer",
            "company": "SomeTech",
            "salary_range": "15k-25k",
            "description": "Build things",
            "contact": "npub1xxx",
            "version": 1,
        })
        job = parse_job_content(raw)
        assert job.title == "Python Developer"
        assert job.company == "SomeTech"
        assert job.salary_range == "15k-25k"
        assert job.version == 1

    def test_parse_job_with_extra_fields(self):
        """Forward compatibility: unknown fields are preserved"""
        raw = json.dumps({
            "title": "Dev",
            "company": "Co",
            "version": 1,
            "future_field": "value",
        })
        job = parse_job_content(raw)
        assert job.title == "Dev"
        assert job.extra["future_field"] == "value"

    def test_parse_job_missing_title_raises(self):
        raw = json.dumps({"company": "Co", "version": 1})
        with pytest.raises(ValueError):
            parse_job_content(raw)

    def test_job_to_json_roundtrip(self):
        raw = json.dumps({
            "title": "Dev",
            "company": "Co",
            "version": 1,
        })
        job = parse_job_content(raw)
        restored = parse_job_content(job.to_json())
        assert restored.title == job.title
        assert restored.company == job.company


class TestRegionMapping:
    def test_parse_valid_mapping(self):
        raw = json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {"1": [101], "2": [201]},
        })
        mapping = parse_region_mapping(raw)
        assert mapping.version == 1
        assert mapping.provinces["1"] == "北京"
        assert mapping.cities["101"] == "北京市"
        assert mapping.province_city["1"] == [101]

    def test_name_to_code_province(self):
        raw = json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {},
            "province_city": {},
        })
        mapping = parse_region_mapping(raw)
        assert mapping.province_name_to_code("北京") == 1
        assert mapping.province_name_to_code("不存在") is None

    def test_name_to_code_city(self):
        raw = json.dumps({
            "version": 1,
            "provinces": {},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {},
        })
        mapping = parse_region_mapping(raw)
        assert mapping.city_name_to_code("北京市") == 101
        assert mapping.city_name_to_code("不存在") is None
