import requests
from bs4 import BeautifulSoup
import re
import urllib.parse
from core.skill.get_time import get_current_time

def search_web(query: str, engine: str = "bing", limit: int = 5) -> str:
    """
    执行网络搜索并返回精简结果
    :param query: 搜索关键词
    :param engine: 搜索引擎 "bing" 或 "baidu"
    :param limit: 返回结果数量
    """
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    results = []
    
    try:
        # 添加当前时间上下文，有助于搜索时效性判断
        current_time = get_current_time()
        
        if engine.lower() == "bing":
            # Bing 有时需要 cookie 或更严格的 UA
            url = f"https://www.bing.com/search?q={urllib.parse.quote(query)}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            # Bing 结构可能会变，尝试多种选择器
            items = soup.select('li.b_algo')
            if not items:
                # 备用选择器
                items = soup.select('.b_algo')
                
            for item in items[:limit]:
                title_tag = item.select_one('h2 a')
                # 尝试获取摘要，优先 caption p，其次 snippet
                snippet_tag = item.select_one('.b_caption p') or item.select_one('.b_snippet') or item.select_one('.b_algoSlug')
                # 尝试获取来源/时间
                source_tag = item.select_one('.b_attribution') or item.select_one('.b_pubDate')
                
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "link": title_tag.get('href'),
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "无摘要",
                        "source": source_tag.get_text(strip=True) if source_tag else ""
                    })
                    
        elif engine.lower() == "baidu":
            url = f"https://www.baidu.com/s?wd={urllib.parse.quote(query)}"
            resp = requests.get(url, headers=headers, timeout=10)
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, 'html.parser')
            
            for item in soup.select('.result.c-container')[:limit]:
                title_tag = item.select_one('h3.t a')
                snippet_tag = item.select_one('.c-abstract') or item.select_one('.c-span18') or item.select_one('.content-right_8Zs40')
                
                if title_tag:
                    results.append({
                        "title": title_tag.get_text(strip=True),
                        "link": title_tag.get('href'),
                        "snippet": snippet_tag.get_text(strip=True) if snippet_tag else "无摘要",
                        "source": "" # 百度来源较难提取统一
                    })
    except requests.exceptions.Timeout as e:
        return f"搜索超时 ({engine}): {type(e).__name__}: {e}"
    except requests.exceptions.ConnectionError as e:
        return f"搜索连接失败 ({engine}): {type(e).__name__}: {e}"
    except Exception as e:
        return f"搜索出错 ({engine}): {type(e).__name__}: {e}"

    if not results:
        return f"未找到相关结果 (当前时间: {get_current_time()})。"

    # 格式化输出，供 LLM 阅读
    output = [f"### 搜索结果 ({engine}): {query}", f"**当前时间**: {get_current_time()}"]
    for i, res in enumerate(results, 1):
        source_info = f" ({res['source']})" if res.get('source') else ""
        output.append(f"{i}. **{res['title']}**{source_info}\n   - 链接: {res['link']}\n   - 摘要: {res['snippet']}")
    
    return "\n\n".join(output)
