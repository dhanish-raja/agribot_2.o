import os
import sys
import json
import re
import argparse
import requests
import urllib.parse
from io import BytesIO

# Try importing pypdf
try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# Default browser headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

def audit_url(url, timeout=25):
    result = {
        "url": url,
        "type": "UNKNOWN",
        "accessible": False,
        "http_status": None,
        "content_type": "",
        "text_extracted": False,
        "text_length": 0,
        "text_sample": "",
        "images_found": 0,
        "agri_images_found": 0,
        "image_urls": [],
        "interactive": False,
        "interactive_details": [],
        "is_pdf": False,
        "pdf_pages": 0,
        "ocr_needed": False,
        "status": "FAIL",
        "reason": "",
        "notes": []
    }

    # Identify URL type hints
    lower_url = url.lower()
    if ".pdf" in lower_url or "/epdf/" in lower_url:
        result["type"] = "PDF"
        result["is_pdf"] = True
    elif "docs.google.com" in lower_url:
        result["type"] = "Google Docs"
    elif "drive.google.com" in lower_url:
        result["type"] = "Google Drive"
    elif "researchgate.net" in lower_url:
        result["type"] = "ResearchGate"
    else:
        result["type"] = "Webpage"

    # Step 1: Probe via HTTP Request
    try:
        resp = requests.get(url, headers=HEADERS, timeout=timeout, verify=False, allow_redirects=True)
        result["http_status"] = resp.status_code
        result["content_type"] = resp.headers.get("Content-Type", "")
        
        if resp.status_code == 200:
            result["accessible"] = True
        elif resp.status_code == 403:
            result["accessible"] = False
            result["status"] = "BLOCKED"
            result["reason"] = f"HTTP 403 Forbidden / Bot Protection ({result['type']})"
            return result
        elif resp.status_code == 404:
            result["accessible"] = False
            result["status"] = "FAIL"
            result["reason"] = "HTTP 404 Not Found"
            return result
        elif resp.status_code >= 500:
            result["accessible"] = False
            result["status"] = "FAIL"
            result["reason"] = f"HTTP {resp.status_code} Server Error"
            return result
        else:
            result["reason"] = f"HTTP {resp.status_code}"
    except requests.exceptions.SSLError as e:
        result["reason"] = f"SSL Certificate Error: {e}"
        result["status"] = "FAIL"
        return result
    except requests.exceptions.Timeout:
        result["reason"] = "Connection Timeout"
        result["status"] = "FAIL"
        return result
    except Exception as e:
        result["reason"] = f"Connection Failed: {e}"
        result["status"] = "FAIL"
        return result

    # Step 2: Handle Google Docs / Google Drive
    if result["type"] == "Google Docs":
        # Extract doc ID
        doc_id_match = re.search(r"/document/d/([a-zA-Z0-9_-]+)", url)
        if doc_id_match:
            doc_id = doc_id_match.group(1)
            export_url = f"https://docs.google.com/document/d/{doc_id}/export?format=txt"
            try:
                exp_resp = requests.get(export_url, headers=HEADERS, timeout=timeout)
                if exp_resp.status_code == 200 and len(exp_resp.text.strip()) > 50:
                    result["text_extracted"] = True
                    result["text_length"] = len(exp_resp.text)
                    result["text_sample"] = exp_resp.text[:300].strip()
                    result["status"] = "PASS"
                    result["reason"] = f"Google Doc public export accessible ({result['text_length']} chars)"
                    return result
                else:
                    result["status"] = "PARTIAL"
                    result["reason"] = "Google Doc accessible via web viewer, but direct TXT export restricted or requires login"
            except Exception as e:
                result["notes"].append(f"Export probe failed: {e}")
        # Web viewer fallback
        if "Sign in" in resp.text:
            result["status"] = "BLOCKED"
            result["reason"] = "Google Docs requires Google account sign-in / access permission"
            return result
        else:
            result["status"] = "PARTIAL"
            result["reason"] = "Google Doc web viewer loaded, requires headless browser DOM extraction"
            return result

    if result["type"] == "Google Drive":
        file_id_match = re.search(r"/file/d/([a-zA-Z0-9_-]+)", url)
        if file_id_match:
            file_id = file_id_match.group(1)
            # Direct download URL
            dl_url = f"https://drive.google.com/uc?export=download&id={file_id}"
            try:
                dl_resp = requests.get(dl_url, headers=HEADERS, timeout=timeout, stream=True)
                if dl_resp.status_code == 200:
                    ct = dl_resp.headers.get("Content-Type", "")
                    if "pdf" in ct.lower() or "application/octet-stream" in ct.lower():
                        result["is_pdf"] = True
                        content_bytes = dl_resp.content
                        if PYPDF_AVAILABLE and len(content_bytes) > 100:
                            try:
                                reader = pypdf.PdfReader(BytesIO(content_bytes))
                                result["pdf_pages"] = len(reader.pages)
                                text = "".join([p.extract_text() or "" for p in reader.pages])
                                if len(text.strip()) > 100:
                                    result["text_extracted"] = True
                                    result["text_length"] = len(text)
                                    result["text_sample"] = text[:300].strip()
                                    result["status"] = "PASS"
                                    result["reason"] = f"Google Drive PDF downloaded and extracted ({result['pdf_pages']} pages, {len(text)} chars)"
                                    return result
                                else:
                                    result["ocr_needed"] = True
                                    result["status"] = "UNSUPPORTED"
                                    result["reason"] = f"Google Drive PDF is scanned/rasterized ({result['pdf_pages']} pages, 0 selectable text, OCR needed)"
                                    return result
                            except Exception as e:
                                result["notes"].append(f"PDF parse failed: {e}")
            except Exception as e:
                result["notes"].append(f"Drive direct download failed: {e}")

        if "Sign in" in resp.text:
            result["status"] = "BLOCKED"
            result["reason"] = "Google Drive file requires permission / sign in"
        else:
            result["status"] = "PARTIAL"
            result["reason"] = "Google Drive preview accessible, direct binary export restricted"
        return result

    # Step 3: Handle PDF files
    is_pdf_content = "application/pdf" in result["content_type"].lower() or result["is_pdf"]
    if is_pdf_content:
        result["type"] = "PDF"
        result["is_pdf"] = True
        try:
            pdf_bytes = resp.content
            if PYPDF_AVAILABLE:
                try:
                    reader = pypdf.PdfReader(BytesIO(pdf_bytes))
                    result["pdf_pages"] = len(reader.pages)
                    extracted_text = ""
                    for p in reader.pages:
                        t = p.extract_text()
                        if t:
                            extracted_text += t + "\n"
                    
                    if len(extracted_text.strip()) > 200:
                        result["text_extracted"] = True
                        result["text_length"] = len(extracted_text)
                        result["text_sample"] = extracted_text[:300].strip()
                        result["status"] = "PASS"
                        result["reason"] = f"PDF text extracted successfully ({result['pdf_pages']} pages, {result['text_length']} chars)"
                    else:
                        result["ocr_needed"] = True
                        result["status"] = "UNSUPPORTED"
                        result["reason"] = f"PDF contains scanned images/raster pages ({result['pdf_pages']} pages, text < 200 chars). Requires OCR."
                except Exception as e:
                    result["status"] = "FAIL"
                    result["reason"] = f"Corrupted or unsupported PDF structure: {e}"
            else:
                result["status"] = "PARTIAL"
                result["reason"] = "PDF downloaded, but pypdf is not available"
            return result
        except Exception as e:
            result["status"] = "FAIL"
            result["reason"] = f"Failed to download/process PDF: {e}"
            return result

    # Step 4: Handle HTML Webpages & ResearchGate
    html = resp.text
    result["text_length"] = len(html)

    # Check for ResearchGate specific behavior
    if result["type"] == "ResearchGate":
        if "captcha" in html.lower() or "blocked" in html.lower() or resp.status_code == 403:
            result["status"] = "BLOCKED"
            result["reason"] = "ResearchGate anti-scraping / Cloudflare challenge triggered"
            return result
        
        # Check if full text is available or only abstract
        has_full_text = "full-text available" in html.lower() or "read full-text" in html.lower()
        has_abstract = "abstract" in html.lower() or "publication-abstract" in html.lower()
        
        if has_full_text and not ("request full-text" in html.lower() and not "download full-text" in html.lower()):
            result["status"] = "PARTIAL"
            result["reason"] = "ResearchGate public article page accessible (Abstract + metadata present; complete PDF locked behind interaction/request)"
        elif has_abstract:
            result["status"] = "PARTIAL"
            result["reason"] = "ResearchGate abstract/metadata accessible; full text requires author request or institutional login"
        else:
            result["status"] = "PARTIAL"
            result["reason"] = "ResearchGate overview page loaded; partial scientific metadata extractable"
        
        result["text_extracted"] = True
        return result

    # Standard Webpage Analysis (TNAU, ICAR, mango-crop, OpenBooks, etc.)
    # 0. Check for Open Journal Systems (OJS) or embedded PDF download links (e.g. epubs.icar.org.in)
    ojs_download_match = re.search(r'href=["\']([^"\']+/article/download/[^"\']+)["\']', html)
    if ojs_download_match:
        pdf_dl_url = urllib.parse.urljoin(url, ojs_download_match.group(1))
        try:
            pdf_resp = requests.get(pdf_dl_url, headers=HEADERS, timeout=timeout, verify=False)
            if pdf_resp.status_code == 200 and PYPDF_AVAILABLE:
                reader = pypdf.PdfReader(BytesIO(pdf_resp.content))
                result["type"] = "PDF Article (OJS)"
                result["is_pdf"] = True
                result["pdf_pages"] = len(reader.pages)
                pdf_text = "".join([p.extract_text() or "" for p in reader.pages])
                if len(pdf_text.strip()) > 200:
                    result["text_extracted"] = True
                    result["text_length"] = len(pdf_text)
                    result["text_sample"] = pdf_text[:300].strip()
                    result["status"] = "PASS"
                    result["reason"] = f"Resolved via OJS PDF download link ({result['pdf_pages']} pages, {result['text_length']} chars text extracted)"
                    return result
        except Exception as e:
            result["notes"].append(f"OJS download attempt failed: {e}")

    # 1. Check for interactive elements
    interactive_markers = [
        "tabbed", "sweetmodal", "modal", "tab-content", "accordion", 
        "aria-expanded", "symptoms and control", "onclick="
    ]
    found_markers = [m for m in interactive_markers if m in html.lower()]
    if found_markers:
        result["interactive"] = True
        result["interactive_details"] = found_markers

    # 2. Extract Images & verify their accessibility
    # Use regex to find <img> tags
    img_matches = re.findall(r'<img[^>]+src=["\']([^"\']+)["\'][^>]*>', html, re.IGNORECASE)
    result["images_found"] = len(img_matches)
    
    agri_keywords = ["mango", "fruit", "leaf", "anthra", "disease", "symptom", "rot", "blight", "twig", "dieback", "hopper", "seedling", "clip_image"]
    agri_images = []
    
    for src in img_matches:
        # Filter UI junk like spacers, banners, arrows
        src_lower = src.lower()
        if any(skip in src_lower for skip in ["spacer.gif", "dot.gif", "blank.png", "facebook", "twitter", "icon"]):
            continue
        
        # Resolve relative URL
        resolved_src = urllib.parse.urljoin(url, src)
        if any(kw in src_lower for kw in agri_keywords):
            agri_images.append(resolved_src)
        else:
            # Check alt text surrounding
            agri_images.append(resolved_src)
            
    result["agri_images_found"] = len(agri_images)
    result["image_urls"] = agri_images[:10]  # Store sample

    # 3. Clean textual preview from HTML
    clean_text = re.sub(r'<script[^>]*>.*?</script>', ' ', html, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r'<style[^>]*>.*?</style>', ' ', clean_text, flags=re.DOTALL | re.IGNORECASE)
    clean_text = re.sub(r'<[^>]+>', ' ', clean_text)
    clean_text = re.sub(r'\s+', ' ', clean_text).strip()
    
    result["text_length"] = len(clean_text)
    if len(clean_text) > 200:
        result["text_extracted"] = True
        result["text_sample"] = clean_text[:300]
        
        # If interactive content exists (e.g. mango-crop disease pages)
        if result["interactive"]:
            result["status"] = "PASS"
            result["reason"] = f"Interactive agricultural page ({len(clean_text)} chars text, {result['agri_images_found']} images, interactive markers: {', '.join(found_markers[:3])})"
        else:
            result["status"] = "PASS"
            result["reason"] = f"Static agricultural page ({len(clean_text)} chars text, {result['agri_images_found']} images)"
    else:
        result["status"] = "PARTIAL"
        result["reason"] = f"Page loaded but extracted text is very short ({len(clean_text)} chars)"

    return result

