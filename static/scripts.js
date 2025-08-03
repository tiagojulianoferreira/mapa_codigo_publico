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
    const naLicenseCountSpan = document.getElementById('naLicenseCount'); // Novo elemento

    // Elementos para Top Linguagens
    const topLanguagesTbody = document.getElementById('topLanguagesTbody');

    // Elementos para Top Repositórios
    const topReposTbody = document.getElementById('topReposTbody');

    // Elementos para Tabela de Todos os Repositórios
    const allReposTbody = document.getElementById('allReposTbody');
    const allReposTableHeaders = document.querySelectorAll('#allReposTable thead tr:first-child th[data-sort-key]');
    const allReposFilterInputs = document.querySelectorAll('#filterRow .filter-input');
    const filteredReposCount = document.getElementById('filteredReposCount');

    // Elementos para Tabela de Clusters
    const clustersTbody = document.getElementById('clustersTbody');

    // Elementos de Paginação
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');

    // === Variáveis de Dados ===
    let allInstitutionsData = [];
    let clusterDescriptions = [];
    let allFlattenedRepos = [];
    let currentFilteredAndSortedRepos = [];
    let calculatedTop10Languages = [];
    let calculatedTop10Repos = [];

    // Variáveis de estado
    let currentPage = 1;
    const itemsPerPage = 50;
    let currentSortColumn = null;
    let currentSortDirection = 'asc';

    // --- Lógica de Carregamento de Dados ---
    async function fetchAndProcessData() {
        try {
            const response = await fetch('repositorios_filtrados.json');
            if (!response.ok) {
                // Atualiza todas as mensagens de erro se o arquivo não puder ser carregado
                allReposTbody.innerHTML = `<tr><td colspan="9" class="error-message">Erro ao carregar os dados: Arquivo 'repositorios_federais_com_clusters_visualizado.json' não encontrado ou inacessível.</td></tr>`;
                topReposTbody.innerHTML = `<tr><td colspan="5" class="error-message">Erro ao carregar top repositórios.</td></tr>`;
                clustersTbody.innerHTML = `<tr><td colspan="2" class="error-message">Erro ao carregar clusters.</td></tr>`;
                topLanguagesTbody.innerHTML = `<tr><td colspan="3" class="error-message">Erro ao carregar top linguagens.</td></tr>`;
                throw new Error(`Erro ao carregar o JSON: ${response.statusText} (Status: ${response.status})`);
            }
            const jsonData = await response.json();

            allInstitutionsData = jsonData.institutions_data || [];
            clusterDescriptions = jsonData.cluster_descriptions || [];

            const tempLanguageCounts = {};
            const availableLanguages = new Set();
            const availableLicenses = new Set();
            
            // Achata os dados para ter uma lista única de repositórios
            allFlattenedRepos = allInstitutionsData.flatMap(institution => {
                return institution.Repositorios.map(repo => {
                    const fullRepo = {
                        ...repo,
                        'Instituicao': institution['Nome Completo'],
                        'SiglaInstituicao': institution.Sigla,
                    };
                    // Garante que Cluster_ID e outros campos existem
                    fullRepo['Cluster_ID'] = fullRepo['Cluster_ID'] || 'N/A';
                    fullRepo['Linguagem Principal'] = fullRepo['Linguagem Principal'] || 'N/A';
                    fullRepo.Licenca = fullRepo.Licenca || 'N/A';
                    fullRepo.Descricao = fullRepo.Descricao || 'Sem descrição';

                    // Coleta dados para filtros e estatísticas
                    if (fullRepo['Linguagem Principal'] !== 'N/A') {
                        availableLanguages.add(fullRepo['Linguagem Principal']);
                        tempLanguageCounts[fullRepo['Linguagem Principal']] = (tempLanguageCounts[fullRepo['Linguagem Principal']] || 0) + 1;
                    }
                    if (fullRepo.Licenca) { // Licenças nulas ou vazias já são tratadas como 'N/A'
                        availableLicenses.add(fullRepo.Licenca);
                    }
                    return fullRepo;
                });
            });

            // Calcula as top 10 linguagens
            calculatedTop10Languages = Object.entries(tempLanguageCounts)
                .map(([language, count]) => ({ language, count }))
                .sort((a, b) => b.count - a.count)
                .slice(0, 10);

            // Calcula os top 10 repositórios por estrelas
            calculatedTop10Repos = [...allFlattenedRepos]
                .sort((a, b) => (b.Estrelas || 0) - (a.Estrelas || 0))
                .slice(0, 10);

            // Popula os filtros e as tabelas adicionais
            populateFilter(languageFilter, Array.from(availableLanguages).sort());
            
            // Filtra as licenças disponíveis para não incluir 'N/A' no dropdown
            const filteredLicensesForDropdown = Array.from(availableLicenses).filter(lic => lic !== 'N/A').sort();
            populateFilter(licenseFilter, filteredLicensesForDropdown);

            populateClustersTable();
            displayTopReposTable(calculatedTop10Repos);
            displayTopLanguagesTable(calculatedTop10Languages);
            updateGlobalStats();

            // Aplica filtros e exibe a tabela principal
            applyFiltersAndDisplay();

        } catch (error) {
            console.error("Erro ao carregar ou processar os dados:", error);
        }
    }

    // --- Funções Auxiliares de Display e Lógica ---

    function populateFilter(selectElement, optionsArray) {
        selectElement.innerHTML = '<option value="">Todas</option>';
        optionsArray.forEach(optionText => {
            const option = document.createElement('option');
            option.value = optionText;
            option.textContent = optionText;
            selectElement.appendChild(option);
        });
    }

    function populateClustersTable() {
        clustersTbody.innerHTML = '';
        if (clusterDescriptions.length === 0) {
            clustersTbody.innerHTML = `<tr><td colspan="2" class="no-data-message">Nenhum cluster encontrado.</td></tr>`;
            return;
        }
        clusterDescriptions.forEach(cluster => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${cluster.id}</td>
                <td>${cluster.description}</td>
            `;
            clustersTbody.appendChild(row);
        });
    }

    function displayTopReposTable(repos) {
        topReposTbody.innerHTML = '';
        if (repos.length === 0) {
            topReposTbody.innerHTML = `<tr><td colspan="5" class="no-data-message">Nenhum repositório top encontrado.</td></tr>`;
            return;
        }
        repos.forEach(repo => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${repo.SiglaInstituicao}</td>
                <td><a href="${repo['Link de Acesso']}" target="_blank">${repo['Nome do Repositório']}</a></td>
                <td>${repo.Estrelas}</td>
                <td><span class="badge">${repo['Linguagem Principal']}</span></td>
                <td>${new Date(repo['Ultima Atualizacao']).toLocaleDateString('pt-BR')}</td>
            `;
            topReposTbody.appendChild(row);
        });
    }

    function displayTopLanguagesTable(languages) {
        topLanguagesTbody.innerHTML = '';
        if (languages.length === 0) {
            topLanguagesTbody.innerHTML = `<tr><td colspan="3" class="no-data-message">Nenhuma linguagem encontrada.</td></tr>`;
            return;
        }
        const totalRepos = allFlattenedRepos.length;
        languages.forEach(lang => {
            const percentage = ((lang.count / totalRepos) * 100).toFixed(2);
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${lang.language}</td>
                <td>${lang.count}</td>
                <td>${percentage}%</td>
            `;
            topLanguagesTbody.appendChild(row);
        });
    }

    function updateGlobalStats() {
        totalReposGlobal.textContent = allFlattenedRepos.length;
        
        const mostUsedLanguage = calculatedTop10Languages.length > 0 ? calculatedTop10Languages[0].language : 'N/A';
        mostUsedLanguageGlobal.textContent = mostUsedLanguage;
        
        const licenseCounts = {};
        allFlattenedRepos.forEach(repo => {
            const lic = repo.Licenca || 'N/A';
            licenseCounts[lic] = (licenseCounts[lic] || 0) + 1;
        });

        // --- INÍCIO DA ALTERAÇÃO ---
        const naCount = licenseCounts['N/A'] || 0; // Obtém a contagem de N/A
        
        const filteredLicenses = Object.entries(licenseCounts).filter(([lic]) => lic !== 'N/A');
        
        const mostUsedLicense = filteredLicenses.length > 0
            ? filteredLicenses.sort(([, a], [, b]) => b - a)[0][0]
            : 'Não Informado';
        
        mostUsedLicenseGlobal.textContent = mostUsedLicense;
        
        // Exibe a contagem de N/A somente se houver algum
        if (naCount > 0) {
            naLicenseCountSpan.textContent = `(${naCount} sem licença registrada)`;
        } else {
            naLicenseCountSpan.textContent = '';
        }
        // --- FIM DA ALTERAÇÃO ---
    }

    function applyFilters() {
        let tempRepos = [...allFlattenedRepos];
        const generalSearchTerm = generalSearchInput.value.toLowerCase().trim();
        const language = languageFilter.value;
        const license = licenseFilter.value;

        if (generalSearchTerm) {
            tempRepos = tempRepos.filter(repo => 
                (repo['Nome do Repositório'] && repo['Nome do Repositório'].toLowerCase().includes(generalSearchTerm)) ||
                (repo.Descricao && repo.Descricao.toLowerCase().includes(generalSearchTerm)) ||
                (repo.SiglaInstituicao && repo.SiglaInstituicao.toLowerCase().includes(generalSearchTerm)) ||
                (repo.Instituicao && repo.Instituicao.toLowerCase().includes(generalSearchTerm))
            );
        }

        if (language) {
            tempRepos = tempRepos.filter(repo => repo['Linguagem Principal'] === language);
        }

        if (license) {
            tempRepos = tempRepos.filter(repo => repo.Licenca === license);
        }

        allReposFilterInputs.forEach(input => {
            const key = input.dataset.filterKey;
            const value = input.value.toLowerCase().trim();
            if (value) {
                tempRepos = tempRepos.filter(repo => {
                    const repoValue = repo[key] ? String(repo[key]).toLowerCase() : '';
                    return repoValue.includes(value);
                });
            }
        });

        return tempRepos;
    }

    function sortRepos(repos) {
        if (!currentSortColumn) {
            return repos;
        }

        return repos.sort((a, b) => {
            let valA = a[currentSortColumn];
            let valB = b[currentSortColumn];

            valA = valA === null || valA === undefined ? (currentSortDirection === 'asc' ? '' : 'zzzzz') : valA;
            valB = valB === null || valB === undefined ? (currentSortDirection === 'asc' ? '' : 'zzzzz') : valB;

            if (typeof valA === 'number' && typeof valB === 'number') {
                return currentSortDirection === 'asc' ? valA - valB : valB - valA;
            }

            if (typeof valA === 'string' && typeof valB === 'string') {
                return currentSortDirection === 'asc' ? valA.localeCompare(valB) : valB.localeCompare(valA);
            }

            const dateA = new Date(valA);
            const dateB = new Date(valB);
            if (!isNaN(dateA) && !isNaN(dateB)) {
                return currentSortDirection === 'asc' ? dateA.getTime() - dateB.getTime() : dateB.getTime() - dateA.getTime();
            }

            return currentSortDirection === 'asc' ? String(valA).localeCompare(String(valB)) : String(valB).localeCompare(String(a));
        });
    }

    function displayAllReposTable(repos) {
        allReposTbody.innerHTML = '';
        if (repos.length === 0) {
            allReposTbody.innerHTML = `<tr><td colspan="9" class="no-data-message">Nenhum repositório encontrado com os filtros aplicados.</td></tr>`;
            updatePaginationControls(0, 0, 0);
            filteredReposCount.textContent = 0;
            return;
        }

        const start = (currentPage - 1) * itemsPerPage;
        const end = start + itemsPerPage;
        const paginatedItems = repos.slice(start, end);

        paginatedItems.forEach(repo => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${repo.SiglaInstituicao}</td>
                <td><a href="${repo['Link de Acesso']}" target="_blank" class="repo-link">${repo['Nome do Repositório']}</a></td>
                <td><span class="badge">${repo['Linguagem Principal']}</span></td>
                <td>${repo.Estrelas || '0'}</td>
                <td>${repo.Licenca || 'N/A'}</td>
                <td>${new Date(repo['Ultima Atualizacao']).toLocaleDateString('pt-BR')}</td>
                <td>${repo.Descricao}</td>
                <td>${repo['Cluster_ID']}</td>
                <td><a href="${repo['Link de Acesso']}" target="_blank" title="Acessar Repositório"><i class="fas fa-external-link-alt"></i></a></td>
            `;
            allReposTbody.appendChild(row);
        });

        filteredReposCount.textContent = repos.length;
        updatePaginationControls(repos.length, currentPage, itemsPerPage);
    }

    function updatePaginationControls(totalItems, page, limit) {
        const totalPages = Math.ceil(totalItems / limit);
        pageInfoSpan.textContent = `Página ${page} de ${totalPages}`;
        prevPageBtn.disabled = page === 1;
        nextPageBtn.disabled = page >= totalPages || totalPages === 0;
    }

    function applyFiltersAndDisplay() {
        currentFilteredAndSortedRepos = applyFilters();
        const sortedRepos = sortRepos(currentFilteredAndSortedRepos);
        displayAllReposTable(sortedRepos);
    }

    // --- Listeners de Eventos ---
    generalSearchInput.addEventListener("input", () => {
        currentPage = 1;
        applyFiltersAndDisplay();
    });
    languageFilter.addEventListener("change", () => {
        currentPage = 1;
        applyFiltersAndDisplay();
    });
    licenseFilter.addEventListener("change", () => {
        currentPage = 1;
        applyFiltersAndDisplay();
    });

    allReposFilterInputs.forEach(input => {
        input.addEventListener("input", () => {
            currentPage = 1;
            applyFiltersAndDisplay();
        });
    });

    clearFiltersBtn.addEventListener("click", () => {
        generalSearchInput.value = "";
        languageFilter.value = "";
        licenseFilter.value = "";
        allReposFilterInputs.forEach(input => input.value = "");
        currentSortColumn = null;
        currentSortDirection = 'asc';
        allReposTableHeaders.forEach(th => {
            th.classList.remove("asc", "desc");
            const icon = th.querySelector(".sort-icon");
            if (icon) icon.className = "fas fa-sort sort-icon";
        });
        currentPage = 1;
        applyFiltersAndDisplay();
    });

    allReposTableHeaders.forEach(header => {
        header.addEventListener("click", () => {
            const column = header.dataset.sortKey;
            
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
