from dataclasses import dataclass

from app.services.text_service import normalize_whitespace


class JobScrapingError(RuntimeError):
    pass


@dataclass(frozen=True)
class ScrapedJobPage:
    url: str
    title: str | None
    raw_text: str
    clean_text: str
    scrape_status: str


def scrape_job_url(url: str) -> ScrapedJobPage:
    try:
        import httpx
        from bs4 import BeautifulSoup
    except ImportError as exc:
        raise JobScrapingError(
            "httpx and beautifulsoup4 are not installed. Run backend dependency setup first."
        ) from exc

    try:
        response = httpx.get(
            url,
            follow_redirects=True,
            timeout=15,
            headers={"User-Agent": "ApplyAI/0.1 job analysis bot"},
        )
        response.raise_for_status()
    except Exception as exc:
        raise JobScrapingError(f"Could not fetch job URL: {exc}") from exc

    soup = BeautifulSoup(response.text, "html.parser")

    for element in soup(["script", "style", "noscript", "svg", "nav", "footer", "header"]):
        element.decompose()

    title = normalize_whitespace(soup.title.get_text(" ")) if soup.title else None
    main = soup.find("main") or soup.find("article") or soup.body or soup
    raw_text = main.get_text("\n")
    clean_text = normalize_whitespace(raw_text)

    if len(clean_text) < 200:
        raise JobScrapingError(
            "The page was fetched, but the extracted text was too short. Use manual paste fallback."
        )

    return ScrapedJobPage(
        url=url,
        title=title,
        raw_text=raw_text,
        clean_text=clean_text,
        scrape_status="success",
    )

