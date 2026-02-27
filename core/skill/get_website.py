import requests
import re
import os
import csv
import json
import sqlite3
from typing import Optional, List, Dict, Union
from requests.exceptions import RequestException
from bs4 import BeautifulSoup
try:
    from lxml import etree
except ImportError:
    etree = None

def get_website(url: str, selector: str = None, selector_type: str = "css", 
                max_pages: int = 1, next_page_selector: str = None,
                save_format: str = None, save_path: str = None,
                use_proxy: bool = False) -> str | None:
    """
    高级网页获取工具
    :param url: 目标 URL
    :param selector: CSS 选择器或 XPath 表达式，用于提取特定内容
    :param selector_type: "css" 或 "xpath"
    :param max_pages: 自动翻页最大页数，默认为 1（不翻页）
    :param next_page_selector: 下一页按钮的 CSS 选择器（仅当 max_pages > 1 时需要）
    :param save_format: 数据持久化格式 "json", "csv", "sqlite"
    :param save_path: 数据保存路径
    :param use_proxy: 是否启用代理轮换
    """
    
    # 简单的代理池示例（实际应从外部服务获取）
    proxies_pool = [
        # "http://user:pass@ip:port",
    ]
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    all_content = []
    current_url = url
    
    for page in range(max_pages):
        try:
            proxy = None
            if use_proxy and proxies_pool:
                # 简单轮换：这里仅演示取第一个，实际可用 random.choice
                proxy = {"http": proxies_pool[0], "https": proxies_pool[0]}

            response = requests.get(
                url=current_url,
                headers=headers,
                proxies=proxy,
                timeout=15,
            )
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            # 解析内容
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 内容提取逻辑
            extracted_text = ""
            if selector:
                if selector_type == "css":
                    elements = soup.select(selector)
                    extracted_text = "\n".join([el.get_text(separator=' ', strip=True) for el in elements])
                elif selector_type == "xpath":
                    dom = etree.HTML(response.text)
                    elements = dom.xpath(selector)
                    # lxml xpath 返回可能是 element 或 string
                    texts = []
                    for el in elements:
                        if hasattr(el, 'text'):
                            texts.append(el.text.strip() if el.text else "")
                        else:
                            texts.append(str(el).strip())
                    extracted_text = "\n".join(texts)
            else:
                # 默认全页提取（之前的逻辑）
                for script in soup(["script", "style", "meta", "noscript", "link", "svg", "path"]):
                    script.decompose()
                extracted_text = soup.get_text(separator=' ', strip=True)
                extracted_text = re.sub(r'\s+', ' ', extracted_text).strip()

            all_content.append(extracted_text)
            
            # 翻页逻辑
            if max_pages > 1 and next_page_selector:
                next_btn = soup.select_one(next_page_selector)
                if next_btn and next_btn.get('href'):
                    # 处理相对路径
                    import urllib.parse
                    current_url = urllib.parse.urljoin(current_url, next_btn['href'])
                else:
                    break # 没有下一页了
            else:
                break

        except RequestException as e:
            all_content.append(f"[ERROR] Page {page+1} 请求失败: {type(e).__name__}: {e} | URL: {current_url}")
            break

    full_text = "\n\n--- PAGE BREAK ---\n\n".join(all_content)
    
    # 数据持久化
    if save_format and save_path:
        save_data(all_content, save_format, save_path)
        
    # 返回给 LLM 的摘要（截断）
    if len(full_text) > 8000:
        return full_text[:8000] + "...(truncated)"
    return full_text

def save_data(data: List[str], fmt: str, path: str):
    try:
        if fmt == "json":
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        elif fmt == "csv":
            with open(path, 'w', encoding='utf-8', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["content"])
                for item in data:
                    writer.writerow([item])
        elif fmt == "sqlite":
            conn = sqlite3.connect(path)
            c = conn.cursor()
            c.execute('CREATE TABLE IF NOT EXISTS scraped_data (content TEXT)')
            for item in data:
                c.execute('INSERT INTO scraped_data VALUES (?)', (item,))
            conn.commit()
            conn.close()
    except PermissionError as e:
        print(f"[ERROR] 保存数据权限不足 ({fmt}): {e} | Path: {path}")
    except Exception as e:
        print(f"[ERROR] 保存数据失败 ({fmt}): {type(e).__name__}: {e} | Path: {path}")
