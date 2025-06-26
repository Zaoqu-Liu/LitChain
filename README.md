## 生物领域论文研究代理

该项目是一个基于LangGraph和deerflow项目方向的生物领域论文深度研究代理系统，能够自动完成从研究背景调研到生成完整调查报告的全过程。

## 功能概述
背景调研：自动检索当前研究领域的最新进展

研究规划：智能规划论文搜索策略

文献检索：精准定位相关学术论文

报告生成：整合信息生成结构化的调查报告

##  工作流程

![img.png](img.png)

##  安装指南
# 前置要求
Python 3.10+

OpenAI API 密钥（或其他支持的大模型API密钥）
TAVILY_API_KEY 密钥

# 安装依赖：
bash

conda create -n bio-research-agent python=3.10 -y
conda activate bio-research-agent
pip install -r requirements.txt

## 使用说明
启动项目
运行主程序并在主函数中输入你想查询的东西：

bash
python main.py

## 示例查询
"CRISPR-Cas9基因编辑技术的最新进展"

"阿尔茨海默病的新型生物标志物研究"

"肿瘤免疫治疗中的CAR-T细胞疗法优化"


##  项目结构

