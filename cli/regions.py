"""Province/City region resolution using local SQLite storage."""

import json
from cli.storage import Storage
from cli.models import parse_region_mapping


class RegionResolver:
    def __init__(self, storage: Storage):
        self._storage = storage

    def apply_mapping(self, mapping_json: str):
        mapping = parse_region_mapping(mapping_json)
        current_version = int(self._storage.get_config("region_version", "0"))
        if mapping.version <= current_version:
            return
        for code_str, name in mapping.provinces.items():
            self._storage.upsert_region(int(code_str), name, "province")
        for code_str, name in mapping.cities.items():
            parent = None
            for prov_code, city_codes in mapping.province_city.items():
                if int(code_str) in city_codes:
                    parent = int(prov_code)
                    break
            self._storage.upsert_region(int(code_str), name, "city", parent_code=parent)
        self._storage.set_config("region_version", str(mapping.version))

    def province_code(self, name: str) -> int | None:
        for r in self._storage.list_regions(region_type="province"):
            if r["name"] == name:
                return r["code"]
        return None

    def city_code(self, name: str) -> int | None:
        for r in self._storage.list_regions(region_type="city"):
            if r["name"] == name:
                return r["code"]
        return None

    def province_name(self, code: int) -> str | None:
        r = self._storage.get_region(code)
        return r["name"] if r and r["type"] == "province" else None

    def city_name(self, code: int) -> str | None:
        r = self._storage.get_region(code)
        return r["name"] if r and r["type"] == "city" else None
