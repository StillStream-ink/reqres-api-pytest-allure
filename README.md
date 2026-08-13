# ReqRes 接口自动化测试项目 ![CI](https://github.com/StillStream-ink/reqres-api-pytest-allure/actions/workflows/pytest-auto.yml/badge.svg)

> 基于 Pytest + Requests + Allure 搭建的接口自动化测试框架，针对 ReqRes 公开接口实现自动化回归测试，生成可视化测试报告。

## ✨ 项目亮点

- ✅ 统一HTTP请求封装，集成tenacity自动重试，提升外部接口稳定性
- ✅ 工程化分层：用例层、公共工具层、配置数据层分离
- ✅ YAML管理测试数据，实现代码与数据解耦
- ✅ Allure可视化报告：支持环境信息、业务模块(Feature/Story)、执行趋势图
- ✅ 接入GitHub Actions CI，支持每次提交自动执行测试

## 🛠️ 技术栈

| 技术 | 说明 |
|------|------|
| Python 3 | 开发语言 |
| Pytest | 测试框架 |
| Requests | HTTP 接口请求库 |
| Allure | 可视化测试报告 |

## 📂 项目结构

reqres-api-pytest-allure/
├── assets/              # 报告截图（README 展示用）
├── cases/               # 业务测试用例
├── common/              # 公共工具：请求封装、日志、yaml 读取
├── config/              # 测试数据 yaml
├── .github/workflows/   # GitHub Actions CI 配置
├── pytest.ini           # pytest 全局配置
├── requirements.txt     # 依赖清单
└── README.md


## ▶️ 本地运行

### 1. 克隆项目
```bash
git clone https://github.com/StillStream-ink/reqres-api-pytest-allure.git
cd reqres-api-pytest-allure
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 执行测试，生成 Allure 结果
```bash
pytest test_api_demo.py -v --alluredir=allure-results
```

### 4. 打开可视化报告
```bash
allure serve allure-results
```

## 📊 效果预览
### 全量回归通过（100% Passed）
![Allure全量通过](./assets/allure_overview_100pass.png)

### 多轮回归 Trend 趋势监控
![Allure Trend趋势图](./assets/allure_trend_fail.png)
> 前两轮全量通过，第三轮构造异常场景模拟缺陷，直观展示接口迭代质量波动


## 🎯 测试范围
ReqRes 文章模块接口：
- GET 获取文章列表
- GET 获取单篇文章
- POST 新增文章
- PUT 修改文章
- DELETE 删除文章
- 参数化查询不同文章 ID

断言校验：HTTP 状态码、返回数据类型、关键字段存在性、数据长度校验

## 💡 拓展方向
- 已接入 GitHub Actions 实现提交自动回归
- 可新增通过率质量门禁，不达标阻断发布
- 增加数据库校验、完整业务链路场景
- 已实现失败用例自动重跑机制
