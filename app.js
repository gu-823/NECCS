let articlePool = null;
let currentArticle = null;

async function loadArticlePool() {
  try {
    const response = await fetch("./articles/pool.json");
    if (!response.ok) throw new Error("Failed to load article pool");
    articlePool = await response.json();
    return articlePool;
  } catch (error) {
    console.error("Error loading article pool:", error);
    articlePool = getFallbackPool();
    return articlePool;
  }
}

function getFallbackPool() {
  return {
    meta: {
      version: "3.0",
      lastUpdated: new Date().toISOString().split("T")[0],
      totalArticles: 1,
      sources: ["The Economist"]
    },
    articles: [
      {
        id: "fallback-001",
        title: "The Hidden Cost of Fast Fashion on Developing Nations",
        source: "The Economist",
        sourceCN: "《经济学人》",
        sourceType: "news",
        category: "社会热点",
        level: "CEFR B1-B2",
        publishDate: "2026-03-15",
        scrapeDate: new Date().toISOString().split("T")[0],
        type: "readingAB",
        wordCount: 522,
        adapted: true,
        paragraphs: [
          "The global fashion industry has undergone a profound transformation in recent decades, with the rise of fast fashion fundamentally altering how consumers purchase and discard clothing on an unprecedented scale. Major retailers now release new collections every single week, encouraging shoppers to buy more, wear less, and throw away garments after only a handful of uses. While Western consumers enjoy increasingly affordable and trendy garments at remarkably low prices, the true cost of this relentless cycle is disproportionately borne by developing nations that form the backbone of global supply chains and employ millions of vulnerable workers. This shift has transformed not only how people shop but also their relationship with clothing, turning garments from durable goods into disposable commodities.",
          "In Bangladesh, the world's second-largest garment exporter after China, factory workers earn as little as 95 dollars per month, barely enough to cover rent and basic meals for their families. Despite decades of international activism and public awareness campaigns led by prominent human rights organisations, wage levels remain stubbornly insufficient to lift workers out of poverty. The 2013 Rana Plaza collapse, which killed over 1,100 workers and injured thousands more, exposed the precarious safety conditions within supply chains. Yet systemic reform remains elusive, with many factories continuing to operate in structurally unsound buildings that pose serious risks to employees who have few alternatives.",
          "Environmental degradation compounds the human toll significantly. Textile dyeing is responsible for an estimated 20 per cent of global wastewater, much of it discharged untreated directly into rivers and streams in producing countries across South and Southeast Asia. The Buriganga River in Dhaka, once a vital water source for millions of people living in the surrounding communities, is now biologically dead due to decades of unchecked industrial pollution. Fish populations have vanished entirely, and local communities suffer from contaminated drinking water and elevated rates of skin disease and respiratory illness that burden local healthcare systems.",
          "Some high-profile brands have pledged to adopt sustainable practices and reduce their carbon footprint in response to growing public pressure from environmentally conscious consumers and activist shareholders. However, critics argue that voluntary commitments lack meaningful enforcement and independent oversight from third-party auditors who could verify whether companies are actually meeting their stated goals. Unless binding regulations and transparent supply-chain monitoring become universal industry standards enforced by governments worldwide with real penalties for non-compliance, the fast-fashion model will continue to externalise its environmental and social costs onto the world's most vulnerable communities who have the least power to resist exploitation and demand better working conditions.",
          "Consumers in developed countries are beginning to shift their attitudes gradually, though change remains slow and uneven across different demographic groups. Second-hand clothing markets have grown rapidly, and campaigns encouraging people to buy less and choose well have gained traction among younger demographics who are more aware of environmental issues and willing to change their habits. Nevertheless, the structural forces driving overproduction and overconsumption remain deeply embedded in the global economy, and meaningful change will require coordinated action from governments, corporations, and consumers alike to reshape an industry that has become far too profitable in its current form to transform voluntarily."
        ],
        summary: "The fast fashion industry shifts its environmental and social costs onto developing nations, where garment workers earn poverty wages and rivers are poisoned by textile waste. Systemic change requires binding regulations rather than voluntary brand commitments.",
        highlights: {
          keyVocab: [
            { word: "disproportionately", phonetic: "/ˌdɪsprəˈpɔːʃənətli/", meaning: "不成比例地" },
            { word: "precarious", phonetic: "/prɪˈkeəriəs/", meaning: "不稳定的；危险的" },
            { word: "elusive", phonetic: "/ɪˈluːsɪv/", meaning: "难以实现的" },
            { word: "degradation", phonetic: "/ˌdeɡrəˈdeɪʃn/", meaning: "退化；恶化" },
            { word: "externalise", phonetic: "/ɪkˈstɜːnəlaɪz/", meaning: "将……外部化（转嫁成本）" }
          ],
          backgroundKnowledge: [
            "Rana Plaza Collapse (2013) 拉纳广场倒塌：孟加拉国一座服装厂倒塌，造成 1,134 人死亡。",
            "Fast Fashion 快时尚：一种快速、廉价生产服装的商业模式，代表品牌包括 Zara、H&M 和 Shein。",
            "Bangladesh Garment Industry 孟加拉国服装业：雇用超过 400 万工人，占该国出口的 80% 以上。"
          ]
        }
      }
    ]
  };
}

function pickTodayReading() {
  if (!articlePool || !articlePool.articles || articlePool.articles.length === 0) {
    return null;
  }
  const now = new Date();
  const startOfYear = new Date(now.getFullYear(), 0, 0);
  const dayOfYear = Math.floor((now - startOfYear) / (1000 * 60 * 60 * 24));
  const index = dayOfYear % articlePool.articles.length;
  return articlePool.articles[index];
}

