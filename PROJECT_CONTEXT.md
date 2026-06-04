# SmartRecipe — Project Context for AI IDE

> **Mata Kuliah**: Semantic Web (Online Course, UNPAD Luhung Live)  
> **Tujuan Proyek**: Membangun aplikasi pencarian semantik resep masakan Indonesia berbasis RDF, Ontologi, dan SPARQL

---

## 1. Ringkasan Proyek

SmartRecipe adalah sistem pencarian semantik resep masakan Indonesia yang memfilter resep berdasarkan **kondisi kesehatan pengguna**. Sistem ini menggunakan teknologi Semantic Web (RDF + Ontologi + SPARQL) untuk memahami hubungan antar-entitas data — bukan sekadar keyword matching.

---

## 2. Tech Stack

| Layer | Teknologi |
|---|---|
| Backend | Python + Flask |
| Frontend | HTML + Tailwind CSS + Vanilla JS (Jinja2 templates) |
| Database Semantik | Apache Jena Fuseki (Triplestore, local) |
| Data Format | RDF Turtle (`.ttl`) |
| Query Language | SPARQL 1.1 |

---

## 3. Status Proyek Saat Ini

✅ **Sudah selesai:**
- File RDF `smartrecipe.ttl` sudah dibuat dan siap di-upload ke Fuseki
- Ontologi schema sudah didefinisikan (classes, object properties, data properties)
- 40 resep dari 8 kategori sudah terkonversi ke RDF
- Relasi bahan → kandungan berbahaya → kondisi kesehatan sudah terhubung

🔲 **Belum dibuat (task sekarang):**
- Aplikasi website Flask (backend + frontend)

---

## 4. Struktur Ontologi

### Namespace
```turtle
@prefix sr:   <http://smartrecipe.org/ontology#> .
@prefix data: <http://smartrecipe.org/data#> .
```

### Classes
| Class URI | Deskripsi |
|---|---|
| `sr:MenuMasakan` | Hidangan/resep masakan (contoh: Rendang Sapi, Soto Ayam) |
| `sr:BahanBaku` | Komponen bahan mentah (contoh: Udang, Santan, Garam) |
| `sr:KandunganGizi` | Zat gizi/senyawa berbahaya (contoh: PurinTinggi) |
| `sr:KondisiKesehatan` | Penyakit/kondisi medis pengguna (contoh: AsamUrat) |

### Object Properties
| Property | Domain → Range | Deskripsi |
|---|---|---|
| `sr:hasIngredient` | `MenuMasakan → BahanBaku` | Resep memiliki bahan baku |
| `sr:containsNutrient` | `BahanBaku → KandunganGizi` | Bahan mengandung zat berbahaya |
| `sr:isAvoidedBy` | `KandunganGizi → KondisiKesehatan` | Zat harus dihindari kondisi ini |
| `sr:hasCategory` | `MenuMasakan → BahanBaku` | Kategori bahan utama resep |

### Data Properties (pada `sr:MenuMasakan`)
| Property | Tipe | Deskripsi |
|---|---|---|
| `rdfs:label` | `string@id` | Nama resep dalam Bahasa Indonesia |
| `dcterms:identifier` | `string` | ID unik resep (contoh: `REC_AYAM_001`) |
| `dcterms:subject` | `string` | Kategori bahan utama |
| `sr:hasSteps` | `xsd:string` | Langkah-langkah memasak |
| `sr:hasSourceURL` | `xsd:anyURI` | URL sumber resep (Cookpad) |
| `sr:hasLoves` | `xsd:integer` | Jumlah likes resep |

