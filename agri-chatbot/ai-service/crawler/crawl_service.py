import asyncio
import datetime
import uuid
import re
import os
import requests
import urllib.parse
from io import BytesIO
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
}

class CrawlerService:
    def __init__(self):
        self.generic_interactive_js = """
        document.querySelectorAll('div, section, article, span, p, ul, li').forEach(el => {
            try {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden') {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                    el.style.height = 'auto';
                }
            } catch(e) {}
        });

        const forbiddenWords = ['submit', 'delete', 'logout', 'download', 'accept', 'reject', 'save', 'buy', 'cart'];
        const expanderWords = ['read more', 'show more', 'details', 'symptom', 'control', 'development', 'management', 'expand', 'view', 'tab', 'accordion'];

        document.querySelectorAll('button, a, [role="button"], [role="tab"]').forEach(el => {
            let text = (el.innerText || '').toLowerCase();
            let href = el.getAttribute('href') || '';
            
            if (href && href.startsWith('http') && !href.startsWith(window.location.origin)) return;
            if (href && href.includes('.pdf') || href.includes('.zip')) return;
            if (forbiddenWords.some(w => text.includes(w))) return;
            if (el.type === 'submit') return;
            
            let isExpander = expanderWords.some(w => text.includes(w));
            let isCollapsed = el.getAttribute('aria-expanded') === 'false';
            
            if(isExpander || isCollapsed) {
                try { 
                    if (el.tagName.toLowerCase() === 'a') {
                        el.removeAttribute('href');
                    }
                    el.click(); 
                } catch(e){}
            }
        });
        """

    def _extract_pdf_from_bytes(self, pdf_bytes, url, title, source_meta):
        if not PYPDF_AVAILABLE:
            return None, "pypdf library not available to parse PDF."
        try:
            reader = pypdf.PdfReader(BytesIO(pdf_bytes))
            pages_text = []
            for i, p in enumerate(reader.pages):
                txt = p.extract_text() or ""
                if txt.strip():
                    pages_text.append(f"## Page {i+1}\n\n{txt.strip()}")
            full_content = "\n\n".join(pages_text)
            if not full_content.strip():
                return None, "PDF is raster/scanned images. No selectable text extracted."
            doc = {
                "document_id": str(uuid.uuid4()),
                "crop": source_meta.get("crop", "unknown"),
                "organization": source_meta.get("organization", "ICAR/Gov"),
                "source": source_meta.get("organization", "ICAR/Gov"),
                "source_url": url,
                "title": title or f"PDF Document from {url}",
                "retrieved_at": datetime.datetime.now().isoformat(),
                "content": full_content,
                "html": "",
                "extracted_images": [],
                "interactive_crawl_used": False
            }
            return doc, None
        except Exception as e:
            return None, f"PDF extraction error: {e}"

    async def crawl_url_async(self, url, source_meta):
        lower_url = url.lower()
        
        # 1. Handle Google Docs
        if "docs.google.com/document/d/" in lower_url:
            doc_id_match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
            if doc_id_match:
                doc_id = doc_id_match.group(1)
                export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
                try:
                    resp = requests.get(export_url, headers=HEADERS, timeout=25)
                    if resp.status_code == 200 and len(resp.text.strip()) > 50:
                        doc = {
                            "document_id": str(uuid.uuid4()),
                            "crop": source_meta.get("crop", "unknown"),
                            "organization": "Google Doc Source",
                            "source": "Google Doc Source",
                            "source_url": url,
                            "title": "Mango Agricultural Document (Google Docs)",
                            "retrieved_at": datetime.datetime.now().isoformat(),
                            "content": resp.text.strip(),
                            "html": "",
                            "extracted_images": [],
                            "interactive_crawl_used": False
                        }
                        return doc, None
                except Exception as e:
                    return None, f"Google Doc export error: {e}"

        # 2. Handle Google Drive PDFs
        if "drive.google.com/file/d/" in lower_url:
            file_id_match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
            if file_id_match:
                file_id = file_id_match.group(1)
                dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                try:
                    resp = requests.get(dl_url, headers=HEADERS, timeout=30, stream=True)
                    if resp.status_code == 200:
                        return self._extract_pdf_from_bytes(resp.content, url, "Google Drive Mango Manual", source_meta)
                except Exception as e:
                    return None, f"Google Drive download error: {e}"

        # 3. Handle Direct PDFs
        if lower_url.endswith(".pdf") or "/epdf/" in lower_url:
            try:
                resp = requests.get(url, headers=HEADERS, timeout=30, verify=False)
                if resp.status_code == 200:
                    filename = url.split("/")[-1].replace(".pdf", "")
                    return self._extract_pdf_from_bytes(resp.content, url, f"Mango Guide - {filename}", source_meta)
                elif resp.status_code == 403:
                    return None, "HTTP 403 Forbidden (Bot Protection / Paywall)"
            except Exception as e:
                return None, f"PDF fetch error: {e}"

        # 4. Handle OJS Article Links (e.g. epubs.icar.org.in)
        if "epubs.icar.org.in" in lower_url:
            try:
                probe = requests.get(url, headers=HEADERS, timeout=20, verify=False)
                if probe.status_code == 200:
                    match = re.search(r'href=["\']([^"\']+/article/download/[^"\']+)["\']', probe.text)
                    if match:
                        dl_url = urllib.parse.urljoin(url, match.group(1))
                        pdf_resp = requests.get(dl_url, headers=HEADERS, timeout=30, verify=False)
                        if pdf_resp.status_code == 200:
                            return self._extract_pdf_from_bytes(pdf_resp.content, url, "ICAR Indian Horticulture Research Article", source_meta)
            except Exception as e:
                pass

        # 5. Generic HTML / Interactive Web Crawl via Crawl4AI
        try:
            print(f"Crawling {url}...")
            config_static = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config_static)
                
                if not result or not result.markdown:
                    # Check if blocked
                    try:
                        probe = requests.get(url, headers=HEADERS, timeout=10, verify=False)
                        if probe.status_code == 403:
                            return None, "HTTP 403 Forbidden / Cloudflare Bot Protection"
                    except:
                        pass
                    return None, "Empty content or failed to crawl."
                    
                html = result.html or ""
                needs_interaction = False
                structural_indicators = ['tab-content', 'accordion', 'aria-expanded="false"', 'modal-dialog', 'collapse']
                if any(ind.lower() in html.lower() for ind in structural_indicators):
                    needs_interaction = True
                    
                if not needs_interaction:
                    if re.search(r'(?i)<(?:button|a)[^>]*>.*?(?:symptom|control|development|read more|show more|details).*?</(?:button|a)>', html):
                        needs_interaction = True
                        
                if needs_interaction:
                    print(f"Interactive elements detected on {url}. Re-crawling with safe Playwright JS injection...")
                    config_interactive = CrawlerRunConfig(
                        js_code=[self.generic_interactive_js],
                        wait_for="js:() => true",
                        delay_before_return_html=2.0,
                        cache_mode=CacheMode.BYPASS
                    )
                    result = await crawler.arun(url=url, config=config_interactive)
                
                images = []
                if hasattr(result, 'media') and result.media and 'images' in result.media:
                    for img in result.media['images']:
                        if img.get('src'):
                            src = img.get('src')
                            resolved_url = urllib.parse.urljoin(url, src)
                            img_type = "general"
                            alt_text = str(img.get('alt', '')).lower()
                            if "symptom" in alt_text or "disease" in alt_text or "anthra" in url.lower() or "rot" in url.lower() or "blight" in url.lower():
                                img_type = "disease_symptom"
                                
                            images.append({
                                "crop": source_meta.get("crop", "unknown"),
                                "disease": "disease_symptom" if img_type == "disease_symptom" else "general",
                                "image_url": resolved_url,
                                "source_url": url,
                                "image_type": img_type,
                                "source": source_meta.get("organization", "unknown"),
                                "organization": source_meta.get("organization", "unknown"),
                                "alt_text": img.get('alt', ''),
                                "score": img.get('score', 0)
                            })
                
                doc = {
                    "document_id": str(uuid.uuid4()),
                    "crop": source_meta.get("crop", "unknown"),
                    "organization": source_meta.get("organization", "unknown"),
                    "source": source_meta.get("organization", "unknown"),
                    "source_url": url,
                    "title": result.metadata.get("title", f"Document from {url}") if hasattr(result, "metadata") and result.metadata else f"Document from {url}",
                    "retrieved_at": datetime.datetime.now().isoformat(),
                    "content": result.markdown,
                    "html": result.html,
                    "extracted_images": images,
                    "interactive_crawl_used": needs_interaction
                }
                return doc, None
        except Exception as e:
            return None, str(e)
            
    def crawl_url(self, url, source_meta):
        return asyncio.run(self.crawl_url_async(url, source_meta))