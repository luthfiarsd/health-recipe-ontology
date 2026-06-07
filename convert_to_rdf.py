"""
CSV → RDF Converter
Proyek Akhir Semantic Web - Sistem Pencarian Semantik Resep Makanan Indonesia
Kelompok: Luthfi (230007), Hafizh (230070), Dzikri (230071)

Dataset: 8 kategori resep (ayam, ikan, kambing, sapi, tahu, telur, tempe, udang)
         + nutrition.csv (data gizi 1345 bahan makanan)
"""

import pandas as pd
import re
import unicodedata
from rdflib import Graph, Literal, RDF, URIRef, Namespace, BNode
from rdflib.namespace import RDFS, OWL, XSD, DCTERMS

# ─────────────────────────────────────────────
# NAMESPACE
# ─────────────────────────────────────────────
SR   = Namespace("http://smartrecipe.org/ontology#")
DATA = Namespace("http://smartrecipe.org/data#")

g = Graph()
g.bind("sr",      SR)
g.bind("data",    DATA)
g.bind("rdfs",    RDFS)
g.bind("owl",     OWL)
g.bind("xsd",     XSD)
g.bind("dcterms", DCTERMS)

# ─────────────────────────────────────────────
# HELPER: URI-safe string
# ─────────────────────────────────────────────
def to_uri_safe(text: str) -> str:
    text = str(text).strip()
    # normalize unicode → ascii where possible
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s\-]+", "_", text)
    text = text.strip("_")
    return text[:80]  # max 80 char

# ─────────────────────────────────────────────
# ONTOLOGY SCHEMA
# ─────────────────────────────────────────────
def define_schema():
    # ── Classes ──
    for cls in [SR.MenuMasakan, SR.BahanBaku, SR.KandunganGizi, SR.KondisiKesehatan]:
        g.add((cls, RDF.type, OWL.Class))

    g.add((SR.MenuMasakan,      RDFS.label, Literal("Menu Masakan",       lang="id")))
    g.add((SR.BahanBaku,        RDFS.label, Literal("Bahan Baku",         lang="id")))
    g.add((SR.KandunganGizi,    RDFS.label, Literal("Kandungan Gizi",     lang="id")))
    g.add((SR.KondisiKesehatan, RDFS.label, Literal("Kondisi Kesehatan",  lang="id")))

    # ── Object Properties ──
    props_obj = [
        (SR.hasIngredient,    SR.MenuMasakan,   SR.BahanBaku,
         "Resep memiliki bahan baku"),
        (SR.containsNutrient, SR.BahanBaku,     SR.KandunganGizi,
         "Bahan mengandung zat gizi"),
        (SR.isAvoidedBy,      SR.KandunganGizi, SR.KondisiKesehatan,
         "Zat gizi dihindari oleh kondisi kesehatan tertentu"),
        (SR.hasCategory,      SR.MenuMasakan,   SR.BahanBaku,
         "Resep termasuk kategori bahan utama"),
    ]
    for prop, domain, range_, comment in props_obj:
        g.add((prop, RDF.type, OWL.ObjectProperty))
        g.add((prop, RDFS.domain, domain))
        g.add((prop, RDFS.range,  range_))
        g.add((prop, RDFS.comment, Literal(comment, lang="id")))

    # ── Data Properties ──
    props_data = [
        (SR.hasCalories,     SR.BahanBaku, XSD.float,  "Kalori (kcal)"),
        (SR.hasProtein,      SR.BahanBaku, XSD.float,  "Protein (gram)"),
        (SR.hasFat,          SR.BahanBaku, XSD.float,  "Lemak (gram)"),
        (SR.hasCarbohydrate, SR.BahanBaku, XSD.float,  "Karbohidrat (gram)"),
        (SR.hasImageURL,     SR.BahanBaku, XSD.anyURI, "URL gambar bahan"),
        (SR.hasSteps,        SR.MenuMasakan, XSD.string, "Langkah memasak"),
        (SR.hasSourceURL,    SR.MenuMasakan, XSD.anyURI, "URL sumber resep"),
        (SR.hasLoves,        SR.MenuMasakan, XSD.integer,"Jumlah likes resep"),
    ]
    for prop, domain, range_, comment in props_data:
        g.add((prop, RDF.type, OWL.DatatypeProperty))
        g.add((prop, RDFS.domain, domain))
        g.add((prop, RDFS.range,  range_))
        g.add((prop, RDFS.comment, Literal(comment, lang="id")))


