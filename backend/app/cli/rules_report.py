import sys
import json
import argparse
from app.db.session import SessionLocal
from app.core import clock
from app.domain.report import generate_rules_report

def main():
    parser = argparse.ArgumentParser(description="Generate EOS Rules Report JSON")
    parser.add_argument("--app-now", dest="app_now", help="Override APP_NOW (ISO 8601)", default=None)
    args = parser.parse_args()

    now_utc = clock.get_app_now_utc(args.app_now) if args.app_now else clock.get_app_now_utc()
    db = SessionLocal()
    try:
        report = generate_rules_report(db, now_utc=now_utc)
        print(json.dumps(report, indent=2))
    finally:
        db.close()

if __name__ == "__main__":
    main()