function getTimeliness(publishDate) {
  const now = new Date();
  const publish = new Date(publishDate);
  const days = Math.floor((now - publish) / (1000 * 60 * 60 * 24));
  if (days <= 90) return "Recent";
  if (days <= 180) return "Within 6 months";
  return "Within 1 year";
}

function renderArticleSelector() {
  const container = document.getElementById("article-selector-container");
  if (!container || !articlePool || !articlePool.articles) return;

  const select = document.createElement("select");
  select.id = "article-selector";
  select.className = "article-selector";
  select.innerHTML = '<option value="">-- Select an Article --</option>';

  articlePool.articles.forEach((article, i) => {
    const opt = document.createElement("option");
    opt.value = i;
    opt.textContent = `${article.source} | ${article.title}`;
    select.appendChild(opt);
  });

  select.addEventListener("change", (e) => {
    if (e.target.value !== "") {
      const idx = parseInt(e.target.value);
      selectArticle(articlePool.articles[idx]);
    }
  });

  const label = document.createElement("label");
  label.className = "article-selector-label";
  label.textContent = "Switch Article:";
  label.setAttribute("for", "article-selector");

  container.innerHTML = "";
  container.appendChild(label);
  container.appendChild(select);
}

function selectArticle(article) {
  currentArticle = article;
  renderReading(article);
  resetExercise();
}

function resetExercise() {
  const textarea = document.getElementById("exercise-input");
  if (textarea) textarea.value = "";
  const wordCount = document.getElementById("exercise-word-count");
  if (wordCount) wordCount.textContent = "0 词";
  const submitBtn = document.getElementById("exercise-submit");
  if (submitBtn) {
    submitBtn.disabled = false;
    submitBtn.textContent = "Submit";
  }
  const feedback = document.getElementById("exercise-feedback");
  if (feedback) {
    feedback.style.display = "none";
    feedback.innerHTML = "";
  }
}

function renderReading(reading) {
  if (!reading) {
    document.getElementById("article-title").textContent = "暂无文章";
    return;
  }

  currentArticle = reading;

  document.getElementById("publish-date").textContent = `Updated: ${reading.scrapeDate || reading.publishDate}`;
  document.getElementById("reading-title").textContent = reading.title;
  document.getElementById("reading-source").innerHTML = `${reading.sourceCN} ${reading.source}`;
  document.getElementById("reading-level").textContent = reading.level;
  document.getElementById("reading-category").textContent = reading.category;
  document.getElementById("word-count").textContent = `${reading.wordCount || "Unknown"} words`;
  document.getElementById("timeliness").textContent = `Originally published: ${reading.publishDate} (${getTimeliness(reading.publishDate)})`;

  const content = document.getElementById("reading-content");
  content.innerHTML = "";
  if (reading.paragraphs) {
    reading.paragraphs.forEach((p, i) => {
      const el = document.createElement("p");
      el.textContent = p;
      el.className = "reading-paragraph";
      el.dataset.index = i;
      content.appendChild(el);
    });
  }

  const selector = document.getElementById("article-selector");
  if (selector) {
    const idx = articlePool.articles.findIndex(a => a.id === reading.id);
    if (idx >= 0) selector.value = idx;
  }
}

function submitExercise() {
  const textarea = document.getElementById("exercise-input");
  const userAnswer = textarea.value.trim();

  if (!userAnswer) {
    alert("Please write down your reading reflection first.");
    return;
  }

  if (!currentArticle) return;

  const feedbackDiv = document.getElementById("exercise-feedback");
  feedbackDiv.style.display = "block";

  let html = "";

  html += '<div class="feedback-section summary-section">';
  html += '<h4 class="feedback-section-title">Summary</h4>';
  html += `<p class="summary-text">${currentArticle.summary || "No summary available."}</p>`;
  html += '</div>';

  if (currentArticle.highlights) {
    html += '<div class="feedback-section vocab-section">';
    html += '<h4 class="feedback-section-title">Key Vocabulary</h4>';
    html += '<ul class="vocab-grid">';
    const vocab = currentArticle.highlights.keyVocab || [];
    vocab.forEach(v => {
      html += `<li class="vocab-item">`;
      html += `<span class="vocab-word">${v.word}</span>`;
      html += `<span class="vocab-phonetic">${v.phonetic}</span>`;
      html += `<span class="vocab-meaning">${v.meaning}</span>`;
      html += `</li>`;
    });
    html += '</ul>';
    html += '</div>';

    const bg = currentArticle.highlights.backgroundKnowledge || [];
    if (bg.length > 0) {
      html += '<div class="feedback-section knowledge-section">';
      html += '<h4 class="feedback-section-title">Background Knowledge</h4>';
      html += '<ul class="knowledge-list">';
      bg.forEach(item => {
        html += `<li>${item}</li>`;
      });
      html += '</ul>';
      html += '</div>';
    }
  }

  feedbackDiv.innerHTML = html;

  const submitBtn = document.getElementById("exercise-submit");
  submitBtn.disabled = true;
  submitBtn.textContent = "Submitted";
}

document.addEventListener("DOMContentLoaded", async () => {
  await loadArticlePool();
  renderArticleSelector();

  const textarea = document.getElementById("exercise-input");
  textarea.addEventListener("input", () => {
    const words = textarea.value.trim().split(/\s+/).filter(w => w.length > 0);
    document.getElementById("exercise-word-count").textContent = `${words.length} words`;
  });

  document.getElementById("exercise-submit").addEventListener("click", submitExercise);

  const todayReading = pickTodayReading();
  if (todayReading) {
    selectArticle(todayReading);
  }
});
