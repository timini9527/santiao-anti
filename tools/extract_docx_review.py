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
    """
    全量提取并审查指定 DOCX 文档的内容、排版结构、修订标记及内嵌多媒体资源。

    :param source: 待审查的源 DOCX 文件路径
    :param output: 审查报告及导出媒体文件的输出目录路径
    """
    output.mkdir(parents=True, exist_ok=True)
    media_dir = output / "media"
    media_dir.mkdir(parents=True, exist_ok=True)

    # 1. 基础元数据统计
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

    # 2. 按文档物理顺序遍历正文子节点（段落与表格）
    paragraph_index = 0
    table_index = 0
    body = document.element.body
    for child in body.iterchildren():
        if isinstance(child, CT_P):
            # 处理段落内容与对应样式
            paragraph_index += 1
            paragraph = Paragraph(child, document)
            text = paragraph.text.replace("\t", "<TAB>").replace("\n", "<BR>")
            style = paragraph.style.name if paragraph.style is not None else ""
            if text.strip() or style:
                lines.append(f"[P{paragraph_index:03d}][{style}] {text}")
        elif isinstance(child, CT_Tbl):
            # 处理表格行列与单元格数据
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

    # 3. 深度解析底层 OOXML 结构与修订审阅标记
    with ZipFile(source) as archive:
        names = archive.namelist()
        lines.extend(["", "=== OOXML STRUCTURE ==="])
        # 检查关键部件 XML 文件是否存在
        for key in (
            "word/comments.xml",
            "word/footnotes.xml",
            "word/endnotes.xml",
            "word/numbering.xml",
            "word/header1.xml",
            "word/footer1.xml",
        ):
            lines.append(f"{key}: {key in names}")

        # 解析主文档 XML 中的修订记录 (Track Changes) 与批注标记数量
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

        # 4. 提取内嵌富媒体文件（图片、图表等）并获取图像元数据
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
            except Exception as error:  # 部分格式（如 SVG、EMF 等矢量图）做异常兜底说明
                details = f"unreadable:{type(error).__name__}"
            lines.append(
                f"{index:02d}. {name} -> {target.name} "
                f"bytes={len(data)} {details}"
            )

    # 5. 输出审查报告文件并打印汇总信息
    report = output / "report.txt"
    report.write_text("\n".join(lines), encoding="utf-8")
    print(report)
    print(
        f"paragraphs={paragraph_index} tables={table_index} media={len(media)}"
    )


def main() -> None:
    """命令行主执行入口，解析源文档路径与输出目录参数"""
    parser = argparse.ArgumentParser(
        description="DOCX 文档内容、结构、修订与富媒体提取审查工具"
    )
    parser.add_argument("source", type=Path, help="待提取的源 DOCX 文件路径")
    parser.add_argument("output", type=Path, help="审查产物输出目录路径")
    args = parser.parse_args()
    extract(args.source, args.output)


if __name__ == "__main__":
    main()
