"""
sparql_queries.py — Modul SPARQL Query untuk SmartRecipe
=========================================================
Semua fungsi yang mengirim SPARQL query ke Apache Jena Fuseki
dikumpulkan di sini. Tidak ada query inline di app.py.

Terminologi Semantic Web:
- Triple: unit data RDF (subject, predicate, object)
- Endpoint: URL SPARQL server yang menerima query
- Ontology: schema/model yang mendefinisikan class dan property
"""

import requests

# ─── Konfigurasi Fuseki Endpoint ─────────────────────────────────────────────
FUSEKI_ENDPOINT = "http://localhost:3030/smartrecipe/query"

# ─── Mapping Kondisi Kesehatan (form value → SPARQL URI) ─────────────────────
CONDITION_MAP = {
    "asam_urat":     "data:AsamUrat",
    "hipertensi":    "data:Hipertensi",
    "kolesterol":    "data:KolesterolTinggi",
    "alergi_kacang": "data:AlergiKacang",
}

# ─── Daftar Kategori Bahan Utama ─────────────────────────────────────────────
CATEGORY_LIST = ["ayam", "ikan", "kambing", "sapi", "tahu", "telur", "tempe", "udang"]

# ─── Prefix SPARQL yang digunakan di semua query ─────────────────────────────
SPARQL_PREFIXES = """
PREFIX sr:      <http://smartrecipe.org/ontology#>
PREFIX data:    <http://smartrecipe.org/data#>
PREFIX rdfs:    <http://www.w3.org/2000/01/rdf-schema#>
PREFIX dcterms: <http://purl.org/dc/terms/>
PREFIX xsd:     <http://www.w3.org/2001/XMLSchema#>
"""


