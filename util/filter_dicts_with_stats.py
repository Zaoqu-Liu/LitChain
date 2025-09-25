# -*- coding: utf-8 -*-
def filter_dicts_with_stats(dict1, dict2):
    """
        论文过滤辅助函数：
        1. 根据论文等级过滤
        2. 生成过滤统计信息
        """
    result = {}
    stats = {}
    # 统计结果
    num_papers = 0
    # 遍历每个数据库（biorxiv, medrxiv, pubmed）
    for database in dict1.keys():
        papers = dict1.get(database, [])
        if len(papers)==0:
            continue
        # 初始化统计计数器
        stats[database] = {'level1': 0, 'level2': 0}  # 初始化统计

        # 创建标题到等级的映射

        level_data = dict2.get(database, [])

        # 创建标题到等级的映射
        title_to_level = {}
        for paper_data in level_data:
            if paper_data['level'] in (1, 2):
                normalized_title = paper_data['title'].lower().strip()
                title_to_level[normalized_title] = paper_data['level']

        # 过滤并标记论文等级
        filtered_papers = []
        for paper in papers:
            paper_title = paper['Title'].lower().strip()
            if paper_title in title_to_level:
                # 复制原始论文数据并添加level字段
                paper_with_level = paper.copy()
                paper_level = title_to_level[paper_title]
                paper_with_level['Level'] = paper_level
                filtered_papers.append(paper_with_level)

                # 更新统计计数
                if paper_level == 1:
                    stats[database]['level1'] += 1
                    num_papers = num_papers + 1
                elif paper_level == 2:
                    stats[database]['level2'] += 1
                    num_papers = num_papers + 1

        # 将过滤后的列表添加到结果字典
        result[database] = filtered_papers

    return result, stats, num_papers