### Data Properties (pada `sr:BahanBaku`)
| Property | Tipe | Deskripsi |
|---|---|---|
| `rdfs:label` | `string@id` | Nama bahan |
| `dcterms:identifier` | `string` | ID unik bahan (contoh: `NUT-0001`) |
| `sr:hasCalories` | `xsd:float` | Kalori (kcal per 100g) |
| `sr:hasProtein` | `xsd:float` | Protein (gram) |
| `sr:hasFat` | `xsd:float` | Lemak (gram) |
| `sr:hasCarbohydrate` | `xsd:float` | Karbohidrat (gram) |
| `sr:hasImageURL` | `xsd:anyURI` | URL gambar bahan |

---

## 5. Data dalam RDF

### Kondisi Kesehatan & Pantangan
| URI | Label | Kandungan Dihindari | Contoh Bahan Berbahaya |
|---|---|---|---|
| `data:AsamUrat` | Asam Urat | `data:PurinTinggi` | udang, jeroan, emping, kangkung, kambing |
| `data:Hipertensi` | Hipertensi | `data:NatriumTinggi` | garam, terasi, ikan asin, kaldu bubuk, kecap asin |
| `data:KolesterolTinggi` | Kolesterol Tinggi | `data:LemakJenuhTinggi` | santan, jeroan, kulit ayam, mentega, margarin |
| `data:AlergiKacang` | Alergi Kacang | `data:AlergenKacang` | kacang tanah, tempe, bumbu kacang |

### Kategori Resep
8 kategori tersedia: `ayam`, `ikan`, `kambing`, `sapi`, `tahu`, `telur`, `tempe`, `udang`

### Statistik Data
- Total triple RDF: **12.284**
- Total resep (MenuMasakan): **40**
- Total bahan (BahanBaku): **1.617**
- Total kandungan berbahaya (KandunganGizi): **4**
- Total kondisi kesehatan: **4**

---

## 6. SPARQL Endpoint

| Item | Nilai |
|---|---|
| URL Fuseki | `http://localhost:3030` |
| Dataset name | `smartrecipe` |
| Query endpoint | `http://localhost:3030/smartrecipe/query` |
| Update endpoint | `http://localhost:3030/smartrecipe/update` |
| Method | HTTP GET atau POST |
| Format response | `application/sparql-results+json` |

### Cara request ke Fuseki dari Python:
```python
import requests

def sparql_query(query: str) -> dict:
    response = requests.get(
        "http://localhost:3030/smartrecipe/query",
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"}
    )
    response.raise_for_status()
    return response.json()
```

---

## 7. SPARQL Query Referensi

### Q1 — Ambil semua kategori yang tersedia
```sparql
PREFIX sr: <http://smartrecipe.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?kategori WHERE {
    ?menu a sr:MenuMasakan ;
          dcterms:subject ?kategori .
}
ORDER BY ?kategori
```

### Q2 — Filter resep berdasarkan kondisi kesehatan
```sparql
PREFIX sr:   <http://smartrecipe.org/ontology#>
PREFIX data: <http://smartrecipe.org/data#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?menu ?namaMenu ?kategori ?loves WHERE {
    ?menu a sr:MenuMasakan ;
          rdfs:label ?namaMenu ;
          dcterms:subject ?kategori ;
          sr:hasLoves ?loves .
    FILTER NOT EXISTS {
        ?menu sr:hasIngredient ?bahan .
        ?bahan sr:containsNutrient ?gizi .
        ?gizi sr:isAvoidedBy data:AsamUrat .   # ← ganti sesuai kondisi
    }
}
ORDER BY DESC(?loves)
```

### Q3 — Filter resep + kondisi + kategori sekaligus
```sparql
PREFIX sr:   <http://smartrecipe.org/ontology#>
PREFIX data: <http://smartrecipe.org/data#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?menu ?namaMenu ?kategori ?loves WHERE {
    ?menu a sr:MenuMasakan ;
          rdfs:label ?namaMenu ;
          dcterms:subject ?kategori ;
          sr:hasLoves ?loves .
    FILTER(?kategori = "ayam")                  # ← ganti sesuai filter
    FILTER NOT EXISTS {
        ?menu sr:hasIngredient ?bahan .
        ?bahan sr:containsNutrient ?gizi .
        ?gizi sr:isAvoidedBy data:AsamUrat .    # ← ganti sesuai kondisi
    }
}
ORDER BY DESC(?loves)
```

