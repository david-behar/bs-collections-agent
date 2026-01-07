from flask import Blueprint, jsonify, send_file

from . import data_access

fetch_api = Blueprint("fetch_api", __name__, url_prefix="/api")


@fetch_api.route("/cases", methods=["GET"])
def list_cases():
    cases = data_access.list_cases()
    return jsonify({"cases": cases})


@fetch_api.route("/cases/<case_id>", methods=["GET"])
def get_case(case_id: str):
    try:
        payload = data_access.get_case_payload(case_id)
    except KeyError:
        return jsonify({"detail": f"Case {case_id} not found"}), 404
    return jsonify(payload)


@fetch_api.route("/cases/<case_id>/attachments/<doc_type>", methods=["GET"])
def download_attachment(case_id: str, doc_type: str):
    try:
        buffer, filename = data_access.get_attachment_stream(case_id, doc_type)
    except KeyError:
        return jsonify({"detail": "Unsupported attachment type"}), 400
    except FileNotFoundError:
        return jsonify({"detail": "Attachment not found"}), 404

    return send_file(
        buffer,
        mimetype="application/pdf",
        download_name=filename,
        as_attachment=False,
    )
