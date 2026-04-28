"""
Task 1: Data Acquisition
Fetches 7-day weather forecast data from the CWA API (F-D0047-091)
and prints the raw JSON response for grading.

Note: CWA's certificate has a known SSL issue (Missing Subject Key Identifier).
We suppress SSL verification with verify=False as a workaround.
"""

import requests
import json
import urllib3

# Suppress the InsecureRequestWarning caused by verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── CWA API settings ──────────────────────────────────────────────────────────
API_KEY  = "CWA-73D0FFD2-E942-41BC-9024-3560C8F88588"
ENDPOINT = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/F-D0047-091"

# Region names we care about (match official CWA location names)
TARGET_REGIONS = [
    "臺北市",   # Northern
    "臺中市",   # Central
    "臺南市",   # Southern
    "宜蘭縣",   # Northeastern
    "花蓮縣",   # Eastern
    "臺東縣",   # Southeastern
]

# ── Friendly English label for each Chinese region name ───────────────────────
REGION_LABEL = {
    "臺北市": "北部地區",
    "臺中市": "中部地區",
    "臺南市": "南部地區",
    "宜蘭縣": "東北部地區",
    "花蓮縣": "東部地區",
    "臺東縣": "東南部地區",
}


def fetch_raw_data() -> dict:
    """Fetch the raw JSON from CWA and return it as a Python dict."""
    params = {
        "Authorization": API_KEY,
        "format": "JSON",
    }
    print("[INFO] Sending request to CWA API …")
    # verify=False bypasses the CWA SSL certificate issue (Missing Subject Key Identifier)
    response = requests.get(ENDPOINT, params=params, timeout=30, verify=False)
    response.raise_for_status()
    data = response.json()
    return data


def parse_records(data: dict) -> list[dict]:
    """
    Walk the CWA JSON tree and extract:
        regionName, dataDate, mint, maxt
    Returns a list of dicts (one per date per region).

    F-D0047-091 returns 12-hour time slots.  We aggregate across
    each calendar day to produce one daily min/max row.
    Value keys in ElementValue are 'MaxTemperature' / 'MinTemperature'.
    """
    records = []

    locations_wrapper = (
        data.get("records", {})
            .get("Locations", [])
    )

    for location_group in locations_wrapper:
        for location in location_group.get("Location", []):
            location_name = location.get("LocationName", "")

            # Only keep target regions
            if location_name not in TARGET_REGIONS:
                continue

            region_label = REGION_LABEL[location_name]

            # date_str → {"mint": [values...], "maxt": [values...]}
            date_temp: dict[str, dict] = {}

            for element in location.get("WeatherElement", []):
                for time_entry in element.get("Time", []):
                    start_time  = time_entry.get("StartTime", "")
                    date_str    = start_time[:10] if start_time else ""
                    if not date_str:
                        continue

                    elem_values = time_entry.get("ElementValue", [])
                    if not elem_values:
                        continue
                    ev = elem_values[0]  # first value dict

                    if date_str not in date_temp:
                        date_temp[date_str] = {"mint": [], "maxt": []}

                    if "MaxTemperature" in ev:
                        try:
                            date_temp[date_str]["maxt"].append(int(ev["MaxTemperature"]))
                        except (ValueError, TypeError):
                            pass

                    if "MinTemperature" in ev:
                        try:
                            date_temp[date_str]["mint"].append(int(ev["MinTemperature"]))
                        except (ValueError, TypeError):
                            pass

            # Flatten: one row per date using daily min / max
            for date_str, temps in sorted(date_temp.items()):
                if temps["mint"] and temps["maxt"]:
                    records.append({
                        "regionName": region_label,
                        "dataDate":   date_str,
                        "mint":       min(temps["mint"]),
                        "maxt":       max(temps["maxt"]),
                    })

    return records



def main():
    # 1. Fetch raw data
    data = fetch_raw_data()

    # 2. Print raw JSON (required for grading)
    print("\n" + "=" * 60)
    print("RAW JSON RESPONSE:")
    print("=" * 60)
    print(json.dumps(data, indent=4, ensure_ascii=False))
    print("=" * 60 + "\n")

    # 3. Parse into structured records
    records = parse_records(data)

    print(f"[INFO] Extracted {len(records)} records from {len(TARGET_REGIONS)} regions.\n")
    for row in records:
        print(f"  {row['regionName']:<20} | {row['dataDate']} | "
              f"min={row['mint']}°C  max={row['maxt']}°C")

    return records   # re-used by task2


if __name__ == "__main__":
    main()
