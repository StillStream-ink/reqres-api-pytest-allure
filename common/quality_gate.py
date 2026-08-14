import json
import os
import sys
import argparse

def check_pass_rate(allure_json_dir="allure-results", threshold=90):
    """
    质量门禁：统计Allure结果通过率，低于阈值阻断CI
    """
    if not os.path.exists(allure_json_dir):
        raise FileNotFoundError(f"目录不存在：{allure_json_dir}")

    total = 0
    passed = 0
    failed = 0
    skipped = 0

    for fname in os.listdir(allure_json_dir):
        if not fname.endswith("-result.json"):
            continue
        
        filepath = os.path.join(allure_json_dir, fname)
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError:
            print(f"⚠️ 跳过损坏文件：{fname}")
            continue

        status = data.get("status", "unknown")
        total += 1
        
        if status == "passed":
            passed += 1
        elif status == "failed":
            failed += 1
        elif status == "skipped":
            skipped += 1

    # 有效用例 = 总数 - 跳过（跳过的不参与通过率计算）
    effective_total = total - skipped
    rate = passed / effective_total * 100 if effective_total > 0 else 0

    print(f"📊 用例总数: {total} | 通过: {passed} | 失败: {failed} | 跳过: {skipped}")
    print(f"📊 有效通过率: {rate:.2f}% (跳过不计入)")
    print(f"🎯 门禁阈值: {threshold}%")

    if rate < threshold:
        print(f"❌ 质量门禁失败！通过率 {rate:.2f}% < {threshold}%")
        sys.exit(1)  # 返回非零退出码，阻断CI
    else:
        print(f"✅ 质量门禁通过")
        sys.exit(0)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Allure Quality Gate")
    parser.add_argument("--dir", default="allure-results", help="Allure结果目录")
    parser.add_argument("--threshold", type=int, default=90, help="最低通过率")
    args = parser.parse_args()
    
    check_pass_rate(args.dir, args.threshold)