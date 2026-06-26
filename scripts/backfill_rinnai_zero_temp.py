#!/usr/bin/env python3
"""
Backfill: delete invalid Rinnai device_history rows where inlet/outlet
temperatures are 0 or NULL.

Usage:
  python scripts/backfill_rinnai_zero_temp.py            # delete rows
  python scripts/backfill_rinnai_zero_temp.py --dry-run  # preview only
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import delete_rinnai_zero_temp_records

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Delete invalid Rinnai records with inlet/outlet 0 or NULL")
    parser.add_argument("--dry-run", action="store_true", help="Preview rows without deleting")
    args = parser.parse_args()

    if args.dry_run:
        rows = delete_rinnai_zero_temp_records(dry_run=True)
        print(f"Would delete {len(rows)} rows (--dry-run, no changes made):")
        for r in rows:
            print(f"  id={r[0]} ts={r[1]} inlet={r[2]} outlet={r[3]}")
    else:
        deleted = delete_rinnai_zero_temp_records(dry_run=False)
        print(f"Deleted {deleted} invalid Rinnai records")
