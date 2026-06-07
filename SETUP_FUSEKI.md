# Panduan Setup Apache Jena Fuseki (Windows)

> **Apache Jena Fuseki** adalah SPARQL server (triplestore) yang digunakan untuk menyimpan dan melakukan query terhadap data RDF.

---

## Prasyarat

- **Java JDK 11+** sudah terinstall
  - Cek: buka Command Prompt → ketik `java -version`
  - Jika belum ada, download dari: https://adoptium.net/
  - Pastikan `JAVA_HOME` environment variable sudah di-set

---

## Langkah 1 — Download Apache Jena Fuseki

1. Buka halaman download resmi:  
   https://jena.apache.org/download/

2. Di bagian **Apache Jena Fuseki**, download file:  
   `apache-jena-fuseki-X.X.X.zip` (versi terbaru)

3. Ekstrak file ZIP ke lokasi yang mudah diakses, misalnya:  
   ```
   C:\Tools\apache-jena-fuseki-5.x.x\
   ```

---

## Langkah 2 — Jalankan Fuseki Server

1. Buka **Command Prompt** (atau PowerShell)

2. Masuk ke direktori Fuseki:
   ```cmd
   cd C:\Tools\apache-jena-fuseki-5.x.x
   ```

3. Jalankan server:
   ```cmd
   fuseki-server.bat
   ```

4. Jika berhasil, akan muncul log seperti:
   ```
   [2026:05:29 19:00:00] Apache Jena Fuseki 5.x.x
   [2026:05:29 19:00:00] Started on port 3030
   ```

5. Buka browser → akses:  
   **http://localhost:3030**

   Kamu akan melihat halaman admin Fuseki.

---

## Langkah 3 — Buat Dataset `smartrecipe`

### Opsi A — Via Web UI (Recommended)

1. Buka **http://localhost:3030** di browser
2. Klik tab **"manage datasets"** di bagian atas
3. Klik **"add new dataset"**
4. Isi form:
   - **Dataset name**: `smartrecipe`
   - **Dataset type**: pilih **Persistent (TDB2)** agar data tidak hilang saat restart
5. Klik **"create dataset"**

### Opsi B — Via Command Line

Jalankan Fuseki langsung dengan dataset:
```cmd
fuseki-server.bat --tdb2 --loc=.\databases\smartrecipe /smartrecipe
```

> Ini akan membuat folder `databases/smartrecipe` untuk menyimpan data secara persisten.

---

## Langkah 4 — Upload File RDF (`smartrecipe.ttl`)

### Opsi A — Via Web UI (Recommended)

1. Buka **http://localhost:3030**
2. Pilih dataset **"smartrecipe"** dari daftar
3. Klik **"upload data"**
4. Klik **"select files..."** → pilih file `smartrecipe.ttl` dari folder proyek:
   ```
   d:\KULIAH\SEMESTER 6\Semantic Web\health-recipe-ontology\smartrecipe.ttl
   ```
5. Klik **"upload all"**
6. Tunggu proses selesai — akan menampilkan jumlah triple yang berhasil di-upload (sekitar **12.284 triples**)

### Opsi B — Via curl (Command Line)

```cmd
curl -X POST "http://localhost:3030/smartrecipe/data" ^
  -H "Content-Type: text/turtle" ^
  --data-binary @"d:\KULIAH\SEMESTER 6\Semantic Web\health-recipe-ontology\smartrecipe.ttl"
```

### Opsi C — Via Python Script

```python
import requests

with open(r"d:\KULIAH\SEMESTER 6\Semantic Web\health-recipe-ontology\smartrecipe.ttl", "r", encoding="utf-8") as f:
    ttl_data = f.read()

response = requests.post(
    "http://localhost:3030/smartrecipe/data",
    headers={"Content-Type": "text/turtle; charset=utf-8"},
    data=ttl_data.encode("utf-8")
)

print(f"Status: {response.status_code}")
print(f"Response: {response.text}")
```

---

## Langkah 5 — Verifikasi Data

### Via Web UI

1. Buka **http://localhost:3030**
2. Pilih dataset **"smartrecipe"**
3. Klik **"query"**
4. Masukkan query berikut lalu klik **"Run Query"**:

```sparql
PREFIX sr: <http://smartrecipe.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT (COUNT(?menu) AS ?total) WHERE {
    ?menu a sr:MenuMasakan .
}
```

**Expected result**: `total = 40` (40 resep)

5. Coba query lain untuk memastikan relasi bahan → gizi → kondisi:

```sparql
PREFIX sr:   <http://smartrecipe.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?namaBahan ?namaGizi ?namaKondisi WHERE {
    ?bahan a sr:BahanBaku ;
           rdfs:label ?namaBahan ;
           sr:containsNutrient ?gizi .
    ?gizi rdfs:label ?namaGizi ;
          sr:isAvoidedBy ?kondisi .
    ?kondisi rdfs:label ?namaKondisi .
}
LIMIT 10
```

---

## Langkah 6 — Jalankan Aplikasi Flask

1. Pastikan Fuseki server **masih berjalan** di `http://localhost:3030`

2. Buka terminal baru, masuk ke folder aplikasi:
   ```cmd
   cd "d:\KULIAH\SEMESTER 6\Semantic Web\health-recipe-ontology\smartrecipe-web"
   ```

3. Install dependencies:
   ```cmd
   pip install -r requirements.txt
   ```

4. Jalankan Flask:
   ```cmd
   python app.py
   ```

5. Buka browser → akses:  
   **http://localhost:5000**

---

## Troubleshooting

### "Java not found" saat menjalankan Fuseki
- Install Java JDK 11+ dari https://adoptium.net/
- Set environment variable `JAVA_HOME` ke folder JDK
- Tambahkan `%JAVA_HOME%\bin` ke `PATH`

### Port 3030 sudah dipakai
- Jalankan Fuseki di port lain:
  ```cmd
  fuseki-server.bat --port=3040
  ```
- Ubah juga `FUSEKI_ENDPOINT` di `sparql_queries.py`

### Upload TTL gagal / timeout
- Pastikan file `smartrecipe.ttl` tidak corrupt
- Coba upload via Web UI (lebih reliable untuk file besar)

### Flask error "Connection refused"
- Pastikan Fuseki server sudah berjalan sebelum Flask
- Cek apakah URL endpoint di `sparql_queries.py` sudah benar

---

## Info Endpoint

| Item | Nilai |
|---|---|
| Fuseki Admin UI | `http://localhost:3030` |
| Dataset name | `smartrecipe` |
| SPARQL Query endpoint | `http://localhost:3030/smartrecipe/query` |
| SPARQL Update endpoint | `http://localhost:3030/smartrecipe/update` |
| Data upload endpoint | `http://localhost:3030/smartrecipe/data` |
