import json
import pytest
from cli.storage import Storage
from cli.regions import RegionResolver


@pytest.fixture
def db(tmp_path):
    s = Storage(str(tmp_path / "test.db"))
    s.init_db()
    yield s
    s.close()


@pytest.fixture
def resolver(db):
    return RegionResolver(db)


class TestRegionResolver:
    def test_apply_mapping_populates_db(self, resolver, db):
        mapping_json = json.dumps({
            "version": 1,
            "provinces": {"1": "北京", "2": "上海"},
            "cities": {"101": "北京市", "201": "上海市"},
            "province_city": {"1": [101], "2": [201]},
        })
        resolver.apply_mapping(mapping_json)
        assert db.get_region(1)["name"] == "北京"
        assert db.get_region(101)["name"] == "北京市"
        assert db.get_region(101)["parent_code"] == 1
        assert db.get_config("region_version") == "1"

    def test_apply_mapping_skips_older_version(self, resolver, db):
        v2 = json.dumps({
            "version": 2,
            "provinces": {"1": "北京"},
            "cities": {},
            "province_city": {},
        })
        v1 = json.dumps({
            "version": 1,
            "provinces": {"1": "旧北京"},
            "cities": {},
            "province_city": {},
        })
        resolver.apply_mapping(v2)
        resolver.apply_mapping(v1)  # should be ignored
        assert db.get_region(1)["name"] == "北京"

    def test_resolve_province_name_to_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {"1": "北京"},
            "cities": {},
            "province_city": {},
        }))
        assert resolver.province_code("北京") == 1
        assert resolver.province_code("不存在") is None

    def test_resolve_city_name_to_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {},
            "cities": {"101": "北京市"},
            "province_city": {},
        }))
        assert resolver.city_code("北京市") == 101
        assert resolver.city_code("不存在") is None

    def test_province_name_from_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {"1": "北京"},
            "cities": {},
            "province_city": {},
        }))
        assert resolver.province_name(1) == "北京"
        assert resolver.province_name(999) is None

    def test_city_name_from_code(self, resolver):
        resolver.apply_mapping(json.dumps({
            "version": 1,
            "provinces": {},
            "cities": {"101": "北京市"},
            "province_city": {},
        }))
        assert resolver.city_name(101) == "北京市"
        assert resolver.city_name(999) is None
