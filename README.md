# SmartRecipe: Sistem Pencarian Semantik Resep Makanan Indonesia Berbasis Kompatibilitas Bahan dan Kondisi Kesehatan Menggunakan RDF, Ontologi, dan SPARQL

SmartRecipe adalah sebuah sistem pencarian resep makanan (mesin pencari spesifik) yang dibangun dengan fondasi teknologi **Semantic Web**. Berbeda dengan mesin pencarian konvensional yang hanya mencocokkan kata kunci teks dasar, sistem ini dibangun di atas **Ontologi RDF** yang menyimpan relasi makna. 

Keunggulan utama sistem ini adalah kemampuannya untuk **merekomendasikan dan mengeksklusi resep masakan berdasarkan pantangan medis penggunanya** secara otomatis melalui penalaran *Knowledge Graph*.

## Kontributor (Disusun Oleh)
- **Luthfi Hamam Arsyada** (140810230007)
- **Hafizh Fadhl Muhammad** (140810230070)
- **Dzikri Bassyril Mu’minin** (140810230071)

---

## 1. Panduan Instalasi

Project ini terdiri atas dua lapisan aplikasi yang harus berjalan berdampingan: **Database Semantik (Apache Jena Fuseki)** dan **Aplikasi Web (Python Flask)**.

### Langkah 1: Persiapan Database Semantik (Fuseki)
1. Pastikan komputer Anda telah terinstal **Java JDK 11** atau versi yang lebih baru.
2. Unduh *Apache Jena Fuseki* dari situs resminya dan ekstrak ke folder di komputer Anda.
3. Buka *Terminal* atau *Command Prompt*, arahkan ke folder ekstraksi Fuseki, lalu jalankan perintah:
   ```bash
   fuseki-server.bat
   ```
4. Buka Browser dan kunjungi panel admin di `http://localhost:3030`.
5. Klik **Manage Datasets** -> **Add New Dataset**. Beri nama dataset dengan `smartrecipe` dan pilih tipe **Persistent (TDB2)**.
6. Masuk ke dataset `smartrecipe` yang baru dibuat, pilih tab **Upload Data**, kemudian unggah file ontologi `smartrecipe.ttl` yang ada di direktori utama folder proyek ini.

### Langkah 2: Menjalankan Aplikasi Web
1. Buka *Terminal* atau *Command Prompt* baru (biarkan terminal Fuseki tetap berjalan).
2. Masuk ke folder aplikasi web dengan perintah:
   ```bash
   cd smartrecipe-web
   ```
3. Instal semua modul Python yang dibutuhkan:
   ```bash
   pip install -r requirements.txt
   ```
4. Jalankan aplikasi web lokal:
   ```bash
   python app.py
   ```
5. Buka Browser dan kunjungi antarmuka web di **`http://localhost:5000`**.

---

## 2. Panduan Pengguna

1. **Pencarian Bebas (Teks):**
   Pada halaman utama, Anda dapat mengetikkan nama resep masakan secara spesifik di kolom pencarian (misal: "Rendang" atau "Soto").
2. **Filter Berdasarkan Kondisi Kesehatan:**
   Terdapat *dropdown* (menu tarik turun) yang memperbolehkan pengguna untuk memasukkan pantangan kesehatannya (contoh: *Asam Urat, Hipertensi, Kolesterol Tinggi, Alergi Kacang*). Saat filter diaktifkan, secara otomatis sistem (SPARQL) akan memblokir resep-resep yang mengandung bahan bahaya turunan dari penyakit tersebut.
3. **Filter Kategori Bahan Dasar:**
   Anda dapat mempersempit hasil masakan berdasarkan lauk utama kesukaan Anda (contoh: hanya menampilkan lauk *Ayam, Sapi, Ikan, Tempe, dll*).
4. **Halaman Detail dan Peringatan Gizi:**
   Ketika Anda mengeklik salah satu resep, halaman detail akan menampilkan langkah-langkah memasak dan daftar bahan. Jika masakan tersebut memiliki bahan berbahaya (misal Santan pada penderita Kolesterol), maka bahan tersebut akan diberi stabilo/sorotan peringatan merah secara visual. Terdapat juga tabel info nilai gizi makro (Kalori, Protein, Lemak, Karbohidrat).

---

## 3. Contoh Hasil (Cara Kerja Sistem)

**Skenario A: Pencarian Umum**
- **Input:** Pengguna mencari dengan kata kunci/kategori `Ayam`.
- **Hasil:** Sistem mengambil semua data *Instance* bertipe `sr:MenuMasakan` yang relevan dengan kata "ayam". Resep-resep populer seperti "Ayam Goreng Bawang Khas Batam", "Ayam Goreng Kecap", dan "Mie Ayam" akan muncul di layar berurutan dari yang memiliki jumlah *Loves* (Suka) tertinggi.

**Skenario B: Filter Semantik Kesehatan (Penalaran Ontologi)**
- **Input:** Pengguna mencari kata kunci `Ayam` DAN Kondisi Kesehatan `Asam Urat`.
- **Hasil:** Melalui *knowledge graph*, sistem SPARQL mendeteksi bahwa penyakit "Asam Urat" memiliki larangan memakan "Zat Purin Tinggi" (seperti udang, jeroan, dan bahan turunan lain). Akibatnya, sistem secara cerdas langsung menyembunyikan mayoritas resep ayam populer (seperti *Ayam Goreng Bawang Khas Batam* dan *Dimsum siomay udang ayam*) dari layar pengguna karena mengandung bahan terlarang. Hasilnya, hanya resep **"Ayam Woku Manado"** yang ditampilkan karena ontologi memverifikasi bahwa bahan-bahannya aman dari purin tinggi.

**Skenario C: Deteksi Bahan Berbahaya di Detail**
- Jika pengguna membuka halaman detail **"Ayam Goreng Bawang Khas Batam"** (atau resep lainnya) yang bumbunya menuntut tambahan bahan masakan seperti "Garam", "Penyedap", atau "Saus Tiram", sistem akan memberikan stabilo peringatan warna merah pada daftar bahan tersebut jika pengguna memiliki riwayat penyakit **Hipertensi**. Ini menunjukkan fungsi peringatan gizi makro secara personal.

---

