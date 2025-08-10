document.addEventListener('DOMContentLoaded', () => {
    // === Elementos do DOM ===
    const generalSearchInput = document.getElementById('generalSearchInput');
    const languageFilter = document.getElementById('languageFilter');
    const licenseFilter = document.getElementById('licenseFilter');
    const clearFiltersBtn = document.getElementById('clearFilters');

    // Elementos para Estatísticas Globais
    const totalReposGlobal = document.getElementById('totalReposGlobal');
    const mostUsedLanguageGlobal = document.getElementById('mostUsedLanguageGlobal');
    const mostUsedLicenseGlobal = document.getElementById('mostUsedLicenseGlobal');
    const naLicenseCountSpan = document.getElementById('naLicenseCount');

    // Elementos para Top Linguagens
    const topLanguagesTbody = document.getElementById('topLanguagesTbody');

    // Elementos para Top Repositórios
    const topReposTbody = document.getElementById('topReposTbody');

    // Novo elemento para Top Licenças
    const topLicensesTbody = document.getElementById('topLicensesTbody');

    // Elementos para Tabela de Todos os Repositórios
    const allReposTbody = document.getElementById('allReposTbody');
    const allReposTableHeaders = document.querySelectorAll('#allReposTable thead tr:first-child th[data-sort-key]');
    const allReposFilterInputs = document.querySelectorAll('#filterRow .filter-input');
    const filteredReposCount = document.getElementById('filteredReposCount');

    // Elementos para Tabela de Clusters (assumindo que o HTML tem esta seção)
    const clustersTbody = document.getElementById('clustersTbody');

    // Elementos para Paginação
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');

    // === Variáveis de Estado ===
    let allRepos = [];
    let allInstitutions = [];
    let currentFilteredAndSortedRepos = [];
    let currentSortColumn = 'Estrelas'; // Coluna de ordenação padrão
    let currentSortDirection = 'desc'; // Direção de ordenação padrão
    let currentPage = 1;
    const itemsPerPage = 20;
    
    // Variáveis para clusters
    let clusters = [];
    let clusterDescriptions = {};


    // === FUNÇÕES DE PROCESSAMENTO E RENDERIZAÇÃO ===

    /**
     * Busca os dados do arquivo JSON, processa e inicia a aplicação.
     */
    async function fetchAndProcessData() {
        try {
            // Acessa o arquivo JSON diretamente no repositório local
            const response = await fetch('./repositorios_federais_filtrado_idioma.json');
            const data = await response.json();
            
            if (data && data.institutions_data) {
                // Limpa o array de repositórios antes de preencher
                allRepos = [];
                allInstitutions = [];

                // Itera sobre as instituições para extrair os repositórios
                data.institutions_data.forEach(institution => {
                    const institutionName = institution['Nome Completo'];
                    const institutionSigla = institution['Sigla'];
                    allInstitutions.push(institutionName);

                    // Adiciona a sigla e o nome da instituição a cada repositório
                    // para facilitar a filtragem e a exibição
                    institution.Repositorios.forEach(repo => {
                        repo.Instituicao = institutionSigla;
                        repo.InstituicaoNomeCompleto = institutionName;
                        allRepos.push(repo);
                    });
                });
                
                // Se houver dados de cluster no JSON, armazena-os
                if (data.cluster_descriptions) {
                    clusters = data.cluster_descriptions;
                    clusterDescriptions = clusters.reduce((acc, curr) => {
                        acc[curr.id] = curr.description;
                        return acc;
                    }, {});
                }

                // Inicia o processamento e exibição
                populateFilters();
                updateGlobalStats();
                updateTopLists();
                updateTopLicenses();
                applyFiltersAndDisplay(true); // Inicializa a tabela principal
                
                console.log(`Dados carregados: ${allRepos.length} repositórios encontrados.`);

            } else {
                displayLoadingMessage('Nenhum dado de repositório encontrado.');
            }

        } catch (error) {
            console.error('Erro ao buscar ou processar os dados:', error);
            displayLoadingMessage('Erro ao carregar os dados. Verifique o console para mais detalhes.');
        }
    }

    /**
     * Preenche os menus suspensos e os campos de filtro da tabela.
     */
    function populateFilters() {
        // Popula o filtro de linguagens
        const languages = [...new Set(allRepos.map(repo => repo['Linguagem Principal']))].filter(Boolean).sort();
        languageFilter.innerHTML = '<option value="">Todas</option>' + languages.map(lang => `<option value="${lang}">${lang}</option>`).join('');

        // Popula o filtro de licenças
        const licenses = [...new Set(allRepos.map(repo => repo['Licenca']))].filter(Boolean).sort();
        licenseFilter.innerHTML = '<option value="">Todas</option>' + licenses.map(lic => `<option value="${lic}">${lic}</option>`).join('');
    }

    /**
     * Atualiza os painéis de estatísticas globais.
     */
    function updateGlobalStats() {
        // Total de Repositórios
        totalReposGlobal.textContent = allRepos.length;

        // Linguagem Mais Usada
        const languageCounts = {};
        allRepos.forEach(repo => {
            const lang = repo['Linguagem Principal'];
            if (lang) {
                languageCounts[lang] = (languageCounts[lang] || 0) + 1;
            }
        });
        const mostUsedLanguage = Object.keys(languageCounts).reduce((a, b) => languageCounts[a] > languageCounts[b] ? a : b, null);
        mostUsedLanguageGlobal.textContent = mostUsedLanguage || 'N/A';

        // Licença Mais Usada
        const licenseCounts = {};
        let naCount = 0;
        allRepos.forEach(repo => {
            const license = repo['Licenca'];
            if (license) {
                if (license.toUpperCase() === 'N/A') {
                    naCount++;
                } else {
                    licenseCounts[license] = (licenseCounts[license] || 0) + 1;
                }
            }
        });
        const mostUsedLicense = Object.keys(licenseCounts).reduce((a, b) => (licenseCounts[a] > licenseCounts[b] ? a : b), null);
        mostUsedLicenseGlobal.textContent = mostUsedLicense || 'N/A';
        naLicenseCountSpan.textContent = `(${naCount} sem licença)`;
        
        // Renderiza as descrições dos clusters se existirem
        if (clustersTbody && clusters.length > 0) {
            clustersTbody.innerHTML = clusters.map(cluster => `
                <tr>
                    <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${cluster.id}</td>
                    <td class="px-6 py-4 text-sm text-gray-700">${cluster.description}</td>
                </tr>
            `).join('');
        }
    }

    /**
     * Atualiza as listas de "Top Repositórios" e "Top Linguagens".
     */
    function updateTopLists() {
        // Top 10 Linguagens
        const languageCounts = {};
        allRepos.forEach(repo => {
            const lang = repo['Linguagem Principal'];
            if (lang) {
                languageCounts[lang] = (languageCounts[lang] || 0) + 1;
            }
        });
        const sortedLanguages = Object.entries(languageCounts)
            .sort(([, countA], [, countB]) => countB - countA)
            .slice(0, 10);
        topLanguagesTbody.innerHTML = sortedLanguages.map(([lang, count]) => `
            <tr>
                <td class="px-4 py-2">${lang}</td>
                <td class="px-4 py-2">${count}</td>
            </tr>
        `).join('');

        // Top 10 Repositórios por Estrelas
        const sortedRepos = [...allRepos].sort((a, b) => b.Estrelas - a.Estrelas).slice(0, 10);
        topReposTbody.innerHTML = sortedRepos.map(repo => `
            <tr>
                <td class="px-4 py-2"><a href="${repo['Link de Acesso']}" target="_blank" class="repo-link">${repo['Nome do Repositório']}</a></td>
                <td class="px-4 py-2">${repo.Instituicao}</td>
                <td class="px-4 py-2"><i class="fas fa-star text-yellow-400"></i> ${repo.Estrelas}</td>
            </tr>
        `).join('');
    }

    /**
     * Atualiza a lista de "Top 10 Licenças".
     */
    function updateTopLicenses() {
        const licenseCounts = {};
        allRepos.forEach(repo => {
            const license = repo['Licenca'];
            if (license) {
                licenseCounts[license] = (licenseCounts[license] || 0) + 1;
            }
        });
        const sortedLicenses = Object.entries(licenseCounts)
            .sort(([, countA], [, countB]) => countB - countA)
            .slice(0, 10);
        topLicensesTbody.innerHTML = sortedLicenses.map(([license, count]) => `
            <tr>
                <td class="px-4 py-2">${license}</td>
                <td class="px-4 py-2">${count}</td>
            </tr>
        `).join('');
    }

    /**
     * Aplica todos os filtros e ordenações e exibe os resultados na tabela.
     * @param {boolean} resetPage - Define se a página deve ser resetada para a primeira.
     */
    function applyFiltersAndDisplay(resetPage = false) {
        // 1. Filtra os repositórios
        let filteredRepos = allRepos.filter(repo => {
            const generalSearchTerm = generalSearchInput.value.toLowerCase();
            const languageFilterValue = languageFilter.value;
            const licenseFilterValue = licenseFilter.value;

            // Filtros da tabela
            const filterNome = document.querySelector('[data-filter-key="Nome do Repositório"]').value.toLowerCase();
            const filterInstituicao = document.querySelector('[data-filter-key="Instituicao"]').value.toLowerCase();
            const filterDescricao = document.querySelector('[data-filter-key="Descricao"]').value.toLowerCase();
            const filterLinguagem = document.querySelector('[data-filter-key="Linguagem Principal"]').value.toLowerCase();
            const filterEstrelas = document.querySelector('[data-filter-key="Estrelas"]').value.toLowerCase();
            const filterLicenca = document.querySelector('[data-filter-key="Licenca"]').value.toLowerCase();
            const filterData = document.querySelector('[data-filter-key="Ultima Atualizacao"]').value.toLowerCase();
            const filterCluster = document.querySelector('[data-filter-key="Cluster_ID"]').value.toLowerCase();


            const matchesGeneralSearch = !generalSearchTerm ||
                (repo['Nome do Repositório'] && repo['Nome do Repositório'].toLowerCase().includes(generalSearchTerm)) ||
                (repo['Descricao'] && repo['Descricao'].toLowerCase().includes(generalSearchTerm)) ||
                (repo['InstituicaoNomeCompleto'] && repo['InstituicaoNomeCompleto'].toLowerCase().includes(generalSearchTerm)) ||
                (repo['Instituicao'] && repo['Instituicao'].toLowerCase().includes(generalSearchTerm));

            const matchesLanguage = !languageFilterValue || repo['Linguagem Principal'] === languageFilterValue;
            const matchesLicense = !licenseFilterValue || repo['Licenca'] === licenseFilterValue;

            const matchesFilterNome = !filterNome || (repo['Nome do Repositório'] && repo['Nome do Repositório'].toLowerCase().includes(filterNome));
            const matchesFilterInstituicao = !filterInstituicao || (repo['Instituicao'] && repo['Instituicao'].toLowerCase().includes(filterInstituicao));
            const matchesFilterDescricao = !filterDescricao || (repo['Descricao'] && repo['Descricao'].toLowerCase().includes(filterDescricao));
            const matchesFilterLinguagem = !filterLinguagem || (repo['Linguagem Principal'] && repo['Linguagem Principal'].toLowerCase().includes(filterLinguagem));
            const matchesFilterEstrelas = !filterEstrelas || (repo['Estrelas'] !== undefined && String(repo['Estrelas']).includes(filterEstrelas));
            const matchesFilterLicenca = !filterLicenca || (repo['Licenca'] && repo['Licenca'].toLowerCase().includes(filterLicenca));
            const matchesFilterData = !filterData || (repo['Ultima Atualizacao'] && repo['Ultima Atualizacao'].toLowerCase().includes(filterData));
            const matchesFilterCluster = !filterCluster || (repo['Cluster_ID'] !== undefined && String(repo['Cluster_ID']).includes(filterCluster));


            return matchesGeneralSearch && matchesLanguage && matchesLicense &&
                   matchesFilterNome && matchesFilterInstituicao && matchesFilterDescricao &&
                   matchesFilterLinguagem && matchesFilterEstrelas && matchesFilterLicenca &&
                   matchesFilterData && matchesFilterCluster;
        });

        // 2. Ordena os repositórios
        filteredRepos.sort((a, b) => {
            const valA = a[currentSortColumn] !== null ? a[currentSortColumn] : (currentSortDirection === 'asc' ? '' : 'zzzz');
            const valB = b[currentSortColumn] !== null ? b[currentSortColumn] : (currentSortDirection === 'asc' ? '' : 'zzzz');

            if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
            if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
            return 0;
        });

        currentFilteredAndSortedRepos = filteredRepos;

        // 3. Atualiza a contagem de repositórios filtrados
        if (filteredReposCount) {
            filteredReposCount.textContent = filteredRepos.length;
        }

        // Reseta a página se a filtragem/ordenação mudou
        if (resetPage) {
            currentPage = 1;
        }

        renderAllRepos();
    }

    /**
     * Renderiza a tabela de repositórios para a página atual.
     */
    function renderAllRepos() {
        allReposTbody.innerHTML = '';
        if (currentFilteredAndSortedRepos.length === 0) {
            allReposTbody.innerHTML = '<tr><td colspan="9" class="p-4 text-center text-gray-500">Nenhum repositório encontrado.</td></tr>';
            pageInfoSpan.textContent = 'Página 0 de 0';
            prevPageBtn.disabled = true;
            nextPageBtn.disabled = true;
            return;
        }

        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedRepos = currentFilteredAndSortedRepos.slice(startIndex, endIndex);

        const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);

        paginatedRepos.forEach(repo => {
            const tr = document.createElement('tr');
            tr.className = 'hover:bg-gray-50 transition duration-150';

            // Formata a data para um formato mais legível
            const formattedDate = repo['Ultima Atualizacao'] ? new Date(repo['Ultima Atualizacao']).toLocaleDateString('pt-BR') : 'N/A';

            // Garante que a descrição não seja nula
            const descricao = repo['Descricao'] || 'Sem descrição';

            // Trunca a descrição para exibição na tabela
            const truncatedDesc = descricao.length > 100 ? descricao.substring(0, 97) + '...' : descricao;
            
            // Acesso seguro ao Cluster_ID
            const clusterId = repo['Cluster_ID'] !== undefined ? repo['Cluster_ID'] : 'N/A';

            tr.innerHTML = `
                <td class="p-4 border-b text-sm text-gray-900">${repo['Instituicao']}</td>
                <td class="p-4 border-b text-sm text-gray-900">${repo['Nome do Repositório']}</td>
                <td class="p-4 border-b text-sm text-gray-700">${repo['Linguagem Principal'] || 'N/A'}</td>
                <td class="p-4 border-b text-sm text-gray-700"><i class="fas fa-star text-yellow-400"></i> ${repo['Estrelas']}</td>
                <td class="p-4 border-b text-sm text-gray-700">${repo['Licenca'] || 'N/A'}</td>
                <td class="p-4 border-b text-sm text-gray-700">${formattedDate}</td>
                <td class="p-4 border-b text-sm text-gray-700 truncate-text" title="${descricao}">${truncatedDesc}</td>
                <td class="p-4 border-b text-sm text-gray-700">${clusterId}</td>
                <td class="p-4 border-b text-center text-sm">
                    <a href="${repo['Link de Acesso']}" target="_blank" class="text-blue-600 hover:text-blue-800 transition-colors">
                        <i class="fas fa-external-link-alt"></i>
                    </a>
                </td>
            `;
            allReposTbody.appendChild(tr);
        });

        // Atualiza a paginação
        pageInfoSpan.textContent = `Página ${currentPage} de ${totalPages}`;
        prevPageBtn.disabled = currentPage === 1;
        nextPageBtn.disabled = currentPage === totalPages;
    }

    /**
     * Exibe uma mensagem de carregamento ou de erro na tabela principal.
     * @param {string} message - A mensagem a ser exibida.
     */
    function displayLoadingMessage(message) {
        allReposTbody.innerHTML = `<tr><td colspan="9" class="p-4 text-center text-gray-500 loading-message">${message}</td></tr>`;
    }

    // === EVENT LISTENERS ===

    // Eventos de filtro global
    generalSearchInput.addEventListener('input', () => applyFiltersAndDisplay(true));
    languageFilter.addEventListener('change', () => applyFiltersAndDisplay(true));
    licenseFilter.addEventListener('change', () => applyFiltersAndDisplay(true));
    
    // Evento para limpar filtros
    clearFiltersBtn.addEventListener('click', () => {
        generalSearchInput.value = '';
        languageFilter.value = '';
        licenseFilter.value = '';
        allReposFilterInputs.forEach(input => input.value = '');

        // Reseta a ordenação para o padrão
        allReposTableHeaders.forEach(th => th.classList.remove('asc', 'desc'));
        const defaultHeader = document.querySelector('[data-sort-key="Estrelas"]');
        if (defaultHeader) {
            defaultHeader.classList.add('desc');
            const icon = defaultHeader.querySelector('.sort-icon');
            if (icon) icon.className = 'fas fa-sort-down sort-icon';
        }

        currentSortColumn = 'Estrelas';
        currentSortDirection = 'desc';

        applyFiltersAndDisplay(true);
    });

    // Eventos de filtro e ordenação da tabela
    allReposFilterInputs.forEach(input => {
        input.addEventListener('input', () => applyFiltersAndDisplay(true));
    });

    allReposTableHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const column = header.getAttribute('data-sort-key');
            if (!column) return;

            // Remove a classe de ordenação e reseta o ícone de todos os outros cabeçalhos
            allReposTableHeaders.forEach(th => {
                if (th !== header) {
                    th.classList.remove("asc", "desc");
                    const icon = th.querySelector(".sort-icon");
                    if (icon) icon.className = "fas fa-sort sort-icon";
                }
            });

            if (currentSortColumn === column) {
                currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
            } else {
                currentSortColumn = column;
                currentSortDirection = 'asc';
            }

            header.classList.remove("asc", "desc");
            header.classList.add(currentSortDirection);
            
            const currentIcon = header.querySelector(".sort-icon");
            if (currentIcon) {
                currentIcon.className = `fas fa-sort-${currentSortDirection === 'asc' ? 'up' : 'down'} sort-icon`;
            }

            currentPage = 1; // Reseta para a primeira página ao mudar a ordenação
            applyFiltersAndDisplay();
        });
    });

    // Event listeners para paginação
    prevPageBtn.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            applyFiltersAndDisplay();
        }
    });

    nextPageBtn.addEventListener("click", () => {
        const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            applyFiltersAndDisplay();
        }
    });

    // Inicia a aplicação
    fetchAndProcessData();
});