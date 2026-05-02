# NECCS 大英赛文章爬虫系统

## 功能

1. **文章池管理**：存储从各大英美主流媒体抓取的文章
2. **定时爬取**：每周一自动从 15 个指定源抓取新文章
3. **文章改编**：自动将文章调整到 500-700 词的目标长度
   - 短于 500 词：自动补充过渡句扩展至目标范围
   - 500-700 词：保持原样
   - 超过 700 词：在完整句子边界处截断
4. **题型生成**：根据文章分类自动生成对应题型
5. **概要生成**：自动为每篇文章生成概要
6. **重点提取**：自动提取关键背景知识和词汇

## 支持的文章源

| 刊物 | 分类 | 题型 |
|------|------|------|
| The Economist | news | 阅读理解 A/B 篇 |
| The Guardian | news | 阅读理解 A/B 篇 |
| BBC News | news | 阅读理解 A/B 篇 |
| TIME | news | 阅读理解 A/B 篇 |
| Newsweek | news | 阅读理解 A/B 篇 |
| The New York Times | news | 阅读理解 A/B 篇 |
| New Scientist | science | 阅读 C 篇（匹配） |
| Scientific American | science | 阅读 C 篇（匹配） |
| Discover | science | 阅读 C 篇（匹配） |
| The Atlantic | culture | 完形填空/翻译 |
| Psychology Today | culture | 完形填空/翻译 |
| National Geographic | culture | 完形填空/翻译 |
| Reader's Digest | culture | 完形填空/翻译 |
| HuffPost | culture | 完形填空/翻译 |
| The New Yorker | literature | 阅读 D 篇（简答/文学） |

## 使用方式

### 本地运行爬虫

```bash
# 安装依赖
pip install -r scraper/requirements.txt

# 运行爬虫
python3 scraper/scraper.py
```

### GitHub Actions 自动爬取

1. 将代码推送到 GitHub 仓库
2. GitHub Actions 会在每周一 00:00 UTC 自动运行
3. 也可以手动触发：Actions -> Weekly Article Scraper -> Run workflow

### 文章池结构

文章池存储在 `articles/pool.json`，包含：

- `meta`: 元数据（最后更新时间、下次爬取时间、文章总数等）
- `articles`: 文章数组，每篇文章包含：
  - 基本信息（标题、来源、分类、难度、日期等）
  - 正文段落
  - `summary`: 文章概要
  - `highlights`: 重点内容
    - `keyVocab`: 影响理解的核心词汇
    - `backgroundKnowledge`: 相关背景常识
  - 题目和答案
  - 解析

## 文章改编规则

1. **词数控制**：目标 500-700 词
   - 短于 500 词：补充过渡句扩展至目标范围
   - 500-700 词：理想长度，保持原样
   - 超过 700 词：截取到合适位置（在句号/问号/感叹号处截断）

2. **段落分割**：每 2-3 句为一段

3. **词汇提取**：从预定义的大英赛高频词库中匹配

## 注意事项

1. 部分网站可能有反爬机制，需要配置代理或使用 API
2. 生成的题目和解析是模板化的，建议人工审核后再使用
3. 文章版权归原作者所有，仅供学习使用
