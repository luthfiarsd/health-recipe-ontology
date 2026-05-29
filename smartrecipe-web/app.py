"""
app.py — Entry Point Aplikasi Flask SmartRecipe
=================================================
Aplikasi pencarian semantik resep masakan Indonesia.
Menggunakan SPARQL query ke Apache Jena Fuseki (triplestore)
untuk memahami hubungan antar-entitas data secara semantik.
"""

from flask import Flask, render_template, request, jsonify, abort
from urllib.parse import quote, unquote
import requests

from sparql_queries import (
    search_recipes,
    get_recipe_detail,
    get_dangerous_ingredients,
    get_categories,
    CONDITION_MAP,
    CATEGORY_LIST,
)

app = Flask(__name__)


# ─── Helper: Cek koneksi ke Fuseki ──────────────────────────────────────────
def check_fuseki_connection() -> bool:
    """Periksa apakah Fuseki triplestore dapat dijangkau."""
    try:
        resp = requests.get("http://localhost:3030/$/ping", timeout=5)
        return resp.status_code == 200
    except requests.ConnectionError:
        return False


# ═══════════════════════════════════════════════════════════════════════════════
# Route: Halaman Utama
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/")
def index():
    """
    Halaman utama — menampilkan search bar, filter, dan grid resep.
    Menggunakan Jinja2 template rendering.
    Data awal (semua resep) di-load server-side.
    Filter selanjutnya dilakukan via AJAX ke /api/recipes.
    """
    fuseki_ok = check_fuseki_connection()
    recipes = []
    categories = CATEGORY_LIST
    error_msg = None

    if fuseki_ok:
        try:
            recipes = search_recipes()
            categories = get_categories() or CATEGORY_LIST
        except Exception as e:
            error_msg = f"Gagal mengambil data dari Fuseki: {str(e)}"
    else:
        error_msg = (
            "⚠️ Apache Jena Fuseki tidak dapat dijangkau di http://localhost:3030. "
            "Pastikan Fuseki sudah berjalan sebelum membuka aplikasi ini."
        )

    return render_template(
        "index.html",
        recipes=recipes,
        categories=categories,
        conditions=CONDITION_MAP,
        error_msg=error_msg,
        quote=quote,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# API: AJAX endpoint untuk filter resep secara dinamis
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/api/recipes")
def api_recipes():
    """
    AJAX endpoint — mengembalikan JSON list resep berdasarkan filter.
    Dipanggil dari JavaScript saat user mengubah filter/search.

    Query params:
        keyword   : Kata kunci pencarian nama resep
        condition : Key kondisi kesehatan (misal "asam_urat")
        category  : Nama kategori (misal "ayam")
    """
    keyword = request.args.get("keyword", "").strip()
    condition = request.args.get("condition", "").strip()
    category = request.args.get("category", "").strip()

    try:
        recipes = search_recipes(
            keyword=keyword,
            condition=condition,
            category=category,
        )
        # Tambahkan encoded URI untuk link ke detail
        for r in recipes:
            r["encoded_uri"] = quote(r["menu"], safe="")
        return jsonify({"success": True, "data": recipes})
    except requests.ConnectionError:
        return jsonify({
            "success": False,
            "error": "Fuseki tidak dapat dijangkau",
        }), 503
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e),
        }), 500


# ═══════════════════════════════════════════════════════════════════════════════
# Route: Halaman Detail Resep
# ═══════════════════════════════════════════════════════════════════════════════
@app.route("/resep/<path:recipe_uri_encoded>")
def recipe_detail(recipe_uri_encoded):
    """
    Halaman detail resep — menampilkan langkah memasak, bahan, dan info gizi.

    URI resep di-encode saat dikirim via URL dan di-decode di sini.
    Contoh: /resep/http%3A%2F%2Fsmartrecipe.org%2Fdata%23resep_Rendang_Sapi

    Langkah memasak disimpan dalam RDF sebagai satu string dengan delimiter "--",
    yang di-split menjadi list untuk ditampilkan per step.
    """
    # Decode URI resep dari URL
    recipe_uri = unquote(recipe_uri_encoded)

    try:
        detail = get_recipe_detail(recipe_uri)
        if not detail:
            abort(404)

        # Ambil daftar bahan berbahaya untuk highlight
        dangerous = get_dangerous_ingredients(recipe_uri)

        # Buat set nama bahan berbahaya untuk lookup cepat di template
        dangerous_map = {}
        for d in dangerous:
            name = d["namaBahan"]
            if name not in dangerous_map:
                dangerous_map[name] = []
            dangerous_map[name].append({
                "gizi": d["namaGizi"],
                "kondisi": d["namaKondisi"],
            })

        # Split langkah memasak (delimiter: --)
        steps_raw = detail["info"].get("steps", "")
        steps = [s.strip() for s in steps_raw.split("--") if s.strip()]

        return render_template(
            "detail.html",
            info=detail["info"],
            ingredients=detail["ingredients"],
            dangerous_map=dangerous_map,
            steps=steps,
            recipe_uri=recipe_uri,
        )

    except requests.ConnectionError:
        return render_template(
            "detail.html",
            info=None,
            error_msg="Fuseki tidak dapat dijangkau. Pastikan server berjalan.",
        )
    except Exception as e:
        return render_template(
            "detail.html",
            info=None,
            error_msg=f"Terjadi kesalahan: {str(e)}",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Error Handlers
# ═══════════════════════════════════════════════════════════════════════════════
@app.errorhandler(404)
def page_not_found(e):
    """Halaman 404 — resep tidak ditemukan."""
    return render_template(
        "detail.html",
        info=None,
        error_msg="Resep tidak ditemukan.",
    ), 404


# ─── Main ────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    print("=" * 60)
    print("  SmartRecipe — Semantic Recipe Search")
    print("  http://localhost:5000")
    print("=" * 60)

    if not check_fuseki_connection():
        print("\n  ⚠️  WARNING: Fuseki tidak terdeteksi di http://localhost:3030")
        print("  Pastikan Apache Jena Fuseki sudah berjalan!\n")
    else:
        print("\n  ✅ Fuseki terhubung di http://localhost:3030\n")

    app.run(debug=True, port=5000)
