#!/usr/bin/env python3
"""
NECCS 大英赛文章爬虫脚本
功能：从指定源抓取文章，改编为500-700词，生成题型，加入文章池
使用：python3 scraper.py 或配置 GitHub Actions 每周一自动执行
"""

import json
import os
import re
import sys
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlparse

# 第三方库（需安装：pip install requests beautifulsoup4 feedparser）
try:
    import requests
    from bs4 import BeautifulSoup
    import feedparser
except ImportError:
    print("请先安装依赖: pip install requests beautifulsoup4 feedparser")
    sys.exit(1)


class ArticleScraper:
    """文章爬虫类"""
    
    # 大英赛文章来源配置
    SOURCES = {
        "The Economist": {
            "url": "https://www.economist.com/feeds/print-sections/79/the-world-this-week.xml",
            "type": "rss",
            "category": "news"
        },
        "The Guardian": {
            "url": "https://www.theguardian.com/world/rss",
            "type": "rss",
            "category": "news"
        },
        "BBC News": {
            "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "type": "rss",
            "category": "news"
        },
        "New Scientist": {
            "url": "https://www.newscientist.com/feed/home",
            "type": "rss",
            "category": "science"
        },
        "Scientific American": {
            "url": "https://www.scientificamerican.com/rss/subject/global-health/",
            "type": "rss",
            "category": "science"
        },
        "National Geographic": {
            "url": "https://www.nationalgeographic.com/rss",
            "type": "rss",
            "category": "culture"
        },
        "Psychology Today": {
            "url": "https://www.psychologytoday.com/us/feed",
            "type": "rss",
            "category": "culture"
        },
        "The Atlantic": {
            "url": "https://www.theatlantic.com/feed/all/",
            "type": "rss",
            "category": "culture"
        },
        "The New Yorker": {
            "url": "https://www.newyorker.com/feed/news",
            "type": "rss",
            "category": "literature"
        },
        "TIME": {
            "url": "https://time.com/feed/",
            "type": "rss",
            "category": "news"
        },
        "Newsweek": {
            "url": "https://www.newsweek.com/rss",
            "type": "rss",
            "category": "news"
        },
        "The New York Times": {
            "url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml",
            "type": "rss",
            "category": "news"
        },
        "Discover": {
            "url": "https://www.discovermagazine.com/rss",
            "type": "rss",
            "category": "science"
        },
        "Reader's Digest": {
            "url": "https://www.rd.com/feed/",
            "type": "rss",
            "category": "culture"
        },
        "HuffPost": {
            "url": "https://www.huffpost.com/section/frontpage/feed",
            "type": "rss",
            "category": "culture"
        }
    }
    
    # 目标词数范围
    TARGET_WORD_COUNT = {"min": 500, "max": 700}
    
    def __init__(self, pool_path="articles/pool.json"):
        self.pool_path = Path(pool_path)
        self.pool = self._load_pool()
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (compatible; NECCSScraper/1.0; +https://example.com)"
        })
    
    def _load_pool(self):
        """加载文章池"""
        if self.pool_path.exists():
            with open(self.pool_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"meta": {"totalArticles": 0, "articles": []}, "articles": []}
    
    def _save_pool(self):
        """保存文章池"""
        self.pool_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.pool_path, "w", encoding="utf-8") as f:
            json.dump(self.pool, f, ensure_ascii=False, indent=2)
    
    def scrape_all_sources(self, articles_per_source=10):
        """从所有源抓取文章"""
        print(f"开始抓取文章... [{datetime.now().strftime('%Y-%m-%d %H:%M')}]")
        
        for source_name, config in self.SOURCES.items():
            print(f"\n--- 抓取: {source_name} ---")
            try:
                articles = self._scrape_source(source_name, config)
                print(f"  获取到 {len(articles)} 篇文章")
                
                # 处理每篇文章
                for i, article in enumerate(articles[:articles_per_source]):
                    print(f"  处理第 {i+1} 篇: {article.get('title', 'Unknown')[:50]}...")
                    processed = self._process_article(article, source_name, config["category"])
                    if processed:
                        self._add_to_pool(processed)
                        
            except Exception as e:
                print(f"  抓取失败: {e}")
        
        # 更新元数据
        self.pool["meta"]["lastUpdated"] = datetime.now().strftime("%Y-%m-%d")
        self.pool["meta"]["totalArticles"] = len(self.pool["articles"])
        self.pool["meta"]["nextScrape"] = (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d")
        
        self._save_pool()
        print(f"\n抓取完成! 文章池总数: {self.pool['meta']['totalArticles']}")
    
    def _scrape_source(self, source_name, config):
        """从单个源抓取文章"""
        articles = []
        
        if config["type"] == "rss":
            articles = self._scrape_rss(config["url"])
        elif config["type"] == "html":
            articles = self._scrape_html(config["url"])
        
        return articles
    
    def _scrape_rss(self, url):
        """通过 RSS 抓取文章"""
        feed = feedparser.parse(url)
        articles = []
        
        for entry in feed.entries[:20]:  # 最多取20篇
            article = {
                "title": entry.get("title", ""),
                "url": entry.get("link", ""),
                "publish_date": entry.get("published", ""),
                "summary": entry.get("summary", ""),
                "content": entry.get("content", [{"value": ""}])[0].get("value", "") if entry.get("content") else entry.get("summary", "")
            }
            articles.append(article)
        
        return articles
    
    def _scrape_html(self, url):
        """通过 HTML 解析抓取文章"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            articles = []
            
            # 通用文章提取逻辑（需根据具体网站调整）
            for article_tag in soup.find_all("article")[:20]:
                title_tag = article_tag.find(["h1", "h2", "h3"])
                content_tag = article_tag.find("div", class_=re.compile(r"content|body|text"))
                
                if title_tag and content_tag:
                    articles.append({
                        "title": title_tag.get_text(strip=True),
                        "url": url,
                        "publish_date": datetime.now().strftime("%Y-%m-%d"),
                        "content": content_tag.get_text(separator=" ", strip=True)
                    })
            
            return articles
            
        except Exception as e:
            print(f"  HTML抓取失败: {e}")
            return []
    
    def _process_article(self, article, source_name, category):
        """处理单篇文章：清洗、改编、生成题型"""
        # 1. 清洗内容
        content = self._clean_content(article.get("content", ""))
        
        # 2. 检查词数并改编
        word_count = len(content.split())
        if word_count < 300:
            print(f"    文章过短 ({word_count} 词)，跳过")
            return None
        
        # 3. 改编到目标词数
        adapted_content = self._adapt_to_target_length(content)
        adapted_word_count = len(adapted_content.split())
        
        # 4. 分割段落
        paragraphs = self._split_paragraphs(adapted_content)
        
        # 5. 提取核心词汇
        vocab = self._extract_vocabulary(adapted_content)
        
        # 6. 生成题目（根据分类）
        questions_data = self._generate_questions(adapted_content, paragraphs, category)

        # 7. 生成概要和背景知识
        summary = self._generate_summary(article.get("title", ""), paragraphs, category)
        highlights = self._generate_highlights(adapted_content, paragraphs, category)

        # 8. 构建文章对象
        processed = {
            "id": f"neccs-{datetime.now().strftime('%Y')}-{len(self.pool['articles'])+1:04d}",
            "title": article.get("title", "Untitled"),
            "source": source_name,
            "sourceCN": self._get_source_cn(source_name),
            "sourceType": category,
            "category": self._get_category_cn(category),
            "level": "CEFR B1-B2",
            "publishDate": article.get("publish_date", datetime.now().strftime("%Y-%m-%d")),
            "scrapeDate": datetime.now().strftime("%Y-%m-%d"),
            "type": questions_data["type"],
            "wordCount": adapted_word_count,
            "adapted": word_count != adapted_word_count,
            "originalUrl": article.get("url", ""),
            "paragraphs": paragraphs,
            "vocab": vocab,
            "summary": summary,
            "highlights": highlights
        }
        
        # 合并题目数据
        processed.update(questions_data)
        
        return processed
    
    def _clean_content(self, content):
        """清洗 HTML 内容"""
        # 移除 HTML 标签
        clean = re.sub(r"<[^>]+>", " ", content)
        # 移除多余空白
        clean = re.sub(r"\s+", " ", clean).strip()
        # 移除特殊字符（保留基本标点）
        clean = re.sub(r"[^\w\s.,;:!?'\"-]", "", clean)
        return clean
    
    def _adapt_to_target_length(self, content):
        """改编文章到目标长度（500-700词）"""
        words = content.split()
        target_min = self.TARGET_WORD_COUNT["min"]
        target_max = self.TARGET_WORD_COUNT["max"]
        target_mid = (target_min + target_max) // 2

        if len(words) < target_min:
            # 文章太短：尝试在最后一个完整句子后补充过渡句
            sentences = re.split(r"(?<=[.!?]) +", content)
            if len(sentences) < 2:
                return content
            last_sentence = sentences[-1]
            expansion = (
                f" This broader context highlights why the issue matters. "
                f"Understanding these dynamics is essential for grasping the full picture. "
                f"The implications extend well beyond the immediate topic at hand."
            )
            expanded = content + expansion
            if len(expanded.split()) >= target_min:
                return expanded
            return content
        elif len(words) > target_max:
            # 文章太长：截取到目标词数附近的完整句子
            target = target_mid
            truncated = " ".join(words[:target])
            last_period = truncated.rfind(".")
            last_question = truncated.rfind("?")
            last_exclaim = truncated.rfind("!")
            last_break = max(last_period, last_question, last_exclaim)

            if last_break > target * 0.6:
                result = truncated[:last_break + 1]
            else:
                result = truncated

            result_words = result.split()
            if len(result_words) < target_min:
                result = " ".join(words[:target_max])
                last_break2 = max(result.rfind("."), result.rfind("?"), result.rfind("!"))
                if last_break2 > target_min:
                    result = result[:last_break2 + 1]

            return result
        else:
            return content
    
    def _split_paragraphs(self, content):
        """将内容分割为段落"""
        # 简单按句号分割，每2-3句为一段
        sentences = re.split(r"(?<=[.!?]) +", content)
        paragraphs = []
        current = []
        
        for sentence in sentences:
            current.append(sentence)
            if len(current) >= 2:  # 每2句为一段
                paragraphs.append(" ".join(current))
                current = []
        
        if current:
            paragraphs.append(" ".join(current))
        
        return paragraphs if paragraphs else [content]
    
    def _extract_vocabulary(self, content):
        """提取核心词汇（简单实现）"""
        # 常见大英赛高频词汇列表（可扩展）
        key_words = [
            "profound", "transform", "disproportionately", "precarious", "elusive",
            "degradation", "sustainable", "commitment", "enforcement", "vulnerable",
            "remarkable", "confound", "intertwined", "subjective", "quantification",
            "paradoxically", "intervention", "cohesion", "backlash", "gentrification"
        ]
        
        vocab = []
        content_lower = content.lower()
        
        for word in key_words:
            if word in content_lower:
                # 简单释义（实际应使用词典API）
                vocab.append(f"{word}: [definition to be added]")
        
        return vocab[:5]  # 最多5个
    
    def _generate_questions(self, content, paragraphs, category):
        """根据分类生成题目"""
        if category == "news":
            return self._generate_reading_ab(content, paragraphs)
        elif category == "science":
            return self._generate_reading_c(content, paragraphs)
        elif category == "literature":
            return self._generate_reading_d(content, paragraphs)
        elif category == "culture":
            # 文化类可以是翻译或完形
            return self._generate_cloze(content, paragraphs)
        else:
            return self._generate_reading_ab(content, paragraphs)
    
    def _generate_reading_ab(self, content, paragraphs):
        """生成阅读理解 A/B 篇（选择题）"""
        return {
            "type": "readingAB",
            "questions": [
                "According to the passage, what is the main idea?",
                "What can be inferred from paragraph 2?",
                "The word '_____' in paragraph X is closest in meaning to _____."
            ],
            "options": [
                ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
                ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"]
            ],
            "answers": [0, 1, 2],
            "explanations": [
                "解析待补充",
                "解析待补充",
                "解析待补充"
            ]
        }
    
    def _generate_reading_c(self, content, paragraphs):
        """生成阅读 C 篇（匹配题）"""
        headings = [
            "A) Introduction to the Topic",
            "B) Key Challenges and Issues",
            "C) Potential Solutions",
            "D) Future Implications",
            "E) Historical Background",
            "F) Expert Opinions"
        ]
        
        return {
            "type": "readingC",
            "matchExercise": {
                "instructions": "Match each paragraph (1-4) with the correct heading (A-F). There are two extra headings.",
                "headings": headings,
                "answers": ["A", "B", "C", "D"],
                "explanations": ["解析待补充"] * len(paragraphs)
            }
        }
    
    def _generate_reading_d(self, content, paragraphs):
        """生成阅读 D 篇（文学简答）"""
        return {
            "type": "readingD",
            "shortAnswer": [
                "What is the tone of the passage?",
                "How does the author develop the main character?",
                "What is the significance of the ending?",
                "Identify one literary device used and explain its effect."
            ],
            "referenceAnswers": [
                "参考答案待补充",
                "参考答案待补充",
                "参考答案待补充",
                "参考答案待补充"
            ]
        }
    
    def _generate_cloze(self, content, paragraphs):
        """生成完形填空"""
        # 简单实现：随机挖空
        words = content.split()
        blank_positions = sorted(set(range(10, len(words)-10, 15))[:8])
        
        cloze_text = content
        for i, pos in enumerate(blank_positions):
            cloze_text = cloze_text.replace(words[pos], f"[{i}]", 1)
        
        return {
            "type": "cloze",
            "clozeText": cloze_text,
            "clozeOptions": [["A) option1", "B) option2", "C) option3", "D) option4"]] * len(blank_positions),
            "clozeAnswers": [0] * len(blank_positions),
            "clozeExplanations": ["解析待补充"] * len(blank_positions)
        }
    
    def _generate_summary(self, title, paragraphs, category):
        """生成文章概要（简短英文，1-2句）"""
        if not paragraphs:
            return ""
        first = paragraphs[0]
        sentences = re.split(r"(?<=[.!?]) +", first)
        summary = sentences[0] if sentences else first[:100]
        if len(sentences) > 1:
            summary += " " + sentences[1]
        last = paragraphs[-1] if len(paragraphs) > 1 else ""
        if last and last != first:
            last_sentences = re.split(r"(?<=[.!?]) +", last)
            if last_sentences:
                summary += " " + last_sentences[-1]
        return summary

    def _generate_highlights(self, content, paragraphs, category):
        """生成重点词汇和背景知识"""
        vocab_map = {
            "disproportionately": { "phonetic": "/ˌdɪsprəˈpɔːʃənətli/", "meaning": "不成比例地" },
            "precarious": { "phonetic": "/prɪˈkeəriəs/", "meaning": "不稳定的；危险的" },
            "elusive": { "phonetic": "/ɪˈluːsɪv/", "meaning": "难以实现的" },
            "degradation": { "phonetic": "/ˌdeɡrəˈdeɪʃn/", "meaning": "退化；恶化" },
            "externalise": { "phonetic": "/ɪkˈstɜːnəlaɪz/", "meaning": "将……外部化（转嫁成本）" },
            "profound": { "phonetic": "/prəˈfaʊnd/", "meaning": "深刻的；深远的" },
            "paradoxically": { "phonetic": "/ˌpærəˈdɒksɪkli/", "meaning": "矛盾地；自相矛盾地" },
            "intervention": { "phonetic": "/ˌɪntəˈvenʃn/", "meaning": "干预措施" },
            "backlash": { "phonetic": "/ˈbæklæʃ/", "meaning": "强烈反对" },
            "gentrification": { "phonetic": "/ˌdʒentrɪfɪˈkeɪʃn/", "meaning": "绅士化（中产化）" },
            "cohesion": { "phonetic": "/kəʊˈhiːʒn/", "meaning": "凝聚力；团结" },
            "confound": { "phonetic": "/kənˈfaʊnd/", "meaning": "使困惑；使混淆" },
            "intertwined": { "phonetic": "/ˌɪntəˈtwaɪnd/", "meaning": "交织在一起的" },
            "subjective": { "phonetic": "/səbˈdʒektɪv/", "meaning": "主观的" },
            "quantification": { "phonetic": "/ˌkwɒntɪfɪˈkeɪʃn/", "meaning": "量化" },
            "sustainable": { "phonetic": "/səˈsteɪnəbl/", "meaning": "可持续的" },
            "vulnerable": { "phonetic": "/ˈvʌlnərəbl/", "meaning": "脆弱的；易受伤的" },
            "commitment": { "phonetic": "/kəˈmɪtmənt/", "meaning": "承诺；投入" },
            "enforcement": { "phonetic": "/ɪnˈfɔːsmənt/", "meaning": "执行；强制" },
            "bombard": { "phonetic": "/bɒmˈbɑːd/", "meaning": "连续轰炸；连珠炮似地提问" },
            "dysregulate": { "phonetic": "/dɪsˈreɡjuleɪt/", "meaning": "使失调" },
            "counterparts": { "phonetic": "/ˈkaʊntəpɑːts/", "meaning": "对应的人或物" },
            "cortisol": { "phonetic": "/ˈkɔːtɪsɒl/", "meaning": "皮质醇（压力激素）" },
            "algorithm": { "phonetic": "/ˈælɡərɪðəm/", "meaning": "算法" },
            "tattered": { "phonetic": "/ˈtætəd/", "meaning": "破旧的；破烂的" },
            "spine": { "phonetic": "/spaɪn/", "meaning": "书脊" },
            "volume": { "phonetic": "/ˈvɒljuːm/", "meaning": "卷；册" },
            "reverence": { "phonetic": "/ˈrevərəns/", "meaning": "尊敬；敬畏" },
            "civilisation": { "phonetic": "/ˌsɪvəlaɪˈzeɪʃn/", "meaning": "文明" },
            "celebrated": { "phonetic": "/ˈselɪbreɪtɪd/", "meaning": "著名的；广受赞誉的" },
            "legumes": { "phonetic": "/ˈleɡjuːmz/", "meaning": "豆类" },
            "landmark": { "phonetic": "/ˈlændmɑːk/", "meaning": "里程碑式的" },
            "cardiovascular": { "phonetic": "/ˌkɑːdiəʊˈvæskjələ(r)/", "meaning": "心血管的" },
            "holistic": { "phonetic": "/həʊˈlɪstɪk/", "meaning": "整体的；全面的" },
            "moderation": { "phonetic": "/ˌmɒdəˈreɪʃn/", "meaning": "适度；节制" },
            "encode": { "phonetic": "/ɪnˈkəʊd/", "meaning": "编码" },
            "facet": { "phonetic": "/ˈfæsɪt/", "meaning": "方面；层面" },
            "intersection": { "phonetic": "/ˌɪntəˈsekʃn/", "meaning": "交叉点" },
            "sacrifice": { "phonetic": "/ˈsækrɪfaɪs/", "meaning": "牺牲；放弃" },
            "homogenised": { "phonetic": "/həˈmɒdʒənaɪzd/", "meaning": "同质化的" },
            "untethered": { "phonetic": "/ʌnˈteðəd/", "meaning": "脱离束缚的" },
            "streamlined": { "phonetic": "/ˈstriːmlaɪnd/", "meaning": "精简的；高效的" },
            "influx": { "phonetic": "/ˈɪnflʌks/", "meaning": "大量涌入" },
            "indistinguishable": { "phonetic": "/ˌɪndɪˈstɪŋɡwɪʃəbl/", "meaning": "难以区分的" },
            "multimodal": { "phonetic": "/ˌmʌltiˈməʊdl/", "meaning": "多模态的" },
            "overconsumption": { "phonetic": "/ˌəʊvəkənˈsʌmpʃn/", "meaning": "过度消费" },
        }

        content_lower = content.lower()
        found_vocab = []
        for word, info in vocab_map.items():
            if word in content_lower:
                found_vocab.append({
                    "word": word,
                    "phonetic": info["phonetic"],
                    "meaning": info["meaning"]
                })

        bg_knowledge = self._get_background_knowledge(category)

        return {
            "keyVocab": found_vocab[:6],
            "backgroundKnowledge": bg_knowledge[:4]
        }

    def _get_background_knowledge(self, category):
        """根据分类返回背景知识（中英结合）"""
        bg = {
            "news": [
                "Inverted Pyramid 倒金字塔结构：新闻写作中将最重要的信息放在开头，次要信息依次排列。",
                "Geopolitical Context 地缘政治背景：理解国际新闻需要掌握相关国家的历史、政治和经济关系。"
            ],
            "science": [
                "Scientific Method 科学方法：通过观察、假设、实验和验证来研究自然现象的系统方法。",
                "Peer Review 同行评审：科学研究成果在发表前需经过同领域专家的审核，以确保质量和可信度。"
            ],
            "culture": [
                "Cultural Context 文化背景：理解文化类文章需要了解相关社会的历史传统和价值观念。",
                "Cross-Cultural Communication 跨文化交流：不同文化背景下人们沟通方式的差异与融合。"
            ],
            "literature": [
                "Literary Devices 文学手法：包括比喻、象征、讽刺等，用于增强作品的表现力和深度。",
                "Narrative Voice 叙事视角：故事中讲述者的立场和语气，影响读者对情节的理解。"
            ]
        }
        return bg.get(category, [])

    def _add_to_pool(self, article):
        """添加文章到文章池"""
        # 检查是否已存在（通过URL或标题）
        for existing in self.pool["articles"]:
            if existing.get("originalUrl") == article.get("originalUrl"):
                print(f"    文章已存在，跳过: {article['title'][:30]}...")
                return
        
        self.pool["articles"].append(article)
        print(f"    已添加: {article['title'][:50]}...")
    
    def _get_source_cn(self, source_name):
        """获取来源中文名"""
        mapping = {
            "The Economist": "《经济学人》",
            "The Guardian": "《卫报》",
            "BBC News": "BBC新闻",
            "New Scientist": "《新科学家》",
            "Scientific American": "《科学美国人》",
            "National Geographic": "《国家地理》",
            "Psychology Today": "《今日心理学》",
            "The Atlantic": "《大西洋月刊》",
            "The New Yorker": "《纽约客》",
            "TIME": "《时代周刊》",
            "Newsweek": "《新闻周刊》",
            "The New York Times": "《纽约时报》",
            "Discover": "《发现》",
            "Reader's Digest": "《读者文摘》",
            "HuffPost": "《赫芬顿邮报》"
        }
        return mapping.get(source_name, source_name)
    
    def _get_category_cn(self, category):
        """获取分类中文名"""
        mapping = {
            "news": "社会热点",
            "science": "科技前沿",
            "culture": "文化与生活",
            "literature": "文学短篇"
        }
        return mapping.get(category, category)


def main():
    """主函数"""
    # 获取文章池路径
    pool_path = os.environ.get("ARTICLE_POOL_PATH", "articles/pool.json")
    
    scraper = ArticleScraper(pool_path)
    scraper.scrape_all_sources(articles_per_source=10)


if __name__ == "__main__":
    main()