def run_audit(urls, output_dir=None):
    if not output_dir:
        output_dir = "C:/Users/HP/OneDrive/Desktop/Agribot_2.o/agri-chatbot/data/audit"
    os.makedirs(output_dir, exist_ok=True)
    
    print(f"Starting URL Audit for {len(urls)} URLs...")
    results = []
    
    for i, u in enumerate(urls):
        print(f"[{i+1}/{len(urls)}] Auditing: {u}")
        r = audit_url(u)
        results.append(r)
        print(f"    -> Status: {r['status']} | Type: {r['type']} | Accessible: {r['accessible']} | Text: {r['text_extracted']} ({r['text_length']} chars) | Images: {r['agri_images_found']} | PDF: {r['is_pdf']} | Reason: {r['reason']}")

    # Save to data/audit/
    out_json = os.path.join(output_dir, "url_audit.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
        
    print(f"\nAudit complete! Results saved to: {out_json}")
    return results

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="URL Compatibility Audit")
    parser.add_argument("--file", type=str, help="Text file with URLs")
    parser.add_argument("--urls", nargs="+", help="One or more URLs to audit")
    parser.add_argument("--output-dir", type=str, default=None, help="Output audit directory")
    args = parser.parse_args()

    urls_to_test = []
    if args.file and os.path.exists(args.file):
        with open(args.file, "r", encoding="utf-8") as f:
            for l in f:
                l = l.strip()
                if l and not l.startswith("#"):
                    urls_to_test.append(l)
    elif args.urls:
        urls_to_test = args.urls

    if urls_to_test:
        run_audit(urls_to_test, args.output_dir)
    else:
        print("Please provide --file or --urls")
