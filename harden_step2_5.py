import os

base_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot/ai-service"
file_path = os.path.join(base_dir, "crawler", "crawl_service.py")

content = """
import asyncio
import datetime
import uuid
import re
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

class CrawlerService:
    def __init__(self):
        # Safer generic JS to unhide tabs/accordions and safely click expanders
        self.generic_interactive_js = \"\"\"
        // Safe unhiding: only unhide elements that look like content containers
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

        // Safe clicking: avoid forms, external links, navigation, destructive actions
        const forbiddenWords = ['submit', 'delete', 'logout', 'download', 'accept', 'reject', 'save', 'buy', 'cart'];
        const expanderWords = ['read more', 'show more', 'details', 'symptom', 'control', 'development', 'management', 'expand', 'view', 'tab', 'accordion'];

        document.querySelectorAll('button, a, [role="button"], [role="tab"]').forEach(el => {
            let text = (el.innerText || '').toLowerCase();
            let href = el.getAttribute('href') || '';
            
            // Skip if it navigates away
            if (href && href.startsWith('http') && !href.startsWith(window.location.origin)) return;
            if (href && href.includes('.pdf') || href.includes('.zip')) return;
            
            // Skip destructive or form actions
            if (forbiddenWords.some(w => text.includes(w))) return;
            if (el.type === 'submit') return;
            
            // Click if it matches expander words or has aria-expanded="false"
            let isExpander = expanderWords.some(w => text.includes(w));
            let isCollapsed = el.getAttribute('aria-expanded') === 'false';
            
            if(isExpander || isCollapsed) {
                try { 
                    el.click(); 
                } catch(e){}
            }
        });
        \"\"\"

    async def crawl_url_async(self, url, source_meta):
        try:
            print(f"Crawling {url}...")
            
            # 1. First attempt generic crawl without heavy JS
            config_static = CrawlerRunConfig(cache_mode=CacheMode.BYPASS)
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config_static)
                
                if not result or not result.markdown:
                    return None, "Empty content or failed to crawl."
                    
                # 2. Interactive Content Detection (Improved)
                html = result.html or ""
                needs_interaction = False
                
                # Check for strong structural indicators of hidden content
                structural_indicators = ['tab-content', 'accordion', 'aria-expanded="false"', 'modal-dialog', 'collapse']
                if any(ind.lower() in html.lower() for ind in structural_indicators):
                    needs_interaction = True
                    
                # Check for specific interactive expander text inside buttons or links
                if not needs_interaction:
                    # Look for <button> or <a> tags containing expander keywords
                    if re.search(r'(?i)<(?:button|a)[^>]*>.*?(?:symptom|control|development|read more|show more|details).*?</(?:button|a)>', html):
                        needs_interaction = True
                        
                # Only use Playwright if meaningful interaction is detected
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
                            img_type = "general"
                            alt_text = str(img.get('alt', '')).lower()
                            if "symptom" in alt_text or "disease" in alt_text or "anthra" in url.lower():
                                img_type = "disease_symptom"
                                
                            images.append({
                                "crop": source_meta.get("crop", "unknown"),
                                "disease": "Anthracnose" if "anthra" in url.lower() else ("unknown" if img_type == "general" else "extracted from context"),
                                "image_url": img.get('src'),
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
"""
with open(file_path, "w", encoding="utf-8") as f:
    f.write(content.strip() + "\\n")
print("crawl_service.py successfully hardened.")
