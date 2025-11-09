#!/usr/bin/env python3
"""
Create a sample PDF for testing conversion methods
"""

from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
import sys


def create_sample_pdf(filename="sample.pdf", num_pages=3):
    """Create a multi-page PDF with various content"""

    c = canvas.Canvas(filename, pagesize=letter)
    width, height = letter

    # Page 1: Text content
    c.setFont("Helvetica-Bold", 24)
    c.drawString(inch, height - inch, "PDF to PNG Conversion Test")

    c.setFont("Helvetica", 14)
    c.drawString(inch, height - 1.5*inch, "Page 1 of 3")

    c.setFont("Helvetica", 12)
    y = height - 2*inch
    text_lines = [
        "This is a sample PDF document created for testing",
        "various PDF to PNG conversion methods.",
        "",
        "This document contains:",
        "- Text in various fonts and sizes",
        "- Shapes and colors",
        "- Multiple pages",
    ]

    for line in text_lines:
        c.drawString(inch, y, line)
        y -= 0.3*inch

    # Add some colored rectangles
    colors = [
        HexColor("#FF0000"),
        HexColor("#00FF00"),
        HexColor("#0000FF"),
    ]

    x_start = inch
    for i, color in enumerate(colors):
        c.setFillColor(color)
        c.rect(x_start + i*1.5*inch, 2*inch, inch, inch, fill=1)

    c.showPage()

    # Page 2: Shapes and patterns
    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, height - inch, "Page 2: Shapes and Patterns")

    c.setFont("Helvetica", 14)
    c.drawString(inch, height - 1.5*inch, "Page 2 of 3")

    # Draw circles
    c.setStrokeColor(HexColor("#FF00FF"))
    c.setFillColor(HexColor("#FFFF00"))
    for i in range(5):
        c.circle(inch + i*1.2*inch, height - 3*inch, 0.3*inch, fill=1)

    # Draw lines
    c.setStrokeColor(HexColor("#000000"))
    c.setLineWidth(2)
    for i in range(10):
        y_pos = height - 5*inch - i*0.2*inch
        c.line(inch, y_pos, width - inch, y_pos)

    c.showPage()

    # Page 3: Grid and text
    c.setFont("Helvetica-Bold", 18)
    c.drawString(inch, height - inch, "Page 3: Grid Pattern")

    c.setFont("Helvetica", 14)
    c.drawString(inch, height - 1.5*inch, "Page 3 of 3")

    # Draw a grid
    c.setStrokeColor(HexColor("#CCCCCC"))
    c.setLineWidth(0.5)

    grid_size = 0.5*inch
    for x in range(int(inch), int(width - inch), int(grid_size)):
        c.line(x, 2*inch, x, height - 2.5*inch)

    for y in range(int(2*inch), int(height - 2.5*inch), int(grid_size)):
        c.line(inch, y, width - inch, y)

    # Add some text
    c.setFont("Courier", 10)
    c.setFillColor(HexColor("#000000"))
    y = height - 3*inch
    sample_code = [
        "def convert_pdf_to_png(pdf_path):",
        "    '''Convert PDF to PNG images'''",
        "    images = convert_from_path(pdf_path)",
        "    for i, image in enumerate(images):",
        "        image.save(f'page_{i}.png')",
    ]

    for line in sample_code:
        c.drawString(1.5*inch, y, line)
        y -= 0.25*inch

    c.save()
    print(f"Created {filename} with {num_pages} pages")


if __name__ == "__main__":
    create_sample_pdf()
