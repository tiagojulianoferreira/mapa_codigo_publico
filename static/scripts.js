document.addEventListener('DOMContentLoaded', () => {

    // === Elementos do DOM (Caché) ===
    const generalSearchInput = document.getElementById('generalSearchInput');
    const languageFilter = document.getElementById('languageFilter');
    const licenseFilter = document.getElementById('licenseFilter');
    const clearFiltersBtn = document.getElementById('clearFilters');
    
    // Estatísticas Globais
    const totalReposGlobal = document.getElementById('totalReposGlobal');
    const mostUsedLanguageGlobal = document.getElementById('mostUsedLanguageGlobal');
    const mostUsedLicenseGlobal = document.getElementById('mostUsedLicenseGlobal');
    const naLicenseCountSpan = document.getElementById('naLicenseCount');

    // Estatísticas Filtradas
    const totalFilteredRepos = document.getElementById('totalFilteredRepos');
    const mostUsedFilteredLanguage = document.getElementById('mostUsedFilteredLanguage');
    const mostUsedFilteredLicense = document.getElementById('mostUsedFilteredLicense');

    // Listas Top
    const topLanguagesTbody = document.getElementById('topLanguagesTbody');
    const topReposTbody = document.getElementById('topReposTbody');
    const topLicensesTbody = document.getElementById('topLicensesTbody');
    const clustersTbody = document.getElementById('clustersTbody');

    // Tabela Principal
    const allReposTbody = document.getElementById('allReposTbody');
    const allReposTableHeaders = document.querySelectorAll('#allReposTable thead th[data-sort-key]');
    const filteredReposCount = document.getElementById('filteredReposCount');

    // Paginação
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');

    // Tabela Cluster 3 de Destaque
    const cluster3Tbody = document.getElementById('cluster-3-tbody');


    // === Variáveis de Estado ===
    let allRepos = [];
    let currentFilteredAndSortedRepos = [];
    let currentSortColumn = 'Estrelas';
    let currentSortDirection = 'desc';
    let currentPage = 1;
    const itemsPerPage = 20;
    let clusters = [];
    let clusterDescriptions = {};


    // === Funções Utilitárias ===

    function countOccurrences(data, key) {
        const counts = {};
        data.forEach(item => {
            const value = item[key];
            if (value) {
                counts[value] = (counts[value] || 0) + 1;
            }
        });
        return counts;
    }

    function getMostCommon(counts) {
        const keys = Object.keys(counts);
        if (keys.length === 0) return null;
        return keys.reduce((a, b) => (counts[a] > counts[b] ? a : b));
    }


    // === Funções de Processamento e Renderização de Dados ===

    async function fetchAndProcessData() {
        try {
            const [responseMain, responseHighlighted] = await Promise.all([
                fetch('./repositorios_federais_filtrado_idioma.json'),
                fetch('./dados/repositorios_destaque_cluster_3.json')
            ]);
            const dataMain = await responseMain.json();
            const dataHighlighted = await responseHighlighted.json();

            if (dataMain && dataMain.institutions_data) {
                allRepos = [];
                dataMain.institutions_data.forEach(institution => {
                    institution.Repositorios.forEach(repo => {
                        repo.Instituicao = institution['Sigla'];
                        repo.InstituicaoNomeCompleto = institution['Nome Completo'];
                        repo.Tipo = repo['Tipo de Entidade'];
                        allRepos.push(repo);
                    });
                });
                
                if (dataMain.cluster_descriptions) {
                    clusters = dataMain.cluster_descriptions;
                    clusterDescriptions = clusters.reduce((acc, curr) => {
                        acc[curr.id] = curr.description;
                        return acc;
                    }, {});
                }

                populateFilters();
                updateGlobalStats();
                updateTopLists();
                updateTopLicenses();
                applyFiltersAndDisplay(true);
            }

            if (dataHighlighted && dataHighlighted.repositorios) {
                renderHighlightedClusterRepos(dataHighlighted.repositorios);
            }
            
            console.log(`Dados carregados: ${allRepos.length} repositórios encontrados.`);
        } catch (error) {
            console.error('Erro ao buscar ou processar os dados:', error);
        }
    }

    function populateFilters() {
        const languages = [...new Set(allRepos.map(repo => repo['Linguagem Principal']))].filter(Boolean).sort();
        if (languageFilter) {
            languageFilter.innerHTML = `<option value="">Todas</option>${languages.map(lang => `<option value="${lang}">${lang}</option>`).join('')}`;
        }

        const licenses = [...new Set(allRepos.map(repo => repo['Licenca']))].filter(Boolean).sort();
        if (licenseFilter) {
            licenseFilter.innerHTML = `<option value="">Todas</option>${licenses.map(lic => `<option value="${lic}">${lic}</option>`).join('')}`;
        }
    }

    function updateGlobalStats() {
        if (totalReposGlobal) totalReposGlobal.textContent = allRepos.length;

        const languageCounts = countOccurrences(allRepos, 'Linguagem Principal');
        if (mostUsedLanguageGlobal) mostUsedLanguageGlobal.textContent = getMostCommon(languageCounts) || 'N/A';

        const licenseCounts = countOccurrences(allRepos, 'Licenca');
        const naCount = allRepos.filter(repo => !repo.Licenca || repo.Licenca.toUpperCase() === 'N/A').length;
        const filteredLicenseCounts = Object.fromEntries(Object.entries(licenseCounts).filter(([key]) => key.toUpperCase() !== 'N/A'));
        if (mostUsedLicenseGlobal) mostUsedLicenseGlobal.textContent = getMostCommon(filteredLicenseCounts) || 'N/A';
        if (naLicenseCountSpan) naLicenseCountSpan.textContent = `(${naCount} sem licença)`;

        if (clustersTbody && clusters.length > 0) {
            clustersTbody.innerHTML = clusters.map(cluster => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${cluster.id}</td>
                    <td class="px-6 py-4 text-sm text-gray-700">${cluster.description}</td>
                </tr>
            `).join('');
        }
    }

    function updateFilteredStats(filteredRepos) {
        if (totalFilteredRepos) totalFilteredRepos.textContent = filteredRepos.length;

        const languageCounts = countOccurrences(filteredRepos, 'Linguagem Principal');
        if (mostUsedFilteredLanguage) mostUsedFilteredLanguage.textContent = getMostCommon(languageCounts) || 'N/A';

        const licenseCounts = countOccurrences(filteredRepos, 'Licenca');
        if (mostUsedFilteredLicense) mostUsedFilteredLicense.textContent = getMostCommon(licenseCounts) || 'N/A';
    }

    function updateTopLists() {
        const topRepos = [...allRepos].sort((a, b) => b.Estrelas - a.Estrelas).slice(0, 10);
        if (topReposTbody) {
            topReposTbody.innerHTML = topRepos.map(repo => `
                <tr>
                    <td class="py-2 px-4"><a href="${repo.Link}" target="_blank" class="text-blue-500 hover:underline">${repo['Nome do Repositório']}</a></td>
                    <td class="py-2 px-4">${repo.Instituicao}</td>
                    <td class="py-2 px-4">${repo.Estrelas}</td>
                </tr>
            `).join('');
        }

        const languageCounts = countOccurrences(allRepos, 'Linguagem Principal');
        const sortedLanguages = Object.entries(languageCounts).sort(([, a], [, b]) => b - a).slice(0, 10);
        if (topLanguagesTbody) {
            topLanguagesTbody.innerHTML = sortedLanguages.map(([lang, count]) => `
                <tr>
                    <td class="py-2 px-4">${lang}</td>
                    <td class="py-2 px-4">${count}</td>
                </tr>
            `).join('');
        }
    }

    function updateTopLicenses() {
        const licenseCounts = countOccurrences(allRepos.filter(repo => repo.Licenca && repo.Licenca.toUpperCase() !== 'N/A'), 'Licenca');
        const sortedLicenses = Object.entries(licenseCounts).sort(([, a], [, b]) => b - a).slice(0, 10);
        if (topLicensesTbody) {
            topLicensesTbody.innerHTML = sortedLicenses.map(([license, count]) => `
                <tr>
                    <td class="py-2 px-4">${license}</td>
                    <td class="py-2 px-4">${count}</td>
                </tr>
            `).join('');
        }
    }

    function applyFiltersAndDisplay(resetPagination = false) {
        const generalSearchQuery = generalSearchInput.value.toLowerCase();
        const selectedLanguage = languageFilter.value;
        const selectedLicense = licenseFilter.value;

        let filteredRepos = allRepos.filter(repo => {
            const matchesSearch = (repo['Nome do Repositório'] || '').toLowerCase().includes(generalSearchQuery) ||
                                 (repo.Descricao || '').toLowerCase().includes(generalSearchQuery) ||
                                 (repo.Instituicao || '').toLowerCase().includes(generalSearchQuery);
            const matchesLanguage = !selectedLanguage || repo['Linguagem Principal'] === selectedLanguage;
            const matchesLicense = !selectedLicense || repo.Licenca === selectedLicense;
            return matchesSearch && matchesLanguage && matchesLicense;
        });

        filteredRepos.sort((a, b) => {
            const valA = ['Estrelas', 'Forks', 'Contribuidores'].includes(currentSortColumn) ? (a[currentSortColumn] || 0) : (a[currentSortColumn] || '').toLowerCase();
            const valB = ['Estrelas', 'Forks', 'Contribuidores'].includes(currentSortColumn) ? (b[currentSortColumn] || 0) : (b[currentSortColumn] || '').toLowerCase();
            if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        currentFilteredAndSortedRepos = filteredRepos;
        if(filteredReposCount) filteredReposCount.textContent = currentFilteredAndSortedRepos.length;

        // Atualizar estatísticas filtradas
        updateFilteredStats(filteredRepos);

        if (resetPagination) currentPage = 1;
        renderTablePage();
    }

    function renderTablePage() {
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const reposToDisplay = currentFilteredAndSortedRepos.slice(startIndex, endIndex);

        if (allReposTbody) {
            allReposTbody.innerHTML = reposToDisplay.map(repo => `
                <tr class="hover:bg-gray-100 transition-colors duration-150">
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Instituicao}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo['Nome do Repositório']}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo['Linguagem Principal'] || 'N/A'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Estrelas}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Licenca || 'N/A'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo['Ultima Atualizacao']}</td>
                    <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">${repo.Descricao}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Cluster_ID}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <a href="${repo.Link}" target="_blank" class="text-blue-500 hover:underline">Link</a>
                    </td>
                </tr>
            `).join('');
        }

        const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
        if(pageInfoSpan) {
            pageInfoSpan.textContent = `Página ${currentPage} de ${totalPages}`;
            if (prevPageBtn) prevPageBtn.disabled = currentPage === 1;
            if (nextPageBtn) nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
        }
    }

    function renderHighlightedClusterRepos(repositorios) {
        if (cluster3Tbody) {
            cluster3Tbody.innerHTML = repositorios.map(repo => `
                <tr class="hover:bg-gray-100 transition-colors duration-150">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        <a href="${repo.link}" target="_blank" class="text-blue-500 hover:underline">${repo['Nome do Repositório']}</a>
                    </td>
                    <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate">${repo.descricao}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.estrelas}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.linguagem || 'N/A'}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.tipo}</td>
                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <a href="${repo.link}" target="_blank" class="text-blue-500 hover:underline">Link</a>
                    </td>
                </tr>
            `).join('');
        }
    }


    // === Listeners de Eventos ===

    if (generalSearchInput) generalSearchInput.addEventListener('input', () => applyFiltersAndDisplay(true));
    if (languageFilter) languageFilter.addEventListener('change', () => applyFiltersAndDisplay(true));
    if (licenseFilter) licenseFilter.addEventListener('change', () => applyFiltersAndDisplay(true));

    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', () => {
            if (generalSearchInput) generalSearchInput.value = '';
            if (languageFilter) languageFilter.value = '';
            if (licenseFilter) licenseFilter.value = '';
            applyFiltersAndDisplay(true);
        });
    }

    if (prevPageBtn && nextPageBtn) {
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderTablePage();
            }
        });
        nextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderTablePage();
            }
        });
    }

    allReposTableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.getAttribute('data-sort-key');
            if (sortKey === currentSortColumn) {
                currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortColumn = sortKey;
                currentSortDirection = 'asc';
            }
            document.querySelectorAll('#allReposTable th .sort-icon').forEach(icon => {
                icon.classList.remove('fa-sort-up', 'fa-sort-down');
                icon.classList.add('fa-sort');
            });
            const sortIcon = header.querySelector('.sort-icon');
            if (sortIcon) {
                sortIcon.classList.remove('fa-sort');
                sortIcon.classList.add(currentSortDirection === 'asc' ? 'fa-sort-up' : 'fa-sort-down');
            }
            applyFiltersAndDisplay(false);
        });
    });

    fetchAndProcessData();
});