### Q4 — Pencarian resep berdasarkan nama (CONTAINS)
```sparql
PREFIX sr:   <http://smartrecipe.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>

SELECT DISTINCT ?menu ?namaMenu ?kategori ?loves WHERE {
    ?menu a sr:MenuMasakan ;
          rdfs:label ?namaMenu ;
          dcterms:subject ?kategori ;
          sr:hasLoves ?loves .
    FILTER(CONTAINS(LCASE(?namaMenu), LCASE("ayam goreng")))  # ← keyword
}
ORDER BY DESC(?loves)
```

### Q5 — Detail lengkap satu resep (termasuk bahan + info gizi)
```sparql
PREFIX sr:   <http://smartrecipe.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

SELECT ?namaMenu ?kategori ?steps ?sourceURL ?loves
       ?namaBahan ?kalori ?protein ?lemak ?karbo ?imgBahan WHERE {
    BIND(<http://smartrecipe.org/data#resep_Rendang_Sapi> AS ?menu)  # ← URI resep
    ?menu a sr:MenuMasakan ;
          rdfs:label ?namaMenu ;
          dcterms:subject ?kategori ;
          sr:hasSteps ?steps ;
          sr:hasLoves ?loves .
    OPTIONAL { ?menu sr:hasSourceURL ?sourceURL }
    OPTIONAL {
        ?menu sr:hasIngredient ?bahan .
        ?bahan rdfs:label ?namaBahan .
        OPTIONAL { ?bahan sr:hasCalories     ?kalori }
        OPTIONAL { ?bahan sr:hasProtein      ?protein }
        OPTIONAL { ?bahan sr:hasFat          ?lemak }
        OPTIONAL { ?bahan sr:hasCarbohydrate ?karbo }
        OPTIONAL { ?bahan sr:hasImageURL     ?imgBahan }
    }
}
```

### Q6 — Deteksi bahan berbahaya dalam sebuah resep
```sparql
PREFIX sr:   <http://smartrecipe.org/ontology#>
PREFIX data: <http://smartrecipe.org/data#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?namaBahan ?namaGizi ?namaKondisi WHERE {
    BIND(<http://smartrecipe.org/data#resep_Rendang_Sapi> AS ?menu)  # ← URI resep
    ?menu sr:hasIngredient ?bahan .
    ?bahan rdfs:label ?namaBahan ;
           sr:containsNutrient ?gizi .
    ?gizi rdfs:label ?namaGizi ;
          sr:isAvoidedBy ?kondisi .
    ?kondisi rdfs:label ?namaKondisi .
}
```

---

## 8. Struktur Folder Proyek Flask

```
smartrecipe-web/
├── app.py                  # Entry point Flask
├── sparql_queries.py       # Semua fungsi SPARQL query
├── requirements.txt
├── static/
│   ├── css/
│   │   └── style.css
│   └── js/
│       └── main.js
└── templates/
    ├── base.html           # Layout utama (navbar, footer)
    ├── index.html          # Halaman utama (search + filter)
    └── detail.html         # Halaman detail resep
```

---

## 9. Fitur Website yang Harus Dibangun

### Halaman Utama (`/`) — `index.html`
1. **Search bar** — cari resep berdasarkan nama (trigger SPARQL Q4)
2. **Filter kondisi kesehatan** — dropdown pilih satu kondisi (AsamUrat / Hipertensi / KolesterolTinggi / AlergiKacang), trigger SPARQL Q2
3. **Filter kategori bahan** — dropdown/checkbox pilih kategori (ayam/ikan/sapi/dll), trigger SPARQL Q3
4. **Grid kartu resep** — tampilkan hasil: nama resep, kategori, jumlah loves
5. **Filter boleh dikombinasikan** — kondisi + kategori + keyword bisa aktif bersamaan

