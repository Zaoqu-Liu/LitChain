import pandas as pd
import numpy as np


def calculate_journal_score(rank_str):
    """
    计算期刊得分：n / r
    参数格式应为 "r/n" 的字符串（例如 "1/32"）
    """
    if pd.isna(rank_str) or rank_str.strip() == "":
        return np.nan

    try:
        # 分割字符串获取排名r和总数n
        parts = rank_str.split('/')
        if len(parts) != 2:
            return np.nan

        r = float(parts[0].strip())  # 排名（数值越小越好）
        n = float(parts[1].strip())  # 领域内期刊总数

        # 验证数值有效性
        if r < 1 or n < 1 or r > n:
            return np.nan

        # 计算得分：n / r
        return n / r

    except (ValueError, TypeError):
        return np.nan


# 1. 读取Excel文件（替换为您的文件路径）
file_path = r"D:\project\paperagent\2024JCR.xlsx"  # 修改为您的实际文件路径
df = pd.read_excel(file_path)

# 2. 检查数据 - 假设包含排名的列名为"Rank"
# 如果您的列名不同，请修改下面的"Rank"
print("数据前5行：")
print(df.head())

print("\n列名：", df.columns.tolist())

# 3. 应用得分计算函数
df["Score"] = df["JIF Rank"].apply(calculate_journal_score)

# 4. 保存结果到新Excel文件
output_path = "../data/journal_scores.xlsx"
df.to_excel(output_path, index=False)

print(f"\n处理完成！结果已保存至: {output_path}")
print(f"生成的得分列示例：")
print(df[["Rank", "Score"]].head(10))