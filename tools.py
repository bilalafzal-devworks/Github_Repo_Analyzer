import httpx
from bs4 import BeautifulSoup
from ddgs import DDGS
from crewai.tools import tool

@tool("github_repo_info")
def github_repo_info(repo_url: str, github_token: str = "") -> str:
    """Fetches GitHub repository metadata, file list, languages, recent commits, and existing README via GitHub REST API."""
    try:
        parts = repo_url.rstrip("/").split("/")
        if len(parts) < 2:
            return "Error: Invalid GitHub repository URL format. Use https://github.com/owner/repo"
        owner, repo = parts[-2], parts[-1]
        
        headers = {"Accept": "application/vnd.github.v3+json"}
        if github_token:
            headers["Authorization"] = f"token {github_token}"
            
        api_base = f"https://api.github.com/repos/{owner}/{repo}"
        
        with httpx.Client(timeout=15.0) as client:
            repo_resp = client.get(api_base, headers=headers)
            if repo_resp.status_code != 200:
                return f"Error fetching repo metadata: HTTP {repo_resp.status_code}. Ensure repository is public."
            data = repo_resp.json()
            
            lang_resp = client.get(f"{api_base}/languages", headers=headers)
            languages = list(lang_resp.json().keys()) if lang_resp.status_code == 200 else []
            
            tree_resp = client.get(f"{api_base}/git/trees/main?recursive=1", headers=headers)
            if tree_resp.status_code != 200:
                tree_resp = client.get(f"{api_base}/git/trees/master?recursive=1", headers=headers)
            
            file_list = []
            if tree_resp.status_code == 200:
                tree_data = tree_resp.json().get("tree", [])
                file_list = [item["path"] for item in tree_data[:100]]
                
            commits_resp = client.get(f"{api_base}/commits", headers=headers)
            recent_commits = []
            if commits_resp.status_code == 200:
                for c in commits_resp.json()[:5]:
                    msg = c.get("commit", {}).get("message", "").split("\n")[0]
                    author = c.get("commit", {}).get("author", {}).get("name", "Unknown")
                    recent_commits.append(f"- {msg} ({author})")
                    
            readme_resp = client.get(f"{api_base}/readme", headers=headers)
            readme_text = "No README found."
            if readme_resp.status_code == 200:
                import base64
                content_b64 = readme_resp.json().get("content", "")
                if content_b64:
                    readme_text = base64.b64decode(content_b64).decode("utf-8", errors="ignore")[:2500]
                    
            summary = f"""
Repository: {data.get('full_name')}
Description: {data.get('description')}
Stars: {data.get('stargazers_count')} | Forks: {data.get('forks_count')} | Open Issues: {data.get('open_issues_count')}
Primary Language: {data.get('language')}
All Languages: {', '.join(languages)}
Root / File List (sample): {', '.join(file_list[:40])}
Recent Commits:
{'\n'.join(recent_commits)}

Existing README Excerpt:
{readme_text[:1500]}
"""
            return summary
    except Exception as e:
        return f"Exception while fetching GitHub repo info: {str(e)}"

@tool("read_repo_file")
def read_repo_file(repo_url: str, filepath: str, github_token: str = "") -> str:
    """Reads raw text of a specific file in the GitHub repository (first 2500 characters)."""
    try:
        parts = repo_url.rstrip("/").split("/")
        owner, repo = parts[-2], parts[-1]
        raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/main/{filepath}"
        
        headers = {}
        if github_token:
            headers["Authorization"] = f"token {github_token}"
            
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(raw_url, headers=headers)
            if resp.status_code != 200:
                raw_url = f"https://raw.githubusercontent.com/{owner}/{repo}/master/{filepath}"
                resp = client.get(raw_url, headers=headers)
            if resp.status_code != 200:
                return f"Error reading file {filepath}: HTTP {resp.status_code}"
            return resp.text[:2500]
    except Exception as e:
        return f"Exception reading file {filepath}: {str(e)}"

@tool("web_search")
def web_search(query: str) -> str:
    """Performs a web search using ddgs to gather tech stack details, libraries, or documentation."""
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=4):
                results.append(f"Title: {r.get('title')}\nSnippet: {r.get('body')}\nURL: {r.get('href')}\n")
        return "\n".join(results) if results else "No search results found."
    except Exception as e:
        return f"Web search failed: {str(e)}"

@tool("check_links")
def check_links(urls_str: str) -> str:
    """Checks up to 8 URLs with httpx and returns OK or DEAD status for each."""
    urls = [u.strip() for u in urls_str.split(",") if u.strip()][:8]
    report = []
    with httpx.Client(timeout=8.0, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = client.get(url)
                status = "OK" if resp.status_code < 400 else f"DEAD (HTTP {resp.status_code})"
                report.append(f"{url}: {status}")
            except Exception:
                report.append(f"{url}: DEAD (Connection Error)")
    return "\n".join(report)

@tool("check_post_length")
def check_post_length(post_text: str) -> str:
    """Returns the character count of the LinkedIn post and warns if it exceeds 3,000 characters."""
    count = len(post_text)
    warning = "WARNING: Exceeds 3,000 characters limit!" if count > 3000 else "Length is within LinkedIn limits."
    return f"Character Count: {count}. {warning}"
