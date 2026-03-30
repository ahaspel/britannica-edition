"""Prototype plate parser — pair images with section labels and captions."""
import json, re, sys
sys.stdout.reconfigure(encoding="utf-8")

with open("data/raw/wikisource/vol_01/vol01-page0747.json", encoding="utf-8") as f:
    data = json.load(f)
raw = data["raw_text"]

# Find HTML tables
tables = re.findall(r"<table[^>]*>.*?</table>", raw, flags=re.DOTALL | re.IGNORECASE)
if not tables:
    print("No HTML tables found")
    sys.exit()

table = tables[0]
rows = re.findall(r"<tr[^>]*>(.*?)</tr>", table, flags=re.DOTALL | re.IGNORECASE)

def extract_cells(row_html):
    return [re.sub(r"<[^>]+>", "", cell).strip()
            for cell in re.findall(r"<td[^>]*>(.*?)</td>", row_html, flags=re.DOTALL | re.IGNORECASE)]

def extract_images(row_html):
    return [m.group(1) for m in re.finditer(r"\[\[(?:Image|File):([^\]|]+)", row_html, re.I)]

def clean_caption(text):
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    text = text.replace("''", "").replace("&amp;", "&").replace("&deg;", "°")
    return " ".join(text.split()).strip()

# Process in groups of 3 rows: images, labels, captions
figures = []  # list of (image, section, caption)

i = 0
while i < len(rows):
    images = extract_images(rows[i])
    if not images:
        i += 1
        continue

    # Next row should be labels
    labels = []
    if i + 1 < len(rows):
        cells = extract_cells(rows[i + 1])
        labels = [c.strip().rstrip(".") for c in cells if c.strip() and any(ch.isalpha() for ch in c)]

    # Next row should be captions
    captions = []
    if i + 2 < len(rows):
        raw_cells = re.findall(r"<td[^>]*>(.*?)</td>", rows[i + 2], flags=re.DOTALL | re.IGNORECASE)
        captions = [clean_caption(c) for c in raw_cells if c.strip()]

    # Pair them up
    for j, img in enumerate(images):
        section = labels[j] if j < len(labels) else ""
        caption = captions[j] if j < len(captions) else ""
        figures.append((img, section, caption))

    i += 3

# Group by section
from collections import defaultdict
by_section = defaultdict(list)
for img, section, caption in figures:
    by_section[section].append((img, caption))

# Display
for section, figs in by_section.items():
    print(f"\n=== {section} ({len(figs)} figures) ===")
    for img, caption in figs:
        print(f"  {img}")
        print(f"    {caption[:80]}")
