import os
import sys
import json
import subprocess
import shutil

def main():
    results_dir = "./allure-results"
    report_dir = "./allure-report"
    env_file = os.path.join(results_dir, "environment.properties")
    executor_file = os.path.join(results_dir, "executor.json")

    # 1. 清理旧数据
    for d in [results_dir, report_dir]:
        if os.path.exists(d):
            shutil.rmtree(d)
    os.makedirs(results_dir, exist_ok=True)

    # 2. 注入 Environment 信息 (解决 Environment 空白问题)
    with open(env_file, "w", encoding="utf-8") as f:
        f.write("Project=ReqRes接口自动化测试\n")
        f.write("BaseUrl=http://127.0.0.1:5000\n")
        f.write("Environment=dev\n")
        f.write("Timeout=10\n")
        f.write("Framework=pytest\n")

    # 3. 注入 Executor 信息
    with open(executor_file, "w", encoding="utf-8") as f:
        json.dump({"name": "Local-Dev", "type": "local", "buildName": "Local-Dev"}, f, ensure_ascii=False, indent=2)

    # 4. 运行 pytest 收集数据
    print("▶ 正在执行测试用例...")
    subprocess.run([sys.executable, "-m", "pytest", "-v", "-s", f"--alluredir={results_dir}"])

    # 5. 生成 Allure 报告
    print("▶ 正在生成 Allure 报告...")
    subprocess.run([r"D:\tools\allure\bin\allure.bat", "generate", results_dir, "-o", report_dir, "--clean"])

    # 6. 强行修改报告标题 (解决标题无法修改的问题)
    summary_path = os.path.join(report_dir, "widgets", "summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["reportName"] = "ReqRes 接口自动化测试"  # 👈 这里改你想要的名字
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()

    # 7. 自动在浏览器中打开报告
    print("▶ 正在启动 Allure 报告...")
    subprocess.run([r"D:\tools\allure\bin\allure.bat", "open", report_dir])

if __name__ == "__main__":
    main()