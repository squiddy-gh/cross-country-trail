"""Build first-print proofs for the Fairfax Cross County Trail guide."""
from __future__ import annotations

import csv
import html
import re
import textwrap
import xml.etree.ElementTree as ET
from pathlib import Path

from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor, black, white
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
OUT = ROOT / "print" / "output"
BOOKLET = OUT / "fairfax-cross-county-trail-pocket-guide.pdf"
FOLDOUT = OUT / "fairfax-cross-county-trail-foldout-map.pdf"
SITE_URL = "https://squiddy-gh.github.io/cross-county-trail/"
GPX_URL = "https://raw.githubusercontent.com/squiddy-gh/cross-county-trail/main/data/trail/GC_CCT.gpx"
PAGE_W, PAGE_H = 4.25 * inch, 7 * inch
MAP_W, MAP_H = 25.5 * inch, 7 * inch  # Six 4.25 x 7 in accordion panels.


def rows(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", errors="replace", newline="") as stream:
        return list(csv.DictReader(stream))


def narrative_text(record: dict[str, str], narratives: dict[str, dict[str, str]]) -> str:
    item = narratives.get(record.get("Narrative", ""))
    if not item or not item.get("Markdown File"):
        return record.get("Notes", "")
    filename = item["Markdown File"]
    for folder in (DATA / "text" / "poi", DATA / "text" / "areas"):
        source = folder / filename
        if source.exists():
            text = source.read_text(encoding="utf-8", errors="replace")
            text = re.sub(r"!?(\[[^]]*\])\([^)]*\)", r"\1", text)
            return re.sub(r"[#*_`]", "", text).strip()
    return record.get("Notes", "")


def qr(c: canvas.Canvas, value: str, x: float, y: float, size: float) -> None:
    widget = QrCodeWidget(value)
    bounds = widget.getBounds()
    drawing = Drawing(size, size, transform=[size / (bounds[2] - bounds[0]), 0, 0, size / (bounds[3] - bounds[1]), 0, 0])
    drawing.add(widget)
    renderPDF.draw(drawing, c, x, y)


def wrapped(c: canvas.Canvas, text: str, x: float, y: float, width: float, leading: float = 10) -> float:
    for paragraph in text.splitlines() or [""]:
        paragraph = paragraph.strip()
        if not paragraph:
            y -= leading
            continue
        for line in textwrap.wrap(paragraph, width=max(20, int(width / 5.3))):
            if y < 0.55 * inch:
                return y
            c.drawString(x, y, line)
            y -= leading
    return y


def photo_cell(c, image_path, x, y, width, height):
    """Draw a photo cropped to fill a fixed gallery cell."""
    image = ImageReader(str(image_path))
    source_width, source_height = image.getSize()
    scale = max(width / source_width, height / source_height)
    draw_width, draw_height = source_width * scale, source_height * scale
    draw_x = x + (width - draw_width) / 2
    draw_y = y + (height - draw_height) / 2
    clip = c.beginPath()
    clip.rect(x, y, width, height)
    c.saveState()
    c.clipPath(clip, stroke=0, fill=0)
    c.drawImage(image, draw_x, draw_y, width=draw_width, height=draw_height)
    c.restoreState()


def booklet() -> None:
    all_pois = [r for r in rows(DATA / "curated_pois_enriched.csv") if r.get("ObjectType") != "Area"]
    pois = [r for r in all_pois if r.get("Type") != "Parking"]
    parking = [r for r in all_pois if r.get("Type") == "Parking"]
    narratives = {r["NarrativeID"]: r for r in rows(DATA / "narratives.csv")}
    photos = {r["PhotoID"]: r for r in rows(DATA / "photos.csv")}
    c = canvas.Canvas(str(BOOKLET), pagesize=(PAGE_W, PAGE_H))
    c.setFillColor(HexColor("#173f36")); c.rect(0, 0, PAGE_W, PAGE_H, fill=1, stroke=0)
    c.setFillColor(white); c.setFont("Helvetica-Bold", 22); c.drawCentredString(PAGE_W / 2, 5.5 * inch, "FAIRFAX COUNTY")
    c.setFont("Helvetica-Bold", 19); c.drawCentredString(PAGE_W / 2, 5.1 * inch, "CROSS COUNTY TRAIL")
    c.setFont("Helvetica", 14); c.drawCentredString(PAGE_W / 2, 4.65 * inch, "A Pocket Guide")
    c.setFont("Helvetica", 10); c.drawCentredString(PAGE_W / 2, 4.25 * inch, "40+ miles - Great Falls to Occoquan")
    qr(c, SITE_URL, 1.55 * inch, 2.4 * inch, 1.15 * inch); c.setFont("Helvetica", 8); c.drawCentredString(PAGE_W / 2, 2.2 * inch, "Interactive maps and current alerts")
    c.showPage()
    y = PAGE_H - .45 * inch
    c.setFillColor(HexColor("#173f36")); c.setFont("Helvetica-Bold", 16); c.drawString(.3 * inch, y, "Trail stories")
    y -= .28 * inch
    for poi in pois:
        story = narrative_text(poi, narratives)
        if not story and not poi.get("Notes"):
            continue
        photo_ids = [photo_id.strip() for photo_id in poi.get("PrimaryPhotoId", "").split(",") if photo_id.strip()]
        image_paths = [DATA / "photos" / photos[photo_id]["Filename"] for photo_id in photo_ids if photo_id in photos and (DATA / "photos" / photos[photo_id]["Filename"]).exists()]
        story = story[:1100]
        image_rows = (len(image_paths) + 1) // 2
        needed = .27 * inch + image_rows * 1.18 * inch + (len(textwrap.wrap(story, 48)) + 3) * 9
        if y - needed < .45 * inch:
            c.showPage(); y = PAGE_H - .45 * inch
        c.setFillColor(HexColor("#173f36")); c.setFont("Helvetica-Bold", 12); c.drawString(.3 * inch, y, poi.get("Name", "")); y -= .15 * inch
        c.setFillColor(HexColor("#745b33")); c.setFont("Helvetica-Bold", 7.5); c.drawString(.3 * inch, y, poi.get("Type", "").upper()); y -= .12 * inch
        for index, image_path in enumerate(image_paths):
            col, row = index % 2, index // 2
            x = .3 * inch + col * 1.84 * inch
            image_y = y - row * 1.18 * inch - 1.02 * inch
            try:
                photo_cell(c, image_path, x, image_y, 1.73 * inch, 1.0 * inch)
            except Exception:
                pass
        y -= image_rows * 1.18 * inch
        c.setFillColor(black); c.setFont("Helvetica", 8.3); y = wrapped(c, story, .3 * inch, y, 3.65 * inch, 9.4)
        facts = " | ".join(f"{label}: {poi[key]}" for label, key in (("Hours", "Hours"), ("Parking", "Capacity"), ("CCT mile", "Trail Mileage")) if poi.get(key))
        if facts:
            c.setFillColor(HexColor("#444444")); c.setFont("Helvetica-Oblique", 7.2); y = wrapped(c, facts, .3 * inch, y - .08 * inch, 3.65 * inch, 8.5)
        y -= .19 * inch
    c.showPage(); y = PAGE_H - .45 * inch
    c.setFillColor(HexColor("#173f36")); c.setFont("Helvetica-Bold", 16); c.drawString(.3 * inch, y, "Parking & trailheads"); y -= .3 * inch
    c.setFillColor(HexColor("#444444")); c.setFont("Helvetica", 8)
    for poi in parking:
        detail = " | ".join(filter(None, [f"CCT mile {poi['Trail Mileage']}" if poi.get('Trail Mileage') else "", f"{poi['Capacity']} spaces" if poi.get('Capacity') else "", poi.get('Surface', ''), poi.get('Hours', '')]))
        note = poi.get("Notes", "")
        needed = 31 + len(textwrap.wrap(note, 52)) * 8
        if y - needed < .42 * inch:
            c.showPage(); y = PAGE_H - .45 * inch
        c.setFillColor(HexColor("#173f36")); c.setFont("Helvetica-Bold", 9); c.drawString(.3 * inch, y, poi.get("Name", "")); y -= .12 * inch
        c.setFillColor(HexColor("#444444")); c.setFont("Helvetica", 7.5); y = wrapped(c, detail, .3 * inch, y, 3.65 * inch, 8.5)
        if note:
            c.setFont("Helvetica-Oblique", 7.2); y = wrapped(c, note, .3 * inch, y - .03 * inch, 3.65 * inch, 8)
        y -= .12 * inch
    c.save()


def foldout() -> None:
    points = []
    root = ET.parse(DATA / "trail" / "GC_CCT.gpx").getroot()
    for point in root.iter():
        if point.tag.endswith("trkpt"):
            points.append((float(point.attrib["lat"]), float(point.attrib["lon"])))
    lats, lons = zip(*points)
    margin_x, margin_y = .35 * inch, .6 * inch
    def project(lat: float, lon: float) -> tuple[float, float]:
        return (margin_x + (lon - min(lons)) / (max(lons) - min(lons)) * (MAP_W - 2 * margin_x), margin_y + (lat - min(lats)) / (max(lats) - min(lats)) * (MAP_H - 2 * margin_y))
    c = canvas.Canvas(str(FOLDOUT), pagesize=(MAP_W, MAP_H))
    c.setFillColor(HexColor("#f5f2e8")); c.rect(0, 0, MAP_W, MAP_H, fill=1, stroke=0)
    c.setStrokeColor(HexColor("#173f36")); c.setLineWidth(2); path = c.beginPath()
    x, y = project(*points[0]); path.moveTo(x, y)
    for point in points[1:]: path.lineTo(*project(*point))
    c.drawPath(path, stroke=1, fill=0)
    c.setStrokeColor(HexColor("#777777")); c.setDash(4, 3); c.setLineWidth(.4)
    for panel in range(1, 6): c.line(panel * 4.25 * inch, 0, panel * 4.25 * inch, MAP_H)
    c.setDash(); c.setFillColor(HexColor("#173f36")); c.setFont("Helvetica-Bold", 16); c.drawString(.35 * inch, MAP_H - .35 * inch, "Fairfax Cross County Trail - detachable six-panel fold-out")
    c.setFont("Helvetica", 7); c.drawRightString(MAP_W - .35 * inch, MAP_H - .33 * inch, "North is to the right")
    qr(c, SITE_URL, MAP_W - 1.15 * inch, .28 * inch, .75 * inch); qr(c, GPX_URL, MAP_W - 2.05 * inch, .28 * inch, .75 * inch)
    c.setFont("Helvetica", 6); c.drawRightString(MAP_W - 1.15 * inch, .18 * inch, "Website"); c.drawRightString(MAP_W - 2.05 * inch, .18 * inch, "Full GPX")
    c.save()


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    booklet(); foldout()
    print(f"Wrote {BOOKLET}\nWrote {FOLDOUT}")
