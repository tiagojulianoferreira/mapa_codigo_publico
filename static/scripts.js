document.addEventListener('DOMContentLoaded', () => {

    // === Elementos do DOM (Caché) ===
    const generalSearchInput = document.getElementById('generalSearchInput');
    const languageFilter = document.getElementById('languageFilter');
    const licenseFilter = document.getElementById('licenseFilter');
    const clearFiltersBtn = document.getElementById('clearFilters'); // Corrigido: ID no HTML é 'clearFilters'
    
    // Filtros individuais por coluna
    const columnFilters = document.querySelectorAll('#filterRow .filter-input');
    
    // Estatísticas Globais
    const totalReposGlobal = document.getElementById('totalReposGlobal');
    const mostUsedLanguageGlobal = document.getElementById('mostUsedLanguageGlobal');
    const mostUsedLicenseGlobal = document.getElementById('mostUsedLicenseGlobal');
    const naLicenseCountSpan = document.getElementById('naLicenseCount');

    // Estatísticas Filtradas
    const totalFilteredRepos = document.getElementById('totalFilteredRepos');
    const mostUsedFilteredLanguage = document.getElementById('mostUsedFilteredLanguage');
    const mostUsedFilteredLicense = document.getElementById('mostUsedFilteredLicense');
    let naFilteredLicenseCountSpan = document.getElementById('naFilteredLicenseCount');

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
    const cluster3AnalysisDate = document.getElementById('cluster3AnalysisDate');


    // === Variáveis de Estado ===
    let allRepos = [];
    let currentFilteredAndSortedRepos = [];
    let currentSortColumn = 'Estrelas';
    let currentSortDirection = 'desc';
    let currentPage = 1;
    const itemsPerPage = 20;
    let clusters = [];
    let clusterDescriptions = {};
    let searchTimeout;


    // === Funções Utilitárias ===

    /**
     * Mostra indicador de carregamento
     */
    function showLoading() {
        if (allReposTbody) {
            allReposTbody.innerHTML = `
                <tr>
                    <td colspan="9" class="p-8 text-center">
                        <div class="flex justify-center items-center space-x-2">
                            <i class="fas fa-spinner fa-spin text-blue-600 text-2xl"></i>
                            <span class="text-gray-600">Carregando dados...</span>
                        </div>
                    </td>
                </tr>
            `;
        }
    }

    /**
     * Mostra mensagem de erro
     */
    function showError(message) {
        if (allReposTbody) {
            allReposTbody.innerHTML = `
                <tr>
                    <td colspan="9" class="p-8 text-center text-red-600">
                        <i class="fas fa-exclamation-circle text-3xl mb-2"></i>
                        <p>${message}</p>
                    </td>
                </tr>
            `;
        }
    }

    /**
     * Conta a ocorrência de valores em um array de objetos.
     */
    function countOccurrences(data, key) {
        const counts = {};
        data.forEach(item => {
            const value = item[key];
            if (value && value.toString().toUpperCase() !== 'N/A') {
                counts[value] = (counts[value] || 0) + 1;
            }
        });
        return counts;
    }

    /**
     * Encontra a chave com o maior valor em um objeto de contagem.
     */
    function getMostCommon(counts) {
        const keys = Object.keys(counts);
        if (keys.length === 0) return null;
        return keys.reduce((a, b) => (counts[a] > counts[b] ? a : b));
    }

    /**
     * Formata data para exibição
     */
    function formatDate(dateString) {
        if (!dateString) return 'N/A';
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString('pt-BR');
        } catch {
            return dateString;
        }
    }


    // === Funções de Processamento e Renderização de Dados ===

    /**
     * Busca, processa e inicia a renderização dos dados da aplicação.
     */
    async function fetchAndProcessData() {
        showLoading();
        
        try {
            // Busca os dois arquivos JSON em paralelo
            const [responseMain, responseHighlighted] = await Promise.all([
                fetch('./repositorios_federais_filtrado_idioma.json'),
                fetch('./dados/repositorios_destaque_cluster_3.json')
            ]);

            if (!responseMain.ok || !responseHighlighted.ok) {
                throw new Error('Falha ao carregar os dados');
            }

            const dataMain = await responseMain.json();
            const dataHighlighted = await responseHighlighted.json();

            if (dataMain && dataMain.institutions_data) {
                // Processa os dados principais
                allRepos = [];
                dataMain.institutions_data.forEach(institution => {
                    institution.Repositorios.forEach(repo => {
                        repo.Instituicao = institution['Sigla'];
                        repo.InstituicaoNomeCompleto = institution['Nome Completo'];
                        repo.Tipo = institution['Tipo de Entidade'];
                        // Garantir que campos numéricos sejam números
                        repo.Estrelas = Number(repo.Estrelas) || 0;
                        repo.Forks = Number(repo.Forks) || 0;
                        repo.Contribuidores = Number(repo.Contribuidores) || 0;
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
                
                // Atualizar data da análise do cluster 3
                if (cluster3AnalysisDate) {
                    cluster3AnalysisDate.textContent = `Análise atualizada em: ${new Date().toLocaleDateString('pt-BR')}`;
                }
                
                applyFiltersAndDisplay(true);
            }

            if (dataHighlighted && dataHighlighted.repositorios_destaque_cluster_3) {
                renderHighlightedClusterRepos(dataHighlighted.repositorios_destaque_cluster_3);
            }
            
            console.log(`✅ Dados carregados: ${allRepos.length} repositórios encontrados.`);
        } catch (error) {
            console.error('❌ Erro ao buscar ou processar os dados:', error);
            showError('Falha ao carregar os dados. Tente novamente mais tarde.');
        }
    }

    /**
     * Preenche os menus suspensos de filtros.
     */
    function populateFilters() {
        const languages = [...new Set(allRepos.map(repo => repo['Linguagem Principal']).filter(Boolean))].sort();
        if (languageFilter) {
            languageFilter.innerHTML = `
                <option value="">Todas as linguagens</option>
                ${languages.map(lang => `<option value="${lang}">${lang}</option>`).join('')}
            `;
        }

        const licenses = [...new Set(allRepos.map(repo => repo['Licenca']).filter(l => l && l.toUpperCase() !== 'N/A'))].sort();
        if (licenseFilter) {
            licenseFilter.innerHTML = `
                <option value="">Todas as licenças</option>
                ${licenses.map(lic => `<option value="${lic}">${lic}</option>`).join('')}
            `;
        }
    }

    /**
     * Atualiza as estatísticas globais da página.
     */
    function updateGlobalStats() {
        if (totalReposGlobal) totalReposGlobal.textContent = allRepos.length;

        const languageCounts = countOccurrences(allRepos, 'Linguagem Principal');
        if (mostUsedLanguageGlobal) {
            const mostUsed = getMostCommon(languageCounts);
            mostUsedLanguageGlobal.textContent = mostUsed || 'N/A';
        }

        const licenseCounts = countOccurrences(allRepos, 'Licenca');
        const naCount = allRepos.filter(repo => !repo.Licenca || repo.Licenca.toUpperCase() === 'N/A').length;
        
        if (mostUsedLicenseGlobal) {
            const mostUsed = getMostCommon(licenseCounts);
            mostUsedLicenseGlobal.textContent = mostUsed || 'N/A';
        }
        
        if (naLicenseCountSpan) {
            naLicenseCountSpan.textContent = `(${naCount} ${naCount === 1 ? 'sem licença' : 'sem licença'})`;
        }

        if (clustersTbody && clusters.length > 0) {
            clustersTbody.innerHTML = clusters.map(cluster => `
                <tr class="hover:bg-gray-50">
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${cluster.id}</td>
                    <td class="px-6 py-4 text-sm text-gray-700">${cluster.description}</td>
                </tr>
            `).join('');
        }
    }

    /**
     * Atualiza as estatísticas dos resultados filtrados.
     */
    function updateFilteredStats(filteredRepos) {
        // Criar span dinamicamente se não existir
        if (!naFilteredLicenseCountSpan && mostUsedFilteredLicense) {
            const parent = mostUsedFilteredLicense.closest('.stat-item');
            if (parent) {
                naFilteredLicenseCountSpan = document.createElement('span');
                naFilteredLicenseCountSpan.id = 'naFilteredLicenseCount';
                naFilteredLicenseCountSpan.className = 'text-sm text-gray-500 italic mt-1 block';
                parent.appendChild(naFilteredLicenseCountSpan);
            }
        }

        if (totalFilteredRepos) {
            totalFilteredRepos.textContent = filteredRepos.length;
        }

        // Linguagem mais usada
        const languageCounts = countOccurrences(filteredRepos, 'Linguagem Principal');
        if (mostUsedFilteredLanguage) {
            mostUsedFilteredLanguage.textContent = getMostCommon(languageCounts) || 'N/A';
        }

        // Licença mais usada
        const licenseCounts = countOccurrences(filteredRepos, 'Licenca');
        if (mostUsedFilteredLicense) {
            mostUsedFilteredLicense.textContent = getMostCommon(licenseCounts) || 'N/A';
        }

        // Contagem de sem licença
        const naCount = filteredRepos.filter(repo => !repo.Licenca || repo.Licenca.toUpperCase() === 'N/A').length;
        if (naFilteredLicenseCountSpan) {
            naFilteredLicenseCountSpan.textContent = `(${naCount} ${naCount === 1 ? 'sem licença' : 'sem licença'})`;
        }
    }

    /**
     * Atualiza as listas de top 10 repositórios e linguagens.
     */
    function updateTopLists() {
        // Top 10 Repositórios por estrelas
        const topRepos = [...allRepos]
            .sort((a, b) => b.Estrelas - a.Estrelas)
            .slice(0, 10);
            
        if (topReposTbody) {
            topReposTbody.innerHTML = topRepos.map(repo => `
                <tr class="hover:bg-gray-50">
                    <td class="py-2 px-4">
                        <a href="${repo['Link de Acesso']}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 hover:underline">
                            ${repo['Nome do Repositório']}
                        </a>
                    </td>
                    <td class="py-2 px-4">${repo.Instituicao}</td>
                    <td class="py-2 px-4 font-medium">${repo.Estrelas}</td>
                </tr>
            `).join('');
        }

        // Top 10 Linguagens
        const languageCounts = countOccurrences(allRepos, 'Linguagem Principal');
        const sortedLanguages = Object.entries(languageCounts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 10);
            
        if (topLanguagesTbody) {
            topLanguagesTbody.innerHTML = sortedLanguages.map(([lang, count]) => `
                <tr class="hover:bg-gray-50">
                    <td class="py-2 px-4">${lang}</td>
                    <td class="py-2 px-4 font-medium">${count}</td>
                </tr>
            `).join('');
        }
    }

    /**
     * Atualiza a lista das 10 licenças mais usadas.
     */
    function updateTopLicenses() {
        const licenseCounts = countOccurrences(allRepos, 'Licenca');
        const sortedLicenses = Object.entries(licenseCounts)
            .sort(([, a], [, b]) => b - a)
            .slice(0, 10);
            
        if (topLicensesTbody) {
            topLicensesTbody.innerHTML = sortedLicenses.map(([license, count]) => `
                <tr class="hover:bg-gray-50">
                    <td class="py-2 px-4">${license}</td>
                    <td class="py-2 px-4 font-medium">${count}</td>
                </tr>
            `).join('');
        }
    }

    /**
     * Aplica filtros individuais por coluna
     */
    function applyColumnFilters(repo) {
        let matchesAllColumns = true;
        
        columnFilters.forEach(filter => {
            const filterKey = filter.dataset.filterKey;
            const filterValue = filter.value.toLowerCase().trim();
            
            if (filterValue) {
                const repoValue = repo[filterKey] ? repo[filterKey].toString().toLowerCase() : '';
                matchesAllColumns = matchesAllColumns && repoValue.includes(filterValue);
            }
        });
        
        return matchesAllColumns;
    }

    /**
     * Filtra, ordena e renderiza os repositórios na tabela principal.
     */
    function applyFiltersAndDisplay(resetPagination = false) {
        const generalSearchQuery = generalSearchInput?.value.toLowerCase() || '';
        const selectedLanguage = languageFilter?.value || '';
        const selectedLicense = licenseFilter?.value || '';

        let filteredRepos = allRepos.filter(repo => {
            // Filtro de pesquisa geral
            const matchesSearch = generalSearchQuery === '' || 
                (repo['Nome do Repositório'] || '').toLowerCase().includes(generalSearchQuery) ||
                (repo.Descricao || '').toLowerCase().includes(generalSearchQuery) ||
                (repo.Instituicao || '').toLowerCase().includes(generalSearchQuery);
            
            // Filtros de dropdown
            const matchesLanguage = !selectedLanguage || repo['Linguagem Principal'] === selectedLanguage;
            const matchesLicense = !selectedLicense || repo.Licenca === selectedLicense;
            
            // Filtros individuais por coluna
            const matchesColumnFilters = applyColumnFilters(repo);
            
            return matchesSearch && matchesLanguage && matchesLicense && matchesColumnFilters;
        });

        // Ordenação
        filteredRepos.sort((a, b) => {
            const isNumeric = ['Estrelas', 'Forks', 'Contribuidores'].includes(currentSortColumn);
            
            let valA = a[currentSortColumn];
            let valB = b[currentSortColumn];
            
            if (!isNumeric) {
                valA = (valA || '').toString().toLowerCase();
                valB = (valB || '').toString().toLowerCase();
            } else {
                valA = Number(valA) || 0;
                valB = Number(valB) || 0;
            }
            
            if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        currentFilteredAndSortedRepos = filteredRepos;
        
        if (filteredReposCount) {
            filteredReposCount.textContent = currentFilteredAndSortedRepos.length;
        }
        
        // Atualizar estatísticas filtradas
        updateFilteredStats(filteredRepos);
        
        if (resetPagination) currentPage = 1;
        renderTablePage();
    }

    /**
     * Renderiza a página atual da tabela principal.
     */
    function renderTablePage() {
        const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
        
        // Ajustar página atual se necessário
        if (currentPage > totalPages && totalPages > 0) {
            currentPage = totalPages;
        }
        
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const reposToDisplay = currentFilteredAndSortedRepos.slice(startIndex, endIndex);

        if (allReposTbody) {
            if (reposToDisplay.length === 0) {
                allReposTbody.innerHTML = `
                    <tr>
                        <td colspan="9" class="p-8 text-center text-gray-500">
                            <i class="fas fa-search text-4xl mb-2 text-gray-400"></i>
                            <p>Nenhum repositório encontrado com os filtros atuais.</p>
                        </td>
                    </tr>
                `;
            } else {
                allReposTbody.innerHTML = reposToDisplay.map(repo => `
                    <tr class="hover:bg-gray-50 transition-colors duration-150">
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Instituicao || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">${repo['Nome do Repositório'] || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo['Linguagem Principal'] || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Estrelas || 0}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Licenca || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${formatDate(repo['Ultima Atualizacao'])}</td>
                        <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title="${repo.Descricao || ''}">${repo.Descricao || 'Sem descrição'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo.Cluster_ID || 'N/A'}</td>
                        <td class="px-6 py-4 whitespace-nowrap text-sm text-center">
                            <a href="${repo['Link de Acesso']}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 hover:underline" title="Abrir repositório">
                                <i class="fas fa-external-link-alt"></i>
                            </a>
                        </td>
                    </tr>
                `).join('');
            }
        }

        if (pageInfoSpan) {
            pageInfoSpan.textContent = `Página ${currentPage} de ${totalPages || 1}`;
        }
        
        if (prevPageBtn) {
            prevPageBtn.disabled = currentPage === 1;
            prevPageBtn.classList.toggle('opacity-50', currentPage === 1);
        }
        
        if (nextPageBtn) {
            nextPageBtn.disabled = currentPage === totalPages || totalPages === 0;
            nextPageBtn.classList.toggle('opacity-50', currentPage === totalPages || totalPages === 0);
        }
    }

    /**
     * Renderiza a tabela do Cluster de Destaque.
     */
    function renderHighlightedClusterRepos(repositorios) {
        if (!cluster3Tbody) return;
        
        if (!repositorios || repositorios.length === 0) {
            cluster3Tbody.innerHTML = `
                <tr>
                    <td colspan="6" class="p-4 text-center text-gray-500">
                        Nenhum repositório em destaque encontrado.
                    </td>
                </tr>
            `;
            return;
        }

        const top10 = repositorios.slice(0, 10);
        cluster3Tbody.innerHTML = top10.map(repo => `
            <tr class="hover:bg-gray-50 transition-colors duration-150">
                <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <a href="${repo['Link de Acesso']}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800 hover:underline">
                        ${repo['Nome do Repositório']}
                    </a>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500 max-w-xs truncate" title="${repo.Descricao || ''}">
                    ${repo.Descricao || 'Sem descrição'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900 font-medium">${repo.Estrelas || 0}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">${repo['Linguagem Principal'] || 'N/A'}</td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    ${repo.Organizacao ? 
                        '<span class="px-2 py-1 bg-purple-100 text-purple-800 rounded-full text-xs">Organização</span>' : 
                        '<span class="px-2 py-1 bg-gray-100 text-gray-800 rounded-full text-xs">Pessoal</span>'}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-center">
                    <a href="${repo['Link de Acesso']}" target="_blank" rel="noopener noreferrer" class="text-blue-600 hover:text-blue-800" title="Abrir repositório">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
            </tr>
        `).join('');
    }

    /**
     * Reseta todos os filtros
     */
    function resetAllFilters() {
        if (generalSearchInput) generalSearchInput.value = '';
        if (languageFilter) languageFilter.value = '';
        if (licenseFilter) licenseFilter.value = '';
        
        // Resetar filtros individuais
        columnFilters.forEach(filter => {
            filter.value = '';
        });
        
        applyFiltersAndDisplay(true);
    }


    // === Listeners de Eventos ===

    // Pesquisa geral com debounce
    if (generalSearchInput) {
        generalSearchInput.addEventListener('input', () => {
            clearTimeout(searchTimeout);
            searchTimeout = setTimeout(() => applyFiltersAndDisplay(true), 300);
        });
    }

    // Filtros de dropdown
    if (languageFilter) {
        languageFilter.addEventListener('change', () => applyFiltersAndDisplay(true));
    }
    
    if (licenseFilter) {
        licenseFilter.addEventListener('change', () => applyFiltersAndDisplay(true));
    }

    // Filtros individuais por coluna
    columnFilters.forEach(filter => {
        filter.addEventListener('input', () => applyFiltersAndDisplay(true));
    });

    // Botão limpar filtros
    if (clearFiltersBtn) {
        clearFiltersBtn.addEventListener('click', resetAllFilters);
    }

    // Paginação
    if (prevPageBtn) {
        prevPageBtn.addEventListener('click', () => {
            if (currentPage > 1) {
                currentPage--;
                renderTablePage();
            }
        });
    }
    
    if (nextPageBtn) {
        nextPageBtn.addEventListener('click', () => {
            const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
            if (currentPage < totalPages) {
                currentPage++;
                renderTablePage();
            }
        });
    }

    // Ordenação
    allReposTableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const sortKey = header.getAttribute('data-sort-key');
            
            if (sortKey === currentSortColumn) {
                currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortColumn = sortKey;
                currentSortDirection = 'asc';
            }
            
            // Atualizar ícones de ordenação
            document.querySelectorAll('#allReposTable th .sort-icon').forEach(icon => {
                icon.className = 'fas fa-sort sort-icon ml-1';
            });
            
            const sortIcon = header.querySelector('.sort-icon');
            if (sortIcon) {
                sortIcon.className = `fas fa-sort-${currentSortDirection === 'asc' ? 'up' : 'down'} sort-icon ml-1`;
            }
            
            applyFiltersAndDisplay(false);
        });
    });

    // Atalho de teclado para limpar filtros (ESC)
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && 
            (document.activeElement === generalSearchInput || 
             document.activeElement?.classList.contains('filter-input'))) {
            resetAllFilters();
            e.target.blur();
        }
    });

    // === Inicialização da Aplicação ===
    fetchAndProcessData();
});