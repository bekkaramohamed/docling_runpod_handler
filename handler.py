import runpod
import base64
import tempfile
from pathlib import Path

from docling.datamodel.pipeline_options import PdfPipelineOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.types.doc import TableItem

# Chargé une seule fois au démarrage du worker
pipeline_options = PdfPipelineOptions(do_ocr=False)
converter = DocumentConverter(
    format_options={"pdf": PdfFormatOption(pipeline_options=pipeline_options)}
)

def handler(job):
    inputs = job["input"]

    if "pdf_base64" not in inputs:
        return {"error": "Champ 'pdf_base64' manquant", "status": "failed"}

    # Décoder le PDF
    pdf_bytes = base64.b64decode(inputs["pdf_base64"])
    tmp_path = None

    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as f:
            f.write(pdf_bytes)
            tmp_path = Path(f.name)

        # Conversion Docling (la partie lourde)
        result = converter.convert(str(tmp_path))
        doc = result.document

        # Sérialiser les items bruts pour ton code local
        items = []
        for idx, (element, level) in enumerate(doc.iterate_items()):
            prov_data = None
            if element.prov:
                prov = element.prov[0]
                b = prov.bbox
                if hasattr(b, 'l') and hasattr(b, 'r'):
                    bbox_raw = [b.l, b.t, b.r, b.b]
                elif hasattr(b, 'to_tuple'):
                    bbox_raw = list(b.to_tuple())
                else:
                    bbox_raw = None

                prov_data = {
                    "page_no": prov.page_no,
                    "bbox": bbox_raw
                }

            # TableItem.text est vide — il faut passer par export_to_markdown(doc=doc)
            # pour récupérer le contenu des cellules (comportement VPS Feb 13).
            if isinstance(element, TableItem):
                text = element.export_to_markdown(doc=doc) if hasattr(element, "export_to_markdown") else ""
            else:
                text = getattr(element, "text", "") or ""

            items.append({
                "idx": idx,
                "level": level,
                "label": str(element.label),
                "text": text,
                "type": type(element).__name__,
                "prov": prov_data,
            })

        return {"items": items, "status": "success"}

    except Exception as e:
        return {"error": str(e), "status": "failed"}

    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()

runpod.serverless.start({"handler": handler})