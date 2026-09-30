import os
import json
import glob
import re

# Negative patterns: UI elements, non-plant graphics, people, scientists, news, events, staff portraits
FORBIDDEN_KEYWORDS = [
    # UI & Web junk
    'banner', 'header', 'footer', 'logo', 'emblem', 'flag', 'icon', 'arrow', 'bullet',
    'button', 'menu', 'nav', 'home', 'screen', 'pixel', 'spacer', 'divider', 'search',
    'social', 'facebook', 'twitter', 'youtube', 'instagram', 'clip_image', 'index',
    'top_of_page', 'license', 'policy', 'privacy', 'avatar', 'btn', 'thumb_nav',
    'portal', 'advertisement', 'ad_', 'sidebar', 'widget', 'government',
    'favicon', 'placeholder', 'no_image', 'default', 'slide_', 'carousel',
    
    # People, Scientists, Events & News junk
    'marie', 'noelle', 'scaled', 'portrait', 'staff', 'team', 'member', 'director',
    'president', 'scientist', 'researcher', 'people', 'person', 'meeting', 'workshop',
    'conference', 'award', 'event', 'speech', 'interview', 'news', 'story', 'author',
    'profile', 'group', 'crowd', 'office', 'building', 'facility', 'lab_',
    'laboratory', 'ceremony', 'inauguration', 'press', 'wp-content/uploads/20'
]

FORBIDDEN_PATHS = [
    '/assets/images/', '/theme/', '/includes/', '/icons/', '/logos/', '/css/',
    '/js/', '/style/', '/site_images/', '/common/', '/template/', '/tag/', '/author/'
]

FORBIDDEN_EXTENSIONS = ['.gif', '.svg', '.ico']

# Positive plant / disease / symptom terms
PLANT_DISEASE_KEYWORDS = [
    'disease', 'symptom', 'blast', 'blight', 'rot', 'spot', 'rust', 'canker', 'wilt',
    'leaf', 'grain', 'stem', 'borer', 'bug', 'pest', 'anthra', 'sheath', 'tungro',
    'smut', 'mildew', 'gall', 'hopper', 'caterpillar', 'moth', 'weevil', 'aphid',
    'deficiency', 'lesion', 'damage', 'infected', 'healthy', 'fruit', 'pod', 'stalk',
    'root', 'panicle', 'tiller', 'crop', 'plant', 'cultivar', 'variety', 'diseases',
    'insect', 'weed', 'field_symptom', 'yellowing', 'stunting', 'necrosis', 'mosaic'
]

def is_valid_plant_image(img, crop_name):
    url = img.get('image_url', '').strip()
    alt = str(img.get('alt_text', '')).strip().lower()
    low_url = url.lower()
    img_type = img.get('image_type', '')
    
    # 1. Must be valid absolute HTTP/HTTPS URL
    if not (url.startswith('http://') or url.startswith('https://')):
        return False, 'Invalid URL format'
        
    # 2. Reject forbidden extensions
    if any(low_url.endswith(ext) or ext + '?' in low_url for ext in FORBIDDEN_EXTENSIONS):
        return False, 'Forbidden image extension (.gif/.svg/.ico)'
        
    # 3. Reject forbidden path patterns
    if any(p in low_url for p in FORBIDDEN_PATHS):
        return False, f'Forbidden path pattern'

    # 4. Reject forbidden keywords in URL or Alt text (people, scientists, UI junk)
    for pat in FORBIDDEN_KEYWORDS:
        if pat in low_url or pat in alt:
            return False, f'Forbidden keyword/person match: {pat}'
            
    # 5. Filter out MS Word / Office web export clipart junk
    if 'clip_image' in low_url or 'image00' in low_url:
        return False, 'Generic office clipart export'
        
    # 6. Must be marked as disease_symptom OR contain plant/disease relevance
    has_plant_relevance = any(k in low_url or k in alt for k in PLANT_DISEASE_KEYWORDS)
    is_disease = (img_type == 'disease_symptom')
    
    # For crops like rice/coconut/sugarcane with large web news scrapes, strictly require disease/plant relevance
    if not (is_disease or has_plant_relevance):
        return False, 'Lacks verified plant or disease symptom relevance'
        
    return True, 'OK'

def clean_all_crop_images(base_dir=None):
    if not base_dir:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data", "processed"))
        if not os.path.exists(base_dir):
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "processed"))

    print(f"=== Running Strict Pure Plant & Disease Image Purge in: {base_dir} ===")
    
    summary = {}
    
    for crop_dir in glob.glob(os.path.join(base_dir, '*')):
        if not os.path.isdir(crop_dir) or 'rejected' in crop_dir:
            continue
        crop = os.path.basename(crop_dir)
        img_file = os.path.join(crop_dir, f"{crop}_images.jsonl")
        
        if not os.path.exists(img_file):
            continue
            
        with open(img_file, 'r', encoding='utf-8') as f:
            lines = [json.loads(l) for l in f if l.strip()]
            
        cleaned_records = []
        seen_urls = set()
        removed_count = 0
        reasons_map = {}
        
        for img in lines:
            url = img.get('image_url', '').strip()
            if not url or url in seen_urls:
                removed_count += 1
                reasons_map['Duplicate URL'] = reasons_map.get('Duplicate URL', 0) + 1
                continue
                
            valid, reason = is_valid_plant_image(img, crop)
            if valid:
                seen_urls.add(url)
                cleaned_records.append(img)
            else:
                removed_count += 1
                reasons_map[reason] = reasons_map.get(reason, 0) + 1
                
        # Overwrite with cleaned records
        with open(img_file, 'w', encoding='utf-8') as f:
            for c_img in cleaned_records:
                f.write(json.dumps(c_img, ensure_ascii=False) + "\n")
                
        summary[crop] = {
            "original": len(lines),
            "cleaned": len(cleaned_records),
            "removed": removed_count,
            "reasons": reasons_map
        }
        
        print(f"[{crop.upper()}] Original: {len(lines)} | Pure Plant & Disease Images: {len(cleaned_records)} | Purged: {removed_count}")

    print("\n=== Pure Plant & Disease Image Cleanup Complete! ===")
    return summary

if __name__ == "__main__":
    clean_all_crop_images()