# ─────────────────────────────────────────────
# KONDISI KESEHATAN & KANDUNGAN GIZI BERBAHAYA
# ─────────────────────────────────────────────
# Struktur: kondisi → {uri_gizi: (label_gizi, [keyword bahan])}
HEALTH_RULES = {
    "AsamUrat": {
        "label": "Asam Urat",
        "avoid_nutrients": {
            "PurinTinggi": {
                "label": "Zat Purin Tinggi",
                "keywords": [
                    "udang", "kepiting", "cumi", "kerang", "seafood",
                    "jeroan", "hati", "ampela", "limpa", "babat", "paru",
                    "emping", "melinjo", "sarden", "teri", "ikan teri",
                    "kacang polong", "bayam", "kangkung", "jamur",
                    "daging kambing", "kambing",
                ]
            }
        }
    },
    "Hipertensi": {
        "label": "Hipertensi",
        "avoid_nutrients": {
            "NatriumTinggi": {
                "label": "Natrium / Garam Tinggi",
                "keywords": [
                    "garam", "kecap asin", "saus tiram", "terasi",
                    "makanan kaleng", "kornet", "sarden kaleng",
                    "keju", "mentega", "abon", "ikan asin",
                    "petis", "tauco", "kaldu bubuk", "penyedap",
                ]
            }
        }
    },
    "KolesterolTinggi": {
        "label": "Kolesterol Tinggi",
        "avoid_nutrients": {
            "LemakJenuhTinggi": {
                "label": "Lemak Jenuh Tinggi",
                "keywords": [
                    "santan", "kelapa", "minyak kelapa",
                    "daging berlemak", "gajih", "lemak sapi",
                    "jeroan", "hati", "babat", "usus",
                    "kulit ayam", "kulit",
                    "mentega", "margarin", "krim",
                    "keju", "susu full cream",
                ]
            }
        }
    },
    "AlergiKacang": {
        "label": "Alergi Kacang",
        "avoid_nutrients": {
            "AlergenKacang": {
                "label": "Allergen Kacang",
                "keywords": [
                    "kacang tanah", "kacang", "selai kacang",
                    "bumbu kacang", "sambal kacang",
                    "kacang mede", "kacang almond", "kacang panjang",
                    "kacang merah", "kacang hijau", "kacang kedelai",
                    "tempe",  # turunan kedelai
                ]
            }
        }
    },
}

def add_health_conditions():
    for cond_key, cond_data in HEALTH_RULES.items():
        cond_uri = DATA[cond_key]
        g.add((cond_uri, RDF.type,   SR.KondisiKesehatan))
        g.add((cond_uri, RDFS.label, Literal(cond_data["label"], lang="id")))
        g.add((cond_uri, DCTERMS.identifier, Literal(cond_key)))

        for nut_key, nut_data in cond_data["avoid_nutrients"].items():
            nut_uri = DATA[nut_key]
            g.add((nut_uri, RDF.type,       SR.KandunganGizi))
            g.add((nut_uri, RDFS.label,     Literal(nut_data["label"], lang="id")))
            g.add((nut_uri, DCTERMS.identifier, Literal(nut_key)))
            g.add((nut_uri, SR.isAvoidedBy, cond_uri))


# ─────────────────────────────────────────────
# NUTRITION.CSV → BahanBaku dengan data gizi
# ─────────────────────────────────────────────
ingredient_nutrition_map = {}   # normalized_name → uri DATA

def add_nutrition_data():
    df = pd.read_csv("/mnt/user-data/uploads/nutrition.csv")
    for _, row in df.iterrows():
        name_raw = str(row["name"]).strip()
        safe     = to_uri_safe(name_raw)
        uri      = DATA[f"bahan_{safe}"]

        g.add((uri, RDF.type,              SR.BahanBaku))
        g.add((uri, RDFS.label,            Literal(name_raw, lang="id")))
        g.add((uri, DCTERMS.identifier,    Literal(f"NUT-{int(row['id']):04d}")))

        for col, prop in [
            ("calories",     SR.hasCalories),
            ("proteins",     SR.hasProtein),
            ("fat",          SR.hasFat),
            ("carbohydrate", SR.hasCarbohydrate),
        ]:
            val = row.get(col)
            if pd.notna(val):
                g.add((uri, prop, Literal(float(val), datatype=XSD.float)))

        img = row.get("image")
        if pd.notna(img) and str(img).startswith("http"):
            g.add((uri, SR.hasImageURL, Literal(str(img), datatype=XSD.anyURI)))

        # Simpan mapping (kunci: lowercase, bersih)
        norm = name_raw.lower().strip()
        ingredient_nutrition_map[norm] = uri

    print(f"  OK Nutrition: {len(ingredient_nutrition_map)} bahan berhasil dimuat")


