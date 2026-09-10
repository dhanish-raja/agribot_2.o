import re

class ContentCleaner:
    def clean(self, raw_doc):
        text = raw_doc.get("content", "")
        text = re.sub(r"\n{3,}", "\n\n", text)
        lines = text.split("\n")
        cleaned_lines = []
        seen_lines = set()
        
        for line in lines:
            line_stripped = line.strip()
            if len(line_stripped) < 3 and not any(c.isdigit() for c in line_stripped):
                continue
            if line_stripped in seen_lines and len(line_stripped) > 50:
                continue
            seen_lines.add(line_stripped)
            cleaned_lines.append(line)
            
        return "\n".join(cleaned_lines)
