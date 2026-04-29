# core/services/file_loader.py

import os
import pdfplumber
import pandas as pd
from docx import Document


SUPPORTED_EXT = [".pdf", ".docx", ".xlsx", ".xls", ".csv"]


def load_document(path: str) -> str:
    """
    Load PDF / DOCX / Excel / CSV and return full text.
    """

    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")

    ext = os.path.splitext(path)[1].lower()

    if ext not in SUPPORTED_EXT:
        raise ValueError(f"Unsupported file format: {ext}")

    if ext == ".pdf":
        return _load_pdf(path)

    if ext == ".docx":
        return _load_docx(path)

    if ext in [".xlsx", ".xls"]:
        return _load_excel(path)

    if ext == ".csv":
        return _load_csv(path)

    raise RuntimeError("Unsupported document type")


# ------------------------------
# INTERNAL LOADERS
# ------------------------------


def _load_pdf(path):

    text_chunks = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_chunks.append(page_text)

    return "\n".join(text_chunks)


def _load_docx(path):

    doc = Document(path)

    return "\n".join(p.text for p in doc.paragraphs if p.text.strip())


def _load_excel(path):

    dfs = pd.read_excel(path, sheet_name=None)

    blocks = []

    for name, df in dfs.items():
        blocks.append(f"--- Sheet: {name} ---")
        blocks.append(df.astype(str).to_string())

    return "\n".join(blocks)


def _load_csv(path):

    df = pd.read_csv(path)

    return df.astype(str).to_string()
