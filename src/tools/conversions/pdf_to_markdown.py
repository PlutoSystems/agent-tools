import sys
import os
from tools.conversions import md_converter


def pdf_to_markdown(file_path: str, output_path: str | None = None) -> str:
    if not os.path.isfile(file_path):
        return f"Error: File not found: {file_path}"
    if not file_path.lower().endswith(".pdf"):
        return "Error: File must be a .pdf"

    result = md_converter.convert(file_path)
    markdown = result.markdown

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(markdown)
        return f"Saved markdown to {output_path}"

    return markdown


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: pdf_to_markdown.py <file_path> [output_path]")
        sys.exit(1)
    output = sys.argv[2] if len(sys.argv) > 2 else None
    print(pdf_to_markdown(sys.argv[1], output))