# ─────────────────────────────────────────────
# CARI NUTRISI dari string bahan
# ─────────────────────────────────────────────
def find_nutrition_uri(ing_text: str):
    """Coba cocokkan teks bahan ke entri nutrition.csv (fuzzy keyword match)."""
    norm = ing_text.lower().strip()
    # 1. exact
    if norm in ingredient_nutrition_map:
        return ingredient_nutrition_map[norm]
    # 2. partial — cek apakah norm adalah substring dari key
    for key, uri in ingredient_nutrition_map.items():
        if norm and len(norm) >= 4 and norm in key:
            return uri
    # 3. partial — cek apakah key adalah substring dari norm
    for key, uri in ingredient_nutrition_map.items():
        if key and len(key) >= 5 and key in norm:
            return uri
    return None


def detect_risky_nutrients(ing_text: str) -> list:
    """Kembalikan list URI kandungan berbahaya yang cocok dengan bahan ini."""
    norm = ing_text.lower()
    risky = []
    for cond_key, cond_data in HEALTH_RULES.items():
        for nut_key, nut_data in cond_data["avoid_nutrients"].items():
            for kw in nut_data["keywords"]:
                if kw in norm:
                    risky.append(DATA[nut_key])
                    break
    return risky


# ─────────────────────────────────────────────
# PARSE INGREDIENTS STRING
# ─────────────────────────────────────────────
def parse_ingredients(raw: str) -> list:
    """Pisah string bahan (delimiter '--') & bersihkan tiap bahan."""
    parts = str(raw).split("--")
    cleaned = []
    for p in parts:
        p = p.strip()
        if not p or len(p) < 3:
            continue
        # Buang angka & satuan di awal (e.g. "2 sdm", "1/2 sdt", "3 butir")
        p = re.sub(
            r"^\s*[\d/]+\s*(sdm|sdt|gram|gr|g|kg|ml|l|siung|lembar|buah|bh|"
            r"butir|batang|ruas|ikat|ekor|lbr|sachet|bungkus|helai|"
            r"keping|lonjor|genggam|sendok teh|sendok makan)\s*",
            "", p, flags=re.IGNORECASE
        )
        # Buang keterangan dalam kurung
        p = re.sub(r"\(.*?\)", "", p).strip()
        # Skip label section seperti "Bumbu halus:", "Bahan:"
        if p.endswith(":") or len(p) < 3:
            continue
        # Skip "secukupnya", "sesuai selera", dll (tanpa nama bahan jelas)
        if re.match(r"^(secukupnya|sesuai selera|optional|opsional|pelengkap)$",
                    p, re.IGNORECASE):
            continue
        cleaned.append(p.strip(" .,"))
    return cleaned


# ─────────────────────────────────────────────
# RECIPES CSV → MenuMasakan + BahanBaku
# ─────────────────────────────────────────────
RECIPE_FILES = {
    "ayam":   "/mnt/user-data/uploads/dataset-ayam.csv",
    "ikan":   "/mnt/user-data/uploads/dataset-ikan.csv",
    "kambing":"/mnt/user-data/uploads/dataset-kambing.csv",
    "sapi":   "/mnt/user-data/uploads/dataset-sapi.csv",
    "tahu":   "/mnt/user-data/uploads/dataset-tahu.csv",
    "telur":  "/mnt/user-data/uploads/dataset-telur.csv",
    "tempe":  "/mnt/user-data/uploads/dataset-tempe.csv",
    "udang":  "/mnt/user-data/uploads/dataset-udang.csv",
}

# Berapa resep per kategori yang diambil
RECIPES_PER_CATEGORY = 5   # ambil 5 × 8 = 40 resep (melewati target 20-30)

