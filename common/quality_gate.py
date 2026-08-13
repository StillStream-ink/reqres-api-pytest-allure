# common/quality_gate.py
import json
import os
import sys

def check_pass_rate(allure_json_dir="allure-results", threshold=90):
    """
    质量门禁：统计Allure结果通过率，低于阈值直接阻断CI
    :param allure_json_dir: allure-results目录
    :param threshold: 最低通过率（百分比，默认90）
    """
    if not os.path.exists(allure_json_dir):
        raise FileNotFoundError(f"目录不存在：{allure_json_dir}")

    total = 0
    passed = 0
    for fname in os.listdir(allure_json_dir):
        if fname.endswith("-result.json"):
            with open(os.path.join(allure_json_dir, fname), "r", encoding="utf-8") as f:
                data = json.load(f)
                total += 1
                if data["status"] == "passed":
                    passed += 1

    rate = passed / total * 100 if total > 0 else 0
    print(f"📊 用例总数: {total}, 通过: {passed}, 通过率: {rate:.2f}%")
    print(f"🎯 门禁阈值: {threshold}%")

    if rate < threshold:
        raise Exception(f"❌ 质量门禁失败！当前通过率 {rate:.2f}% < 阈值 {threshold}%，阻断发布")

if __name__ == "__main__":
    # 可在这里修改阈值，例如90代表最低90%通过率
    check_pass_rate(threshold=90)
