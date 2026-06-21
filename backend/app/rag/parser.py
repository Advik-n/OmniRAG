from pathlib import Path
import csv
import fitz
import pandas as pd
from docx import Document as DocxDocument
from pptx import Presentation
from openpyxl import load_workbook

class ParsedDocument(dict): pass

def parse_file(path: str) -> ParsedDocument:
    p = Path(path); ext = p.suffix.lower(); pages=[]
    if ext == ".pdf":
        with fitz.open(path) as doc:
            for i, page in enumerate(doc, 1): pages.append({"page": i, "text": page.get_text("text")})
    elif ext in [".docx", ".doc"]:
        doc = DocxDocument(path); text="\n".join(x.text for x in doc.paragraphs if x.text.strip()); pages.append({"section":"document","text":text})
    elif ext in [".pptx", ".ppt"]:
        prs=Presentation(path)
        for i, slide in enumerate(prs.slides,1):
            text="\n".join(s.text for s in slide.shapes if hasattr(s,"text") and s.text.strip()); pages.append({"slide":i,"text":text})
    elif ext in [".xlsx", ".xls"]:
        wb=load_workbook(path, read_only=True, data_only=True)
        for sheet in wb.sheetnames:
            rows=[]
            for row in wb[sheet].iter_rows(values_only=True): rows.append(" | ".join("" if c is None else str(c) for c in row))
            pages.append({"sheet":sheet,"text":"\n".join(rows)})
    elif ext == ".csv":
        with open(path, newline='', encoding='utf-8', errors='ignore') as f:
            reader=csv.reader(f); pages.append({"section":"csv","text":"\n".join(" | ".join(r) for r in reader)})
    elif ext in [".txt", ".md"]:
        pages.append({"section":ext[1:],"text":p.read_text(encoding='utf-8', errors='ignore')})
    else:
        pages.append({"section":"raw","text":p.read_text(encoding='utf-8', errors='ignore')})
    return ParsedDocument(filename=p.name, pages=[x for x in pages if x.get("text","").strip()])
