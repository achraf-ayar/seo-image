"""Build the JSON report and the Markdown summary from one list of results."""
import json
import os


def build_report(results):
    return {"results": [r.to_dict() for r in results]}


def write_report(results, out_folder):
    path = os.path.join(out_folder, "report.json")
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as fh:
        json.dump(build_report(results), fh, indent=2, ensure_ascii=False)
        fh.write("\n")
    os.replace(tmp, path)
    return path


def _cell(value):
    if value is None or value == "":
        return "-"
    if isinstance(value, list):
        value = ", ".join(value)
    return str(value).replace("|", "\\|").replace("\n", " ")


def to_markdown(results):
    head = ["Original", "New file", "Status", "Alt", "Title", "Description", "Tags",
            "Domain", "Watermark", "Position"]
    lines = ["| " + " | ".join(head) + " |", "|" + "|".join(["---"] * len(head)) + "|"]
    for r in results:
        status = r.status if not r.reason else f"{r.status}: {r.reason}"
        wm = r.watermark_status if not r.watermark_reason else \
            f"{r.watermark_status} ({r.watermark_reason})"
        row = [r.original_filename, r.new_filename, status, r.alt, r.title, r.description,
               r.tags, r.domain, wm, r.watermark_position]
        lines.append("| " + " | ".join(_cell(c) for c in row) + " |")
    ok = sum(1 for r in results if r.status == "ok")
    lines.append("")
    lines.append(f"{ok} of {len(results)} images processed.")
    return "\n".join(lines)
