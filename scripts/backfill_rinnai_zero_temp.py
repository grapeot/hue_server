#!/usr/bin/env python3
"""
Backfill: 删除 device_history 中进水/出水温度为 0 或 NULL 的 Rinnai 记录（无效数据）
用法:
  python scripts/backfill_rinnai_zero_temp.py         # 执行删除
  python scripts/backfill_rinnai_zero_temp.py --dry-run  # 仅预览，不删除
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import delete_rinnai_zero_temp_records

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="删除无效 Rinnai 记录（inlet/outlet 为 0 或 NULL）")
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不实际删除")
    args = parser.parse_args()

    if args.dry_run:
        rows = delete_rinnai_zero_temp_records(dry_run=True)
        print(f"将删除 {len(rows)} 条记录（--dry-run 未实际执行）：")
        for r in rows:
            print(f"  id={r[0]} ts={r[1]} inlet={r[2]} outlet={r[3]}")
    else:
        deleted = delete_rinnai_zero_temp_records(dry_run=False)
        print(f"已删除 {deleted} 条无效 Rinnai 记录")