### Halaman Detail (`/resep/<recipe_uri_encoded>`) — `detail.html`
1. **Judul resep** dan metadata (kategori, loves, link sumber)
2. **Langkah memasak** — dari `sr:hasSteps`, tampilkan per step
3. **Daftar bahan** — tampilkan semua bahan resep
4. **Highlight bahan berbahaya** — bahan yang memiliki `sr:containsNutrient` ditampilkan dengan **latar merah/highlight merah** beserta label kandungan berbahayanya (contoh: "⚠️ Udang — mengandung Zat Purin Tinggi")
5. **Tabel info gizi** — untuk bahan yang memiliki data gizi dari nutrition.csv (kalori, protein, lemak, karbohidrat)

---

## 10. Aturan Penting saat Generate Kode

1. **Semua query ke Fuseki** harus melalui fungsi di `sparql_queries.py`, bukan inline di `app.py`
2. **Kondisi kesehatan** di SPARQL menggunakan URI `data:NamaKondisi` (contoh: `data:AsamUrat`) — bukan string label
3. **URI resep** perlu di-encode saat dikirim via URL (`urllib.parse.quote`) dan di-decode di backend
4. **Fuseki harus berjalan** di `http://localhost:3030` sebelum Flask dijalankan — tambahkan error handling jika Fuseki tidak dapat dijangkau
5. **Jinja2 templates** digunakan untuk render HTML — bukan REST API/JSON response (kecuali untuk AJAX filter di halaman utama)
6. **Tailwind CSS** di-load via CDN di `base.html` — tidak perlu npm/build step
7. **Langkah memasak** di RDF tersimpan dalam satu string dengan delimiter `--` — perlu di-split saat ditampilkan

### Mapping kondisi kesehatan (untuk form → SPARQL URI):
```python
CONDITION_MAP = {
    "asam_urat":      "data:AsamUrat",
    "hipertensi":     "data:Hipertensi",
    "kolesterol":     "data:KolesterolTinggi",
    "alergi_kacang":  "data:AlergiKacang",
}
```

### Mapping kategori bahan (untuk form → SPARQL filter):
```python
CATEGORY_LIST = ["ayam", "ikan", "kambing", "sapi", "tahu", "telur", "tempe", "udang"]
```

---

## 11. Contoh Response Fuseki (JSON)

```json
{
  "results": {
    "bindings": [
      {
        "menu":     { "type": "uri",     "value": "http://smartrecipe.org/data#resep_Rendang_Sapi" },
        "namaMenu": { "type": "literal", "value": "Rendang Sapi",  "xml:lang": "id" },
        "kategori": { "type": "literal", "value": "sapi" },
        "loves":    { "type": "literal", "value": "127", "datatype": "http://www.w3.org/2001/XMLSchema#integer" }
      }
    ]
  }
}
```

### Helper parsing response:
```python
def parse_bindings(results: dict) -> list[dict]:
    """Ubah SPARQL JSON bindings menjadi list of plain dict."""
    rows = []
    for binding in results.get("results", {}).get("bindings", []):
        rows.append({k: v["value"] for k, v in binding.items()})
    return rows
```

---

## 12. Catatan Akademis

- Proyek ini adalah **Proyek Akhir mata kuliah Semantic Web** — kode harus mencerminkan pemahaman konsep RDF, Ontologi, dan SPARQL
- Setiap query SPARQL sebaiknya diberi **komentar** yang menjelaskan logika reasoning-nya
- Nama variabel dan fungsi yang berkaitan dengan Semantic Web sebaiknya menggunakan terminologi yang tepat (`triple`, `endpoint`, `ontology`, `predicate`, dll)
- Laporan proyek akan menyertakan penjelasan teknis dari kode yang dibuat
