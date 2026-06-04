# SmartRecipe — Walkthrough

## Ringkasan

Aplikasi web Flask untuk pencarian semantik resep masakan Indonesia berbasis RDF, Ontologi, dan SPARQL telah selesai dibangun. Aplikasi terhubung ke Apache Jena Fuseki (triplestore) dan mendukung filter berdasarkan kondisi kesehatan.

## File yang Dibuat

### Root Project
| File | Deskripsi |
|------|-----------|
| [SETUP_FUSEKI.md](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/SETUP_FUSEKI.md) | Panduan lengkap setup Apache Jena Fuseki (download, install, create dataset, upload TTL, verifikasi) |

### `smartrecipe-web/` — Aplikasi Flask

| File | Deskripsi |
|------|-----------|
| [requirements.txt](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/requirements.txt) | Dependencies: flask, requests |
| [app.py](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/app.py) | Entry point Flask — routes untuk `/`, `/api/recipes`, `/resep/<uri>` |
| [sparql_queries.py](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/sparql_queries.py) | Semua fungsi SPARQL query (Q1–Q6) — terpisah dari app.py |

### Templates (Jinja2)

| File | Deskripsi |
|------|-----------|
| [base.html](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/templates/base.html) | Layout utama — navbar glass, footer, Tailwind CDN, Inter font |
| [index.html](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/templates/index.html) | Halaman utama — hero, search bar, filter kondisi & kategori, grid resep |
| [detail.html](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/templates/detail.html) | Detail resep — steps, bahan (highlight merah jika berbahaya), tabel gizi |

### Static Assets

| File | Deskripsi |
|------|-----------|
| [style.css](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/static/css/style.css) | Glassmorphism, animations, dark theme |
| [main.js](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/smartrecipe-web/static/js/main.js) | AJAX handler, debounce search, dynamic card rendering |

## Arsitektur

```
Browser → Flask (app.py) → sparql_queries.py → HTTP GET → Fuseki (:3030)
                                                              ↓
                                                         smartrecipe.ttl
                                                        (12.284 triples)
```

### Fitur
1. **Search bar** — pencarian nama resep (substring matching, case-insensitive)
2. **Filter kondisi kesehatan** — Asam Urat, Hipertensi, Kolesterol Tinggi, Alergi Kacang
3. **Filter kategori** — ayam, ikan, kambing, sapi, tahu, telur, tempe, udang
4. **Kombinasi filter** — keyword + kondisi + kategori bisa aktif bersamaan
5. **AJAX filtering** — filter tanpa reload halaman
6. **Detail resep** — langkah memasak, daftar bahan, highlight bahan berbahaya, tabel gizi
7. **Error handling** — pesan jelas jika Fuseki tidak berjalan

## Cara Menjalankan

### 1. Setup Fuseki (lihat [SETUP_FUSEKI.md](file:///d:/KULIAH/SEMESTER%206/Semantic%20Web/health-recipe-ontology/SETUP_FUSEKI.md))
```cmd
cd C:\Tools\apache-jena-fuseki-5.x.x
fuseki-server.bat
```
Kemudian upload `smartrecipe.ttl` via http://localhost:3030.

### 2. Jalankan Flask
```cmd
cd "d:\KULIAH\SEMESTER 6\Semantic Web\health-recipe-ontology\smartrecipe-web"
pip install -r requirements.txt
python app.py
```

### 3. Buka Browser
👉 http://localhost:5000

## Verifikasi
- ✅ Dependencies terinstall (flask, requests)
- ✅ Semua modul bisa di-import tanpa error
- ⏳ Test end-to-end membutuhkan Fuseki berjalan dengan dataset `smartrecipe` terisi
