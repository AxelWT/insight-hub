import httpx
from bs4 import BeautifulSoup


async def crawl_page(url: str, timeout: int = 10) -> dict:
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "Mozilla/5.0 Research Bot"})
            resp.raise_for_status()
            return _extract_content(url, resp.text)
    except Exception as e:
        return {"url": url, "title": "", "content": "", "error": str(e)}


def crawl_page_sync(url: str, timeout: int = 10) -> dict:
    try:
        with httpx.Client(timeout=timeout, follow_redirects=True) as client:
            resp = client.get(url, headers={"User-Agent": "Mozilla/5.0 Research Bot"})
            resp.raise_for_status()
            return _extract_content(url, resp.text)
    except Exception as e:
        return {"url": url, "title": "", "content": "", "error": str(e)}


def _extract_content(url: str, html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")

    for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
        tag.decompose()

    title = soup.title.string.strip() if soup.title and soup.title.string else ""

    main = soup.find("main") or soup.find("article") or soup.find("body")
    if main:
        content = main.get_text(separator="\n", strip=True)
    else:
        content = soup.get_text(separator="\n", strip=True)

    content = "\n".join(line for line in content.splitlines() if line.strip())

    return {"url": url, "title": title, "content": content[:8000], "error": None}
