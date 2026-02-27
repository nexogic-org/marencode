try:
    from github import Github, GithubException
except ImportError:
    Github = None
    GithubException = Exception
from datetime import datetime
import json

def search_github(query: str, limit: int = 5, token: str = None) -> str:
    """
    在 GitHub 上搜索项目并获取详细信息
    :param query: 搜索关键词 (例如: "maren-code language:python")
    :param limit: 返回结果数量限制
    :param token: GitHub Personal Access Token (可选，用于提高限额)
    """
    try:
        # 如果提供了 token 则使用，否则匿名访问（限制较严格）
        g = Github(token)
        
        # 搜索仓库
        # sort="stars" 按星数排序，order="desc" 降序
        repositories = g.search_repositories(query=query, sort="stars", order="desc")
        
        results = []
        count = 0
        
        for repo in repositories:
            if count >= limit:
                break
                
            repo_info = {
                "name": repo.full_name,
                "description": repo.description or "无描述",
                "stars": repo.stargazers_count,
                "forks": repo.forks_count,
                "language": repo.language or "Unknown",
                "url": repo.html_url,
                "updated_at": repo.updated_at.strftime("%Y-%m-%d"),
                "topics": repo.get_topics()
            }
            results.append(repo_info)
            count += 1
            
        if not results:
            return "未在 GitHub 上找到相关项目。"
            
        # 格式化输出
        output = [f"### GitHub 搜索结果: {query}"]
        for i, res in enumerate(results, 1):
            topics = ", ".join(res['topics'][:5]) if res['topics'] else "无标签"
            output.append(
                f"{i}. **{res['name']}** (⭐ {res['stars']} | 🍴 {res['forks']})\n"
                f"   - 描述: {res['description']}\n"
                f"   - 语言: {res['language']} | 更新: {res['updated_at']}\n"
                f"   - 标签: {topics}\n"
                f"   - 链接: {res['url']}"
            )
            
        return "\n\n".join(output)
        
    except GithubException as e:
        msg = e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)
        return f"GitHub API 调用失败: {msg}"
    except ConnectionError as e:
        return f"GitHub 连接失败: {type(e).__name__}: {e}"
    except Exception as e:
        return f"GitHub 搜索异常: {type(e).__name__}: {e}"

if __name__ == "__main__":
    # 测试
    print(search_github("maren-code"))