def sparql_query(query: str) -> dict:
    """
    Kirim SPARQL query ke Fuseki endpoint via HTTP GET.

    Args:
        query: String SPARQL query lengkap (termasuk PREFIX)

    Returns:
        dict: Response JSON dari Fuseki berformat SPARQL Results JSON

    Raises:
        requests.ConnectionError: Jika Fuseki tidak dapat dijangkau
        requests.HTTPError: Jika query gagal (syntax error, dll)
    """
    response = requests.get(
        FUSEKI_ENDPOINT,
        params={"query": query},
        headers={"Accept": "application/sparql-results+json"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def parse_bindings(results: dict) -> list[dict]:
    """
    Ubah SPARQL JSON bindings menjadi list of plain dict.

    SPARQL Results JSON memiliki struktur nested:
        results.bindings[i].varName.value
    Fungsi ini menyederhanakan menjadi:
        [{"varName": "value", ...}, ...]

    Args:
        results: Response JSON dari sparql_query()

    Returns:
        list[dict]: List of flat dictionaries
    """
    rows = []
    for binding in results.get("results", {}).get("bindings", []):
        rows.append({k: v["value"] for k, v in binding.items()})
    return rows


# ═══════════════════════════════════════════════════════════════════════════════
# Q1 — Ambil semua kategori yang tersedia
# ═══════════════════════════════════════════════════════════════════════════════
def get_categories() -> list[str]:
    """
    Query semua kategori unik dari triple (menu, dcterms:subject, kategori).

    Reasoning SPARQL:
    - Setiap MenuMasakan memiliki property dcterms:subject berisi kategori
    - SELECT DISTINCT memastikan tidak ada duplikat
    - ORDER BY mengurutkan alfabetis

    Returns:
        list[str]: Daftar nama kategori, misal ["ayam", "ikan", ...]
    """
    query = SPARQL_PREFIXES + """
    SELECT DISTINCT ?kategori WHERE {
        ?menu a sr:MenuMasakan ;
              dcterms:subject ?kategori .
    }
    ORDER BY ?kategori
    """
    results = sparql_query(query)
    return [row["kategori"] for row in parse_bindings(results)]


# ═══════════════════════════════════════════════════════════════════════════════
# Q2/Q3/Q4 — Pencarian resep dengan filter gabungan
# ═══════════════════════════════════════════════════════════════════════════════
def search_recipes(
    keyword: str = "",
    condition: str = "",
    category: str = "",
) -> list[dict]:
    """
    Cari resep dengan kombinasi filter: keyword, kondisi kesehatan, kategori.

    Reasoning SPARQL:
    - Basis: ambil semua MenuMasakan dengan label, kategori, dan loves
    - Jika keyword diisi → FILTER(CONTAINS(LCASE(?namaMenu), LCASE("keyword")))
      Ini melakukan substring matching case-insensitive pada nama resep
    - Jika condition diisi → FILTER NOT EXISTS { ... isAvoidedBy condition }
      Ini menyaring resep yang TIDAK mengandung bahan berbahaya untuk kondisi tsb.
      Logika: eksklusi resep jika ADA bahan yang mengandung zat yang harus dihindari
    - Jika category diisi → FILTER(?kategori = "category")
      Filter berdasarkan kategori bahan utama resep

    Args:
        keyword: Kata kunci pencarian nama resep (opsional)
        condition: Key dari CONDITION_MAP, misal "asam_urat" (opsional)
        category: Nama kategori, misal "ayam" (opsional)

    Returns:
        list[dict]: Hasil pencarian, setiap dict berisi:
            - menu: URI resep
            - namaMenu: Nama resep (string)
            - kategori: Kategori bahan utama
            - loves: Jumlah likes (string, perlu di-cast ke int)
    """
    # Bangun bagian FILTER secara dinamis
    filters = []

    if keyword:
        # Q4: Pencarian berdasarkan nama — substring matching case-insensitive
        safe_keyword = keyword.replace('"', '\\"')
        filters.append(
            f'FILTER(CONTAINS(LCASE(?namaMenu), LCASE("{safe_keyword}")))'
        )

    if category:
        # Q3: Filter berdasarkan kategori bahan utama
        safe_category = category.replace('"', '\\"')
        filters.append(f'FILTER(?kategori = "{safe_category}")')

    # Bangun FILTER NOT EXISTS untuk kondisi kesehatan
    condition_block = ""
    if condition and condition in CONDITION_MAP:
        # Q2: Eksklusi resep yang mengandung bahan berbahaya
        # Reasoning: jika ada triple chain:
        #   menu → hasIngredient → bahan → containsNutrient → gizi → isAvoidedBy → kondisi
        # maka resep tersebut TIDAK aman untuk kondisi ini
        condition_uri = CONDITION_MAP[condition]
        condition_block = f"""
    FILTER NOT EXISTS {{
        ?menu sr:hasIngredient ?bahan .
        ?bahan sr:containsNutrient ?gizi .
        ?gizi sr:isAvoidedBy {condition_uri} .
    }}"""

    filter_str = "\n    ".join(filters)

    query = SPARQL_PREFIXES + f"""
    SELECT DISTINCT ?menu ?namaMenu ?kategori ?loves WHERE {{
        ?menu a sr:MenuMasakan ;
              rdfs:label ?namaMenu ;
              dcterms:subject ?kategori ;
              sr:hasLoves ?loves .
        {filter_str}
        {condition_block}
    }}
    ORDER BY DESC(?loves)
    """
    results = sparql_query(query)
    return parse_bindings(results)


# ═══════════════════════════════════════════════════════════════════════════════
# Q5 — Detail lengkap satu resep (termasuk bahan + info gizi)
# ═══════════════════════════════════════════════════════════════════════════════
def get_recipe_detail(recipe_uri: str) -> dict:
    """
    Ambil detail lengkap satu resep berdasarkan URI-nya.

    Reasoning SPARQL:
    - BIND URI resep sebagai variabel ?menu
    - Ambil semua data property: label, kategori, steps, loves, sourceURL
    - OPTIONAL untuk hasIngredient → ambil data bahan + info gizi
    - OPTIONAL memastikan resep tanpa bahan tetap bisa ditampilkan

    Args:
        recipe_uri: URI lengkap resep, misal "http://smartrecipe.org/data#resep_Rendang_Sapi"

    Returns:
        dict: {
            "info": {"namaMenu": ..., "kategori": ..., "steps": ..., "loves": ..., "sourceURL": ...},
            "ingredients": [{"namaBahan": ..., "kalori": ..., "protein": ..., "lemak": ..., "karbo": ..., "imgBahan": ...}, ...]
        }
    """
    query = SPARQL_PREFIXES + f"""
    SELECT ?namaMenu ?kategori ?steps ?sourceURL ?loves
           ?namaBahan ?kalori ?protein ?lemak ?karbo ?imgBahan WHERE {{
        BIND(<{recipe_uri}> AS ?menu)
        ?menu a sr:MenuMasakan ;
              rdfs:label ?namaMenu ;
              dcterms:subject ?kategori ;
              sr:hasSteps ?steps ;
              sr:hasLoves ?loves .
        OPTIONAL {{ ?menu sr:hasSourceURL ?sourceURL }}
        OPTIONAL {{
            ?menu sr:hasIngredient ?bahan .
            ?bahan rdfs:label ?namaBahan .
            OPTIONAL {{ ?bahan sr:hasCalories     ?kalori }}
            OPTIONAL {{ ?bahan sr:hasProtein      ?protein }}
            OPTIONAL {{ ?bahan sr:hasFat          ?lemak }}
            OPTIONAL {{ ?bahan sr:hasCarbohydrate ?karbo }}
            OPTIONAL {{ ?bahan sr:hasImageURL     ?imgBahan }}
        }}
    }}
    """
    rows = parse_bindings(sparql_query(query))

    if not rows:
        return None

    # Ambil info resep dari baris pertama (sama di semua baris)
    first = rows[0]
    info = {
        "namaMenu":  first.get("namaMenu", ""),
        "kategori":  first.get("kategori", ""),
        "steps":     first.get("steps", ""),
        "loves":     first.get("loves", "0"),
        "sourceURL": first.get("sourceURL", ""),
    }

    # Kumpulkan semua bahan unik (satu resep bisa punya banyak bahan)
    seen_ingredients = set()
    ingredients = []
    for row in rows:
        name = row.get("namaBahan")
        if name and name not in seen_ingredients:
            seen_ingredients.add(name)
            ingredients.append({
                "namaBahan": name,
                "kalori":    row.get("kalori", ""),
                "protein":   row.get("protein", ""),
                "lemak":     row.get("lemak", ""),
                "karbo":     row.get("karbo", ""),
                "imgBahan":  row.get("imgBahan", ""),
            })

    return {"info": info, "ingredients": ingredients}


# ═══════════════════════════════════════════════════════════════════════════════
# Q6 — Deteksi bahan berbahaya dalam sebuah resep
# ═══════════════════════════════════════════════════════════════════════════════
def get_dangerous_ingredients(recipe_uri: str) -> list[dict]:
    """
    Cari bahan dalam resep yang mengandung zat berbahaya untuk kondisi kesehatan tertentu.

    Reasoning SPARQL:
    - Triple chain: menu → hasIngredient → bahan → containsNutrient → gizi → isAvoidedBy → kondisi
    - Ini memanfaatkan ontologi SmartRecipe untuk mendeteksi:
      1. Bahan apa saja dalam resep (hasIngredient)
      2. Zat berbahaya apa yang dikandung bahan (containsNutrient)
      3. Kondisi kesehatan apa yang harus menghindari zat ini (isAvoidedBy)
    - Hasilnya: daftar bahan + nama zat berbahaya + nama kondisi

    Args:
        recipe_uri: URI lengkap resep

    Returns:
        list[dict]: Setiap dict berisi:
            - namaBahan: Nama bahan (misal "Udang")
            - namaGizi: Nama zat berbahaya (misal "Zat Purin Tinggi")
            - namaKondisi: Nama kondisi kesehatan (misal "Asam Urat")
    """
    query = SPARQL_PREFIXES + f"""
    SELECT ?namaBahan ?namaGizi ?namaKondisi WHERE {{
        BIND(<{recipe_uri}> AS ?menu)
        ?menu sr:hasIngredient ?bahan .
        ?bahan rdfs:label ?namaBahan ;
               sr:containsNutrient ?gizi .
        ?gizi rdfs:label ?namaGizi ;
              sr:isAvoidedBy ?kondisi .
        ?kondisi rdfs:label ?namaKondisi .
    }}
    """
    return parse_bindings(sparql_query(query))
