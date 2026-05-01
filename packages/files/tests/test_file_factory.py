import io
import json

import pytest

from agentos_files import FileAdapterFactory, UnsupportedFormatError


def test_text_plain():
    doc = FileAdapterFactory.normalize(b"hello world", filename="note.txt")
    assert doc.text == "hello world"
    assert doc.metadata["adapter"] == "text"
    assert doc.tabular is None


def test_markdown_passthrough():
    doc = FileAdapterFactory.normalize(b"# Title\n\nbody", filename="readme.md")
    assert "Title" in doc.text


def test_csv_yields_tabular():
    payload = b"name,age\nAna,28\nLuis,35"
    doc = FileAdapterFactory.normalize(payload, filename="people.csv")
    assert doc.tabular == [{"name": "Ana", "age": 28}, {"name": "Luis", "age": 35}]
    assert doc.metadata["rows"] == 2
    assert "name,age" in doc.text


def test_json_array_of_records():
    payload = json.dumps([{"id": 1, "x": "a"}, {"id": 2, "x": "b"}]).encode()
    doc = FileAdapterFactory.normalize(payload, filename="data.json")
    assert doc.tabular == [{"id": 1, "x": "a"}, {"id": 2, "x": "b"}]
    assert doc.metadata["parsed"] is True


def test_json_object_with_nested_records():
    payload = json.dumps({"items": [{"a": 1}, {"a": 2}]}).encode()
    doc = FileAdapterFactory.normalize(payload, filename="nested.json")
    assert doc.tabular == [{"a": 1}, {"a": 2}]


def test_xlsx_multi_sheet():
    pytest.importorskip("openpyxl")
    import pandas as pd

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        pd.DataFrame({"x": [1, 2]}).to_excel(writer, sheet_name="A", index=False)
        pd.DataFrame({"y": [3, 4]}).to_excel(writer, sheet_name="B", index=False)
    doc = FileAdapterFactory.normalize(buffer.getvalue(), filename="book.xlsx")
    assert doc.metadata["sheets"] == ["A", "B"]
    assert any(r.get("_sheet") == "A" for r in doc.tabular or [])


def test_html_strips_scripts():
    payload = b"<html><head><title>T</title></head><body><script>x=1</script><p>hi</p></body></html>"
    doc = FileAdapterFactory.normalize(payload, filename="page.html")
    assert "x=1" not in doc.text
    assert "hi" in doc.text
    assert doc.metadata["title"] == "T"


def test_unsupported_extension_raises():
    with pytest.raises(UnsupportedFormatError):
        FileAdapterFactory.normalize(b"...", filename="thing.exe")


def test_mime_fallback_when_no_filename():
    doc = FileAdapterFactory.normalize(b"hello", mime="text/plain")
    assert doc.text == "hello"
