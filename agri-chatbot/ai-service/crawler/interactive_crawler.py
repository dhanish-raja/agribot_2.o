import asyncio
import datetime
import uuid
import json
import os
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode

class InteractiveCrawlerService:
    async def crawl_url_async(self, url, source_meta):
        try:
            print(f"Crawling {url} interactively...")
            
            # JS to unhide all tabs/modals and extract image metadata
            js_code = """
            // Reveal hidden content
            document.querySelectorAll('*').forEach(el => {
                const style = window.getComputedStyle(el);
                if (style.display === 'none' || style.visibility === 'hidden' || style.opacity === '0') {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                }
            });
            // Try to click any 'Symptoms and control' or interactive buttons
            document.querySelectorAll('a, button').forEach(el => {
                if(el.innerText && el.innerText.toLowerCase().includes('symptoms')) {
                    try { el.click(); } catch(e){}
                }
            });
            """
            
            config = CrawlerRunConfig(
                js_code=[js_code],
                wait_for="js:() => true", # Just wait a bit for JS to execute
                delay_before_return_html=2.0,
                cache_mode=CacheMode.BYPASS
            )
            
            async with AsyncWebCrawler() as crawler:
                result = await crawler.arun(url=url, config=config)
                
                if not result or not result.markdown:
                    return None, "Empty content or failed to crawl."
                
                images = []
                # Handle images from media
                if hasattr(result, 'media') and result.media and 'images' in result.media:
                    for img in result.media['images']:
                        if img.get('src'):
                            images.append({
                                "crop": source_meta.get("crop", "unknown"),
                                "disease": "Anthracnose" if "anthra" in url.lower() else "unknown",
                                "image_url": img.get('src'),
                                "source_url": url,
                                "image_type": "disease_symptom",
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
                    "extracted_images": images
                }
                return doc, None
        except Exception as e:
            return None, str(e)
            
    def crawl_url(self, url, source_meta):
        return asyncio.run(self.crawl_url_async(url, source_meta))
