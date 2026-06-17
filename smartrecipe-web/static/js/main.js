/**
 * main.js — SmartRecipe Frontend Handler
 * ========================================
 * Menghandle AJAX search & filter tanpa reload halaman.
 * Debounce diterapkan pada search input untuk mengurangi request berlebih.
 */

// ─── Debounce Utility ───────────────────────────────────────────────────────
function debounce(func, delay = 400) {
    let timer;
    return function (...args) {
        clearTimeout(timer);
        timer = setTimeout(() => func.apply(this, args), delay);
    };
}

// ─── Init Search Handler ────────────────────────────────────────────────────
function initSearch(categoryEmoji) {
    const searchInput    = document.getElementById('search-input');
    const filterCondition = document.getElementById('filter-condition');
    const filterCategory = document.getElementById('filter-category');
    const btnSearch      = document.getElementById('btn-search');
    const recipeGrid     = document.getElementById('recipe-grid');
    const resultsCount   = document.getElementById('results-count');
    const emptyState     = document.getElementById('empty-state');
    const loadingSpinner = document.getElementById('loading-spinner');
    const askInput       = document.getElementById('ask-input');
    const btnAsk         = document.getElementById('btn-ask');
    const askResponse    = document.getElementById('ask-response');

    if (!searchInput || !recipeGrid) return;

    // ─── Fetch & Render ─────────────────────────────────────────────────────
    async function fetchRecipes() {
        const keyword   = searchInput.value.trim();
        const condition = filterCondition.value;
        const category  = filterCategory.value;

        // Build query params
        const params = new URLSearchParams();
        if (keyword)   params.set('keyword', keyword);
        if (condition) params.set('condition', condition);
        if (category)  params.set('category', category);

        // Show loading
        loadingSpinner.classList.remove('hidden');

        try {
            const response = await fetch(`/api/recipes?${params.toString()}`);
            const json = await response.json();

            if (json.success) {
                renderRecipes(json.data, categoryEmoji);
            } else {
                showError(json.error || 'Terjadi kesalahan');
            }
        } catch (err) {
            showError('Gagal terhubung ke server. Pastikan Flask dan Fuseki berjalan.');
            console.error('Fetch error:', err);
        } finally {
            loadingSpinner.classList.add('hidden');
        }
    }

    // ─── Render Recipe Cards ────────────────────────────────────────────────
    function renderRecipes(recipes, categoryLabels) {
        recipeGrid.innerHTML = '';

        // Update count badge
        resultsCount.textContent = `${recipes.length} resep`;

        if (recipes.length === 0) {
            emptyState.classList.remove('hidden');
            return;
        }

        emptyState.classList.add('hidden');

        recipes.forEach((recipe, index) => {
            const categoryLabel = categoryLabels[recipe.kategori] || recipe.kategori || 'resep';
            const encodedUri = recipe.encoded_uri || encodeURIComponent(recipe.menu);
            const media = recipe.imgMenu
                ? `
                <img src="${escapeHtml(recipe.imgMenu)}" alt="${escapeHtml(recipe.namaMenu)}" loading="lazy" class="absolute inset-0 w-full h-full object-cover transition-transform duration-500 group-hover:scale-105">
                <div class="absolute inset-0 bg-gradient-to-t from-dark-950 via-dark-900/30 to-transparent"></div>
                `
                : `
                <div class="absolute inset-0 bg-gradient-to-t from-dark-900/80 to-transparent"></div>
                <span class="text-lg font-semibold uppercase tracking-widest text-primary-200 relative z-10 group-hover:scale-110 transition-transform duration-300">${escapeHtml(categoryLabel)}</span>
                `;
            
            const card = document.createElement('a');
            card.href = `/resep/${encodedUri}`;
            card.className = 'recipe-card glass-card rounded-xl overflow-hidden group hover:border-primary-500/30 transition-all duration-300';
            card.id = `recipe-card-${index + 1}`;
            card.style.animationDelay = `${index * 0.02}s`;

            card.innerHTML = `
                <div class="h-32 bg-gradient-to-br from-primary-500/20 via-primary-600/10 to-dark-800 flex items-center justify-center relative overflow-hidden">
                    ${media}
                </div>
                <div class="p-4">
                    <h3 class="font-semibold text-white text-sm mb-2 line-clamp-2 group-hover:text-primary-300 transition-colors">
                        ${escapeHtml(recipe.namaMenu)}
                    </h3>
                    <div class="flex items-center justify-between">
                        <span class="inline-flex items-center gap-1 px-2.5 py-1 rounded-lg bg-dark-700/60 text-xs text-gray-400 border border-white/5">
                            <svg class="w-3 h-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"/>
                            </svg>
                            ${capitalize(recipe.kategori)}
                        </span>
                        <span class="flex items-center gap-1 text-xs text-red-400/80">
                            <svg class="w-3.5 h-3.5" fill="currentColor" viewBox="0 0 24 24">
                                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
                            </svg>
                            ${recipe.loves}
                        </span>
                    </div>
                </div>
            `;

            recipeGrid.appendChild(card);
        });
    }

    // ─── Ask SmartRecipe via LLM ───────────────────────────────────────────
    async function askSmartRecipe() {
        if (!askInput || !btnAsk) return;

        const question = askInput.value.trim();
        if (!question) {
            renderAskResponse({
                summary: 'Tulis pertanyaan terlebih dahulu.',
                notes: [],
                filters: null,
                isError: true,
            });
            return;
        }

        loadingSpinner.classList.remove('hidden');
        btnAsk.disabled = true;
        btnAsk.textContent = 'Memproses...';

        try {
            const response = await fetch('/api/ask', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ question }),
            });
            const json = await response.json();

            if (!json.success) {
                throw new Error(json.error || 'Gagal memproses pertanyaan.');
            }

            const filters = json.filters || {};
            searchInput.value = filters.keyword || '';
            filterCondition.value = filters.condition || '';
            filterCategory.value = filters.category || '';

            renderAskResponse({
                summary: json.narrative?.summary || 'Hasil ditemukan berdasarkan data ontology.',
                notes: json.narrative?.notes || [],
                filters,
                isError: false,
            });
            renderRecipes(json.data || [], categoryEmoji);
        } catch (err) {
            renderAskResponse({
                summary: err.message || 'Gagal menghubungi layanan LLM.',
                notes: [],
                filters: null,
                isError: true,
            });
            console.error('Ask error:', err);
        } finally {
            btnAsk.disabled = false;
            btnAsk.textContent = 'Tanya';
            loadingSpinner.classList.add('hidden');
        }
    }

    function renderAskResponse({ summary, notes, filters, isError }) {
        if (!askResponse) return;

        const filterBadges = filters ? [
            filters.keyword ? `Kata kunci: ${filters.keyword}` : '',
            filters.condition ? `Kondisi: ${filters.condition.replace('_', ' ')}` : '',
            filters.category ? `Kategori: ${filters.category}` : '',
        ].filter(Boolean) : [];

        askResponse.classList.remove('hidden');
        askResponse.innerHTML = `
            <div class="flex items-start gap-3">
                <div class="w-9 h-9 rounded-lg ${isError ? 'bg-red-500/10 border-red-500/20' : 'bg-emerald-500/10 border-emerald-500/20'} border flex items-center justify-center flex-shrink-0">
                    <svg class="w-5 h-5 ${isError ? 'text-red-300' : 'text-emerald-300'}" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="${isError ? 'M12 9v2m0 4h.01M12 3a9 9 0 110 18 9 9 0 010-18z' : 'M9.75 17L9 20l2.25-1.5L13.5 20l-.75-3M7 10a5 5 0 1110 0c0 2.5-2.5 4-5 4s-5-1.5-5-4z'}"/>
                    </svg>
                </div>
                <div class="min-w-0">
                    <p class="text-sm ${isError ? 'text-red-200' : 'text-gray-200'} leading-6">${escapeHtml(summary)}</p>
                    ${filterBadges.length ? `
                        <div class="flex flex-wrap gap-2 mt-3">
                            ${filterBadges.map((badge) => `
                                <span class="px-2.5 py-1 rounded-lg bg-dark-800/80 border border-white/5 text-xs text-gray-400">${escapeHtml(badge)}</span>
                            `).join('')}
                        </div>
                    ` : ''}
                    ${notes.length ? `
                        <ul class="mt-3 space-y-1">
                            ${notes.map((note) => `<li class="text-xs text-gray-500">${escapeHtml(note)}</li>`).join('')}
                        </ul>
                    ` : ''}
                </div>
            </div>
        `;
    }

    // ─── Show Error ─────────────────────────────────────────────────────────
    function showError(message) {
        recipeGrid.innerHTML = `
            <div class="col-span-full text-center py-12">
                <div class="w-16 h-16 mx-auto mb-3 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
                    <svg class="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.964-.833-2.732 0L4.082 16.5c-.77.833.192 2.5 1.732 2.5z"/>
                    </svg>
                </div>
                <p class="text-sm text-red-300">${escapeHtml(message)}</p>
            </div>
        `;
        emptyState.classList.add('hidden');
        resultsCount.textContent = '0 resep';
    }

    // ─── Event Listeners ────────────────────────────────────────────────────

    // Debounced search on typing
    const debouncedFetch = debounce(fetchRecipes, 500);
    searchInput.addEventListener('input', debouncedFetch);

    // Immediate filter on dropdown change
    filterCondition.addEventListener('change', fetchRecipes);
    filterCategory.addEventListener('change', fetchRecipes);

    // Search button click
    btnSearch.addEventListener('click', fetchRecipes);
    if (btnAsk) {
        btnAsk.addEventListener('click', askSmartRecipe);
    }

    // Enter key on search input
    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            e.preventDefault();
            fetchRecipes();
        }
    });

    if (askInput) {
        askInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                e.preventDefault();
                askSmartRecipe();
            }
        });
    }
}

// ─── Utility Functions ──────────────────────────────────────────────────────

function escapeHtml(str) {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
}

function capitalize(str) {
    if (!str) return '';
    return str.charAt(0).toUpperCase() + str.slice(1);
}
