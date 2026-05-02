import csv
import io
from typing import Any

from fastapi.responses import StreamingResponse
from pydantic import BaseModel


def to_csv_response(items: list[BaseModel], filename: str) -> StreamingResponse:
    if not items:
        return StreamingResponse(
            iter([""]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    rows = [item.model_dump() for item in items]
    # Flatten nested dicts/lists to strings for CSV
    def flatten(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, (dict, list)):
            return str(v)
        return str(v)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    for row in rows:
        writer.writerow({k: flatten(v) for k, v in row.items()})

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
