def save_markdown(content, filename="output.md"):
    """
    将Markdown内容保存为.md文件

    :param content: Markdown格式的字符串
    :param filename: 文件名或路径
    """
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"Markdown文件已保存：{filename}")
    except Exception as e:
        print(f"保存失败：{e}")