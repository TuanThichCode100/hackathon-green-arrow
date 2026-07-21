"""Build Điện Biên's 2025 commune boundaries from pre-merger GADM polygons.

The merge groups are transcribed from Resolution 1661/NQ-UBTVQH15. The
geometry source is GADM 4.1 level 3 (Vietnam), downloaded separately from:
https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_VNM_3.json.zip

Usage:
    python data/build_dien_bien_admin_2025.py path/to/gadm41_VNM_3.json
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import unicodedata
from pathlib import Path

from shapely.geometry import mapping, shape
from shapely.ops import unary_union
from shapely.validation import make_valid


MERGES: list[tuple[str, str, list[str]]] = [
    ("Mường Nhé", "xã", ["Nậm Vì", "Chung Chải", "Mường Nhé"]),
    ("Sín Thầu", "xã", ["Sen Thượng", "Leng Su Sìn", "Sín Thầu"]),
    ("Mường Toong", "xã", ["Huổi Lếch", "Mường Toong"]),
    ("Nậm Kè", "xã", ["Pá Mỳ", "Nậm Kè"]),
    ("Quảng Lâm", "xã", ["Na Cô Sa", "Quảng Lâm"]),
    ("Nà Hỳ", "xã", ["Nà Khoa", "Nậm Nhừ", "Nậm Chua", "Nà Hỳ"]),
    ("Mường Chà", "xã", ["Chà Cang", "Chà Nưa", "Nậm Tin", "Pa Tần"]),
    ("Nà Bủng", "xã", ["Vàng Đán", "Nà Bủng"]),
    ("Chà Tở", "xã", ["Nậm Khăn", "Chà Tở"]),
    ("Si Pa Phìn", "xã", ["Phìn Hồ", "Si Pa Phìn"]),
    ("Na Sang", "xã", ["Mường Chà", "Ma Thì Hồ", "Sa Lông", "Na Sang"]),
    ("Mường Tùng", "xã", ["Huổi Lèng", "Mường Tùng"]),
    ("Pa Ham", "xã", ["Hừa Ngài", "Pa Ham"]),
    ("Nậm Nèn", "xã", ["Huổi Mí", "Nậm Nèn"]),
    ("Mường Pồn", "xã", ["Mường Mươn", "Mường Pồn"]),
    ("Tủa Chùa", "xã", ["Tủa Chùa", "Mường Báng", "Nà Tòng"]),
    ("Sín Chải", "xã", ["Tả Sìn Thàng", "Lao Xả Phình", "Sín Chải"]),
    ("Sính Phình", "xã", ["Trung Thu", "Tả Phìn", "Sính Phình"]),
    ("Tủa Thàng", "xã", ["Huổi Só", "Tủa Thàng"]),
    ("Sáng Nhè", "xã", ["Xá Nhè", "Mường Đun", "Phình Sáng"]),
    ("Tuần Giáo", "xã", ["Tuần Giáo", "Quài Cang", "Quài Nưa"]),
    ("Quài Tở", "xã", ["Tỏa Tình", "Tênh Phông", "Quài Tở"]),
    ("Mường Mùn", "xã", ["Mùn Chung", "Pú Xi", "Mường Mùn"]),
    ("Pú Nhung", "xã", ["Rạng Đông", "Ta Ma", "Pú Nhung"]),
    ("Chiềng Sinh", "xã", ["Nà Sáy", "Mường Thín", "Mường Khong", "Chiềng Sinh"]),
    ("Mường Ảng", "xã", ["Mường Ảng", "Ẳng Nưa", "Ẳng Cang"]),
    ("Nà Tấu", "xã", ["Mường Đăng", "Ngối Cáy", "Nà Tấu"]),
    ("Búng Lao", "xã", ["Ẳng Tở", "Chiềng Đông", "Búng Lao"]),
    ("Mường Lạn", "xã", ["Nặm Lịch", "Xuân Lao", "Mường Lạn"]),
    ("Mường Phăng", "xã", ["Nà Nhạn", "Pá Khoang", "Mường Phăng"]),
    ("Thanh Nưa", "xã", ["Hua Thanh", "Thanh Luông", "Thanh Hưng", "Thanh Chăn", "Thanh Nưa"]),
    ("Thanh An", "xã", ["Noong Hẹt", "Sam Mứn", "Thanh An"]),
    ("Thanh Yên", "xã", ["Noong Luống", "Pa Thơm", "Thanh Yên"]),
    ("Sam Mứn", "xã", ["Pom Lót", "Na Ư"]),
    ("Núa Ngam", "xã", ["Hẹ Muông", "Na Tông", "Núa Ngam"]),
    ("Mường Nhà", "xã", ["Mường Lói", "Phu Luông", "Mường Nhà"]),
    ("Na Son", "xã", ["Điện Biên Đông", "Keo Lôm", "Na Son"]),
    ("Xa Dung", "xã", ["Phì Nhừ", "Xa Dung"]),
    ("Pu Nhi", "xã", ["Nong U", "Pu Nhi"]),
    ("Mường Luân", "xã", ["Chiềng Sơ", "Luân Giói", "Mường Luân"]),
    ("Tìa Dình", "xã", ["Háng Lìa", "Tìa Dình"]),
    ("Phình Giàng", "xã", ["Pú Hồng", "Phình Giàng"]),
    ("Mường Lay", "phường", ["Sông Đà", "Na Lay", "Lay Nưa", "Sá Tổng"]),
    (
        "Điện Biên Phủ",
        "phường",
        ["Him Lam", "Tân Thanh", "Mường Thanh", "Thanh Bình", "Thanh Trường", "Thanh Minh"],
    ),
    ("Mường Thanh", "phường", ["Noong Bua", "Nam Thanh", "Thanh Xương"]),
]

# GADM 4.1 contains a handful of legacy/alternate spellings. It also predates
# the 2020 merger of Tà Lèng into Thanh Minh, so that polygon must follow
# Thanh Minh into the new Điện Biên Phủ ward.
SOURCE_NAME_ALIASES = {
    "Huổi Lếch": "Huổi Lếnh",
    "Sín Chải": "Xín Chải",
    "Xá Nhè": "Sáng Nhè",
    "Sá Tổng": "Xá Tổng",
}
PRIOR_MERGER_GEOMETRY = {"Điện Biên Phủ": ["Tà Lèng"]}


def normalize(value: str) -> str:
    value = "".join(
        char
        for char in unicodedata.normalize("NFD", value)
        if unicodedata.category(char) != "Mn"
    )
    return re.sub(r"[^a-z0-9]", "", value.lower().replace("đ", "d"))


def compact(value: str) -> str:
    return re.sub(r"[\W_]", "", value.casefold(), flags=re.UNICODE)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("gadm", type=Path, help="Extracted gadm41_VNM_3.json")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("frontend/public/dien-bien-communes.geojson"),
    )
    parser.add_argument(
        "--mapping-output",
        type=Path,
        default=Path("data/dien_bien_admin_2025_mapping.csv"),
    )
    args = parser.parse_args()

    source = json.loads(args.gadm.read_text(encoding="utf-8"))
    dien_bien = [
        feature
        for feature in source["features"]
        if normalize(feature["properties"]["NAME_1"]) == "dienbien"
    ]

    by_name: dict[str, list[dict]] = {}
    by_exact_name: dict[str, list[dict]] = {}
    for feature in dien_bien:
        by_name.setdefault(normalize(feature["properties"]["NAME_3"]), []).append(feature)
        by_exact_name.setdefault(compact(feature["properties"]["NAME_3"]), []).append(feature)

    result = []
    used_ids: set[str] = set()
    missing: list[str] = []

    for index, (new_name, unit_type, old_names) in enumerate(MERGES, start=1):
        members = []
        geometry_names = old_names + PRIOR_MERGER_GEOMETRY.get(new_name, [])
        for old_name in geometry_names:
            source_name = SOURCE_NAME_ALIASES.get(old_name, old_name)
            candidates = by_exact_name.get(compact(source_name), [])
            if not candidates:
                candidates = by_name.get(normalize(source_name), [])
            available = [
                feature
                for feature in candidates
                if feature["properties"]["GID_3"] not in used_ids
            ]
            if len(available) > 1 and members:
                member_districts = {
                    normalize(member["properties"]["NAME_2"]) for member in members
                }
                same_district = [
                    feature
                    for feature in available
                    if normalize(feature["properties"]["NAME_2"]) in member_districts
                ]
                if len(same_district) == 1:
                    available = same_district
            if len(available) != 1:
                missing.append(
                    f"{new_name}: {old_name} (matches={len(available)}, total={len(candidates)})"
                )
                continue
            member = available[0]
            members.append(member)
            used_ids.add(member["properties"]["GID_3"])

        if len(members) != len(geometry_names):
            continue

        geometry = unary_union([make_valid(shape(member["geometry"])) for member in members])
        geometry = make_valid(geometry)
        result.append(
            {
                "type": "Feature",
                "properties": {
                    "admin_code": f"DB-{index:02d}",
                    "name": new_name,
                    "unit_type": unit_type,
                    "former_units": old_names,
                    "source": "GADM 4.1 + Resolution 1661/NQ-UBTVQH15",
                    # Compatibility with the existing Leaflet component.
                    "FID": index,
                    "NAME_1": "Điện Biên",
                    "NAME_3": new_name,
                    "TYPE_3": unit_type.capitalize(),
                },
                "geometry": mapping(geometry),
            }
        )

    unused = [
        feature["properties"]["NAME_3"]
        for feature in dien_bien
        if feature["properties"]["GID_3"] not in used_ids
    ]
    if missing or unused or len(result) != 45:
        raise RuntimeError(
            json.dumps(
                {
                    "source_features": len(dien_bien),
                    "result_features": len(result),
                    "missing_or_ambiguous": missing,
                    "unused_source_features": sorted(unused),
                },
                ensure_ascii=False,
                indent=2,
            )
        )

    collection = {
        "type": "FeatureCollection",
        "name": "Điện Biên — đơn vị hành chính cấp xã từ 01/07/2025",
        "metadata": {
            "effective_date": "2025-07-01",
            "resolution": "1661/NQ-UBTVQH15",
            "geometry_source": "GADM 4.1 level 3",
            "feature_count": 45,
        },
        "features": result,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(collection, ensure_ascii=False, separators=(",", ":")),
        encoding="utf-8",
    )
    args.mapping_output.parent.mkdir(parents=True, exist_ok=True)
    with args.mapping_output.open("w", encoding="utf-8-sig", newline="") as stream:
        writer = csv.writer(stream)
        writer.writerow(
            ["admin_code", "new_name", "unit_type", "former_units", "effective_date", "resolution"]
        )
        for feature in result:
            properties = feature["properties"]
            writer.writerow(
                [
                    properties["admin_code"],
                    properties["name"],
                    properties["unit_type"],
                    " | ".join(properties["former_units"]),
                    "2025-07-01",
                    "1661/NQ-UBTVQH15",
                ]
            )
    print(f"Wrote {len(result)} valid features to {args.output}")


if __name__ == "__main__":
    main()
