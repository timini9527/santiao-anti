from __future__ import annotations

import argparse
from io import BytesIO
from pathlib import Path
from zipfile import ZipFile

from PIL import Image
from docx import Document
from docx.oxml.table import CT_Tbl
from docx.oxml.text.paragraph import CT_P
from docx.table import Table
from docx.text.paragraph import Paragraph
from lxml import etree


def extract(source: Path, output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    media_dir = output / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    lines: list[str] = [
        f"SOURCE: {source}",
        f"SIZE: {source.stat().st_size}",
    ]

    document = Document(str(source))
    lines.extend(
        [
            f"SECTIONS: {len(document.sections)}",
            f"INLINE_SHAPES: {len(document.inline_shapes)}",
            "",
            "=== BODY IN DOCUMENT ORDER ===",
        ]
    )

    paragraph_index = 0
    table_index = 0
    body = document.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            paragraph_index += 1
            paragraph = Paragraph(child, document)
            text = paragraph.text.replace("\t", "<TAB>").replace("\n", "<BR>")
            style = paragraph.style.name if paragraph.style is not None else ""
            if text.strip() or style:
                lines.append(f"[P{paragraph_index:03d}][{style}] {text}")
        elif isinstance(child, CT_Tbl):
            table_index += 1
            table = Table(child, document)
            lines.append(
                f"[TABLE {table_index}] rows={len(table.rows)} cols={len(table.columns)}"
            )
            for row_index, row in enumerate(table.rows, 1):
                values = [
                    cell.text.replace("\t", "<TAB>").replace("\n", "<BR>")
                    for cell in row.cells
                ]
                lines.append(f"  R{row_index:02d}: " + " || ".join(values))
            lines.append(f"[/TABLE {table_index}]")

    with ZipFile(source) as archive:
        names = archive.namelist()
        lines.extend(["", "=== OOXML STRUCTURE ==="])
        for key in (
            "word/comments.xml",
            "word/footnotes.xml",
            "word/endnotes.xml",
            "word/numbering.xml",
            "word/header1.xml",
            "word/footer1.xml",
        ):
            lines.append(f"{key}: {key in names}")

        root = etree.fromstring(archive.read("word/document.xml"))
        namespaces = {
            "w": "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
        }
        for tag in (
            "ins",
            "del",
            "moveFrom",
            "moveTo",
            "commentRangeStart",
            "commentReference",
        ):
            count = len(root.xpath(f".//w:{tag}", namespaces=namespaces))
            lines.append(f"w:{tag}: {count}")

        media = sorted(
            name
            for name in names
            if name.startswith("word/media/") and not name.endswith("/")
        )
        lines.extend([f"MEDIA_COUNT: {len(media)}", "", "=== MEDIA ==="])
        for index, name in enumerate(media, 1):
            data = archive.read(name)
            target = media_dir / Path(name).name
            target.write_bytes(data)
            try:
                image = Image.open(BytesIO(data))
                details = (
                    f"{image.width}x{image.height} {image.mode} {image.format}"
                )
            except Exception as error:  # Media can also be SVG/EMF.
                details = f"unreadable:{type(error).__name__}"
            lines.append(
                f"{index:02d}. {name} -> {target.name} "
                f"bytes={len(data)} {details}"
            )

    report = output / "report.txt"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)
    print(
        f"paragraphs={paragraph_index} tables={table_index} media={len(media)}"
    )


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    extract(args.source, args.output)


if __name__ == "__main__":
    main()
