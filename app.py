from __future__ import annotations

import csv
import json
import math
import os
from dataclasses import dataclass, asdict
from functools import lru_cache
from typing import Iterable, List, Optional, Tuple

from flask import Flask, jsonify, request, render_template


# -----------------------------
# データモデル
# -----------------------------


@dataclass
class Shelter:
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    notes: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "name": self.name,
            "address": self.address,
            "lat": self.latitude,
            "lon": self.longitude,
            "notes": self.notes,
        }


# -----------------------------
# ヘルパー
# -----------------------------


def _safe_float(value: str) -> Optional[float]:
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two lat/lon points in kilometers."""
    radius_km = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(min(1.0, math.sqrt(a)))
    return radius_km * c


def _csv_path_candidates() -> List[str]:
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return [
        os.path.join(repo_root, "mergeFromCity_2.csv"),
        os.path.join(repo_root, "13121_2.csv"),
    ]


def _detect_csv_path() -> str:
    for path in _csv_path_candidates():
        if os.path.exists(path):
            return path
    raise FileNotFoundError(
        "CSV file not found. Expected one of: " + ", ".join(_csv_path_candidates())
    )


def _parse_row_13121(row: dict) -> Optional[Shelter]:
    # ヘッダーの例:
    # NO,共通ID,施設・場所名,住所,洪水,崖崩れ、土石流及び地滑り,高潮,地震,津波,大規模な火事,内水氾濫,火山現象,指定避難所との住所同一,緯度,経度,備考
    lat = _safe_float(row.get("緯度"))
    lon = _safe_float(row.get("経度"))
    if lat is None or lon is None:
        return None
    return Shelter(
        id=(row.get("共通ID") or ""),
        name=(row.get("施設・場所名") or "不明"),
        address=(row.get("住所") or ""),
        latitude=lat,
        longitude=lon,
        notes=(row.get("備考") or ""),
    )


def _parse_row_merge(row: dict) -> Optional[Shelter]:
    # フォールバックとして一般的な英語ライクなヘッダーを試す
    lat = _safe_float(row.get("lat") or row.get("latitude") or row.get("緯度"))
    lon = _safe_float(row.get("lon") or row.get("lng") or row.get("longitude") or row.get("経度"))
    name = row.get("name") or row.get("施設・場所名") or row.get("place")
    address = row.get("address") or row.get("住所")
    if lat is None or lon is None:
        return None
    return Shelter(
        id=(row.get("id") or row.get("共通ID") or ""),
        name=(name or "不明"),
        address=(address or ""),
        latitude=lat,
        longitude=lon,
        notes=(row.get("備考") or ""),
    )


def _choose_parser(header: List[str]):
    header_str = ",".join(header)
    if "施設・場所名" in header_str and "緯度" in header_str and "経度" in header_str:
        return _parse_row_13121
    return _parse_row_merge


@lru_cache(maxsize=1)
def load_shelters() -> List[Shelter]:
    csv_path = _detect_csv_path()
    with open(csv_path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        parser = _choose_parser(reader.fieldnames or [])
        shelters: List[Shelter] = []
        for row in reader:
            shelter = parser(row)
            if shelter is not None:
                shelters.append(shelter)
    return shelters


def sort_by_distance(lat: float, lon: float, shelters: Iterable[Shelter]) -> List[Tuple[Shelter, float]]:
    result: List[Tuple[Shelter, float]] = []
    for shelter in shelters:
        distance_km = haversine_km(lat, lon, shelter.latitude, shelter.longitude)
        result.append((shelter, distance_km))
    result.sort(key=lambda pair: pair[1])
    return result


# -----------------------------
# Flask app
# -----------------------------


def create_app() -> Flask:
    # static_url_path を空文字にしないことで、アプリをサブパスに載せる際も相対参照で解決可能
    app = Flask(__name__, static_folder="static", template_folder="templates")

    # Basic CORS for simple GET requests
    @app.after_request
    def add_cors_headers(response):
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type"
        # Light caching for read-only resources
        if request.method == "GET":
            response.headers.setdefault("Cache-Control", "public, max-age=60")
        return response

    @app.get("/")
    def home():
        google_api_key = os.environ.get(AIzaSyBsLZDipt1qz8E8_fmKmPDtZ_N9AOsqgQc) or os.environ.get(AIzaSyBsLZDipt1qz8E8_fmKmPDtZ_N9AOsqgQc) or ""
        zip_supported = bool(google_api_key)
        return render_template("index.html", zip_supported=zip_supported, google_api_key=google_api_key)

    @app.get("/health")
    def health():
        return jsonify({"status": "ok"})

    @app.get("/shelters")
    def list_shelters():
        all_items = load_shelters()

        # Filters
        q = (request.args.get("q") or "").strip()
        bbox = (request.args.get("bbox") or "").strip()

        filtered = all_items
        applied_filters = {}

        if q:
            q_lower = q.lower()
            filtered = [
                s for s in filtered
                if (s.name and q_lower in s.name.lower())
                or (s.address and q_lower in s.address.lower())
            ]
            applied_filters["q"] = q

        if bbox:
            parts = [p.strip() for p in bbox.split(",") if p.strip()]
            if len(parts) != 4:
                return jsonify({"error": "bbox must be 'minLon,minLat,maxLon,maxLat'"}), 400
            try:
                min_lon, min_lat, max_lon, max_lat = map(float, parts)
            except ValueError:
                return jsonify({"error": "bbox values must be numbers"}), 400
            if min_lat > max_lat or min_lon > max_lon:
                return jsonify({"error": "bbox min must be <= max"}), 400
            filtered = [
                s for s in filtered
                if (min_lat <= s.latitude <= max_lat) and (min_lon <= s.longitude <= max_lon)
            ]
            applied_filters["bbox"] = bbox

        total = len(filtered)

        # ページネーション
        limit_param = request.args.get("limit", "100")
        offset_param = request.args.get("offset", "0")
        try:
            limit = max(1, min(500, int(limit_param)))
        except ValueError:
            limit = 100
        try:
            offset = max(0, int(offset_param))
        except ValueError:
            offset = 0

        page_items = filtered[offset: offset + limit]
        data = [s.to_dict() for s in page_items]

        return jsonify({
            "total": total,
            "count": len(data),
            "offset": offset,
            "limit": limit,
            "appliedFilters": applied_filters,
            "items": data,
        })

    @app.get("/nearest")
    def nearest():
        try:
            lat = float(request.args.get("lat", ""))
            lon = float(request.args.get("lon", ""))
        except ValueError:
            return jsonify({"error": "lat and lon must be numbers"}), 400

        if not (-90.0 <= lat <= 90.0 and -180.0 <= lon <= 180.0):
            return jsonify({"error": "lat must be in [-90,90], lon in [-180,180]"}), 400

        limit_param = request.args.get("limit") or request.args.get("n") or "5"
        try:
            limit = max(1, min(50, int(limit_param)))
        except ValueError:
            limit = 5

        sorted_pairs = sort_by_distance(lat, lon, load_shelters())
        items = [
            {**shelter.to_dict(), "distance_km": round(distance_km, 3)}
            for shelter, distance_km in sorted_pairs[:limit]
        ]
        return jsonify({
            "origin": {"lat": lat, "lon": lon},
            "limit": limit,
            "items": items,
        })

    @app.get("/nearest/by-zip")
    def nearest_by_zip():
        zip_code = (request.args.get("zip") or "").strip()
        if not zip_code or not zip_code.isdigit() or len(zip_code) != 7:
            return jsonify({"error": "zip must be 7 digits (no hyphen)"}), 400

        api_key = os.environ.get(AIzaSyBsLZDipt1qz8E8_fmKmPDtZ_N9AOsqgQc) or os.environ.get(AIzaSyBsLZDipt1qz8E8_fmKmPDtZ_N9AOsqgQc)
        if not api_key:
            return jsonify({"error": "Server missing GOOGLE_MAPS_API_KEY env var"}), 500

        import requests

        resp = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": zip_code, "key": api_key},
            timeout=10,
        )
        if resp.status_code != 200:
            return jsonify({"error": f"Geocode request failed: {resp.status_code}"}), 502

        data = resp.json()
        if data.get("status") != "OK" or not data.get("results"):
            return jsonify({"error": "Could not geocode zip"}), 404

        location = data["results"][0]["geometry"]["location"]
        lat = float(location["lat"])
        lon = float(location["lng"])

        limit_param = request.args.get("limit", "5")
        try:
            limit = max(1, min(50, int(limit_param)))
        except ValueError:
            limit = 5

        sorted_pairs = sort_by_distance(lat, lon, load_shelters())
        items = [
            {**shelter.to_dict(), "distance_km": round(distance_km, 3)}
            for shelter, distance_km in sorted_pairs[:limit]
        ]
        return jsonify({"origin": {"lat": lat, "lon": lon, "zip": zip_code}, "items": items})

    return app


app = create_app()


if __name__ == "__main__":
    # ローカル開発環境
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", "8000")), debug=True)

