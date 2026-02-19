#!/usr/bin/env python3
"""
Backfill: 删除 device_history 中进水/出水温度为 0 的 Rinnai 记录（无效数据）
用法: python scripts/backfill_rinnai_zero_temp.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from models.database import delete_rinnai_zero_temp_records

if __name__ == "__main__":
    deleted = delete_rinnai_zero_temp_records()
    print(f"已删除 {deleted} 条无效 Rinnai 记录（进水/出水温度为 0）")
