import re

class DocumentSegmenter:
    def segment(self, clean_text, max_chunk_chars=3500):
        segments = []
        current_title = "General"
        current_content = []
        
        # 1. First split by markdown headings if present
        for line in clean_text.split("\n"):
            if line.startswith("#"):
                if current_content:
                    text_block = "\n".join(current_content).strip()
                    if len(text_block) > 10:
                        segments.append({
                            "section_title": current_title,
                            "content": text_block
                        })
                current_title = line.strip("# ").strip()
                current_content = []
            else:
                current_content.append(line)
                
        if current_content:
            text_block = "\n".join(current_content).strip()
            if len(text_block) > 10:
                segments.append({
                    "section_title": current_title,
                    "content": text_block
                })

        # 2. Sub-chunk any segment that is too large (> max_chunk_chars)
        final_segments = []
        for seg in segments:
            c = seg["content"]
            if len(c) <= max_chunk_chars:
                final_segments.append(seg)
            else:
                # Sub-chunk by double newlines (paragraphs)
                paras = c.split("\n\n")
                buf = []
                buf_len = 0
                part_idx = 1
                for p in paras:
                    p = p.strip()
                    if not p:
                        continue
                    if buf_len + len(p) > max_chunk_chars and buf:
                        final_segments.append({
                            "section_title": f"{seg['section_title']} (Part {part_idx})",
                            "content": "\n\n".join(buf).strip()
                        })
                        part_idx += 1
                        buf = [p]
                        buf_len = len(p)
                    else:
                        buf.append(p)
                        buf_len += len(p)
                if buf:
                    final_segments.append({
                        "section_title": f"{seg['section_title']} (Part {part_idx})",
                        "content": "\n\n".join(buf).strip()
                    })

        return [s for s in final_segments if len(s["content"]) > 30]
