import fitz
from typing import List, Dict, Tuple
import io


class PDFExtractor:
    def extract_text_from_pdf(self, pdf_bytes: bytes) -> Tuple[str, List[Dict[str, any]], int]:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")

        full_text = ""
        pages_data = []
        char_offset = 0

        for page_num in range(len(doc)):
            page = doc[page_num]
            page_text = page.get_text()

            char_start = char_offset
            char_end = char_offset + len(page_text)

            pages_data.append({
                "page_number": page_num + 1,
                "text": page_text,
                "char_start": char_start,
                "char_end": char_end
            })

            full_text += page_text
            char_offset = char_end

        doc.close()

        return full_text, pages_data, len(doc)

    def chunk_text(self, text: str, pages_data: List[Dict], chunk_size: int = 1000, overlap: int = 200) -> List[Dict]:
        chunks = []
        chunk_id = 0

        for page_data in pages_data:
            page_text = page_data["text"]
            page_number = page_data["page_number"]
            page_char_start = page_data["char_start"]

            start = 0
            while start < len(page_text):
                end = min(start + chunk_size, len(page_text))

                chunk_text = page_text[start:end]

                if chunk_text.strip():
                    chunks.append({
                        "chunk_text": chunk_text,
                        "page_number": page_number,
                        "char_start": page_char_start + start,
                        "char_end": page_char_start + end
                    })

                if end >= len(page_text):
                    break

                start = end - overlap

        return chunks
