import os
import json

def pytest_unconfigure(config):
    """用例全部跑完之后执行，避开--clean-alluredir清空时序冲突【CI首选钩子】"""
    alluredir = config.getoption("--alluredir")
    if not alluredir:
        return

    # ========== 1.自动写入 environment.properties ==========
    env_data = """Project=ReqRes接口自动化测试
BaseUrl=https://reqres.in
System=Windows10 + WSL Ubuntu
Python=3.11
Framework=pytest
Library=requests
ReportTool=allure-pytest
Tester=测试工程师
Module=文章模块
"""
    env_path = os.path.join(alluredir, "environment.properties")
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_data)

    # ========== 2.自动写入 executor.json（CI构建信息，右下角Executors区域） ==========
    executor_data = {
        "name": "Jenkins",
        "type": "jenkins",
        "buildName": os.getenv("BUILD_NAME", "Local-Dev"),
        "buildUrl": os.getenv("BUILD_URL", ""),
        "reportName": "ReqRes API自动化报告"
    }
    exec_path = os.path.join(alluredir, "executor.json")
    with open(exec_path, "w", encoding="utf-8") as f:
        json.dump(executor_data, f, ensure_ascii=False, indent=2)
