from database import get_all_zones, get_recent_reports
from ai import analyze_sentiment

zones = get_all_zones()
reports = get_recent_reports(days=30)
print(f"Total reports in 30 days: {len(reports)}\n")

for zone in zones:
    z_name = zone["name"].lower()
    zone_reports = [r for r in reports if z_name in r["location_name"].lower() or r["location_name"].lower() in z_name]
    
    if not zone_reports:
        print(f"NO REPORTS  | {zone['name']}")
        continue
        
    total = sum(r["severity"] + analyze_sentiment(r["description"]) for r in zone_reports)
    avg = total / len(zone_reports)
    print(f"avg={avg:.1f} reports={len(zone_reports)} | {zone['name']}")
