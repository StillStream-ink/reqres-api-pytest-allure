import os
import sys
import json
import subprocess
import shutil
import time
from datetime import datetime

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

    # 2. 注入 Environment 信息
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

    # 6. 修改报告标题
    summary_path = os.path.join(report_dir, "widgets", "summary.json")
    if os.path.exists(summary_path):
        with open(summary_path, "r+", encoding="utf-8") as f:
            data = json.load(f)
            data["reportName"] = "ReqRes 接口自动化测试"
            f.seek(0)
            json.dump(data, f, ensure_ascii=False, indent=2)
            f.truncate()

    # 7. 自动在浏览器中打开报告
    print("▶ 正在启动 Allure 报告...")
    subprocess.run([r"D:\tools\allure\bin\allure.bat", "open", report_dir])

    # ==================== 🆕 8. 归档报告（带时间戳） ====================
    print("▶ 正在归档报告...")
    
    # 创建 reports 目录
    os.makedirs("reports", exist_ok=True)
    
    # 生成时间戳
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"report_{timestamp}"
    archive_path = os.path.join("reports", archive_name)
    
    # 复制报告
    if os.path.exists(report_dir):
        shutil.copytree(report_dir, archive_path)
        print(f"✅ 报告已归档到: {archive_path}")
        
        # 写入归档信息
        info_path = os.path.join(archive_path, "archive_info.txt")
        with open(info_path, "w", encoding="utf-8") as f:
            f.write(f"归档时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"报告名称: {archive_name}\n")
            f.write(f"项目: ReqRes接口自动化测试\n")
        
        # 创建最新版本链接（reports/latest 指向最新报告）
        latest_link = os.path.join("reports", "latest")
        if os.path.exists(latest_link) or os.path.islink(latest_link):
            os.remove(latest_link)
        # Windows 下用符号链接
        try:
            os.symlink(archive_name, latest_link, target_is_directory=True)
        except Exception:
            # 如果不支持符号链接，创建一个快捷方式文件
            with open(os.path.join("reports", "latest.txt"), "w", encoding="utf-8") as f:
                f.write(f"最新报告: {archive_name}\n")
                f.write(f"路径: {archive_path}\n")
        
        print(f"✅ 最新报告链接已更新: reports/latest")
    else:
        print("⚠️ 报告目录不存在，跳过归档")

if __name__ == "__main__":
    main()