def add_recipes():
    total_recipes   = 0
    total_ing_linked = 0   # bahan yang berhasil dihubungkan ke nutrition
    seen_titles = set()    # deduplikasi lintas kategori

    for category, filepath in RECIPE_FILES.items():
        df = pd.read_csv(filepath)
        # Ambil resep dengan jumlah Loves tertinggi agar representatif
        df = df.sort_values("Loves", ascending=False).head(RECIPES_PER_CATEGORY)

        cat_count = 0
        for idx, row in df.iterrows():
            title = str(row["Title"]).strip()
            if title in seen_titles:
                continue
            seen_titles.add(title)

            # ── URI Resep ──
            safe_title = to_uri_safe(title)
            recipe_id  = f"REC_{category.upper()}_{cat_count+1:03d}"
            recipe_uri = DATA[f"resep_{safe_title}"]

            g.add((recipe_uri, RDF.type,             SR.MenuMasakan))
            g.add((recipe_uri, RDFS.label,            Literal(title, lang="id")))
            g.add((recipe_uri, DCTERMS.identifier,    Literal(recipe_id)))
            g.add((recipe_uri, DCTERMS.subject,       Literal(category, lang="id")))

            loves = row.get("Loves", 0)
            if pd.notna(loves):
                g.add((recipe_uri, SR.hasLoves, Literal(int(loves), datatype=XSD.integer)))

            url = str(row.get("URL", "")).strip()
            if url.startswith("/") or url.startswith("http"):
                full_url = url if url.startswith("http") else f"https://cookpad.com{url}"
                g.add((recipe_uri, SR.hasSourceURL, Literal(full_url, datatype=XSD.anyURI)))

            steps = str(row.get("Steps", "")).strip()
            if steps:
                g.add((recipe_uri, SR.hasSteps, Literal(steps)))

            # ── Kategori bahan utama ──
            category_uri = DATA[f"kategori_{category}"]
            g.add((category_uri, RDF.type,   SR.BahanBaku))
            g.add((category_uri, RDFS.label, Literal(category.capitalize(), lang="id")))
            g.add((recipe_uri, SR.hasCategory, category_uri))

            # ── Parse & tambahkan bahan-bahan ──
            raw_ingredients = str(row.get("Ingredients", ""))
            ingredients     = parse_ingredients(raw_ingredients)

            for ing_text in ingredients:
                safe_ing = to_uri_safe(ing_text)
                if not safe_ing:
                    continue

                ing_uri = DATA[f"bahan_{safe_ing}"]

                # Cek apakah sudah ada dari nutrition.csv
                nutrition_uri = find_nutrition_uri(ing_text)

                if nutrition_uri:
                    # Gunakan URI dari nutrition.csv (sudah ada data gizi)
                    g.add((recipe_uri, SR.hasIngredient, nutrition_uri))
                    total_ing_linked += 1
                    # Tambahkan label mentah juga jika belum ada
                    # (label utama sudah dari nutrition)
                    act_ing_uri = nutrition_uri
                else:
                    # Buat entitas BahanBaku baru (belum ada di nutrition)
                    g.add((ing_uri, RDF.type,           SR.BahanBaku))
                    g.add((ing_uri, RDFS.label,         Literal(ing_text, lang="id")))
                    g.add((recipe_uri, SR.hasIngredient, ing_uri))
                    act_ing_uri = ing_uri

                # ── Relasi ke KandunganGizi berbahaya ──
                risky_nutrients = detect_risky_nutrients(ing_text)
                for nut_uri in risky_nutrients:
                    g.add((act_ing_uri, SR.containsNutrient, nut_uri))

            cat_count  += 1
            total_recipes += 1

        print(f"  OK {category:10s}: {cat_count} resep ditambahkan")

    print(f"\n  Total resep       : {total_recipes}")
    print(f"  Bahan ter-link gizi: {total_ing_linked}")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
if __name__ == "__main__":
    print("Mendefinisikan skema ontologi...")
    define_schema()

    print("Menambahkan kondisi kesehatan & kandungan berbahaya...")
    add_health_conditions()

    print("Memuat data nutrisi (nutrition.csv)...")
    add_nutrition_data()

    print("Mengkonversi resep dari semua CSV...")
    add_recipes()

    output_path = "/home/claude/smartrecipe.ttl"
    print(f"\nMenyimpan RDF ke {output_path} ...")
    g.serialize(destination=output_path, format="turtle")

    # Statistik akhir
    total_triples = len(g)
    recipes  = len(list(g.subjects(RDF.type, SR.MenuMasakan)))
    bahanb   = len(list(g.subjects(RDF.type, SR.BahanBaku)))
    kandungan= len(list(g.subjects(RDF.type, SR.KandunganGizi)))
    kondisi  = len(list(g.subjects(RDF.type, SR.KondisiKesehatan)))

    print("\n" + "="*50)
    print("KONVERSI SELESAI")
    print("="*50)
    print(f"  Total Triple RDF     : {total_triples:,}")
    print(f"  MenuMasakan          : {recipes}")
    print(f"  BahanBaku            : {bahanb:,}")
    print(f"  KandunganGizi        : {kandungan}")
    print(f"  KondisiKesehatan     : {kondisi}")
    print(f"  Output               : {output_path}")
    print("="*50)
