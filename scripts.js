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
    const filteredReposCount = document.getElementById('filteredReposCount');

    // Elementos para Top Linguagens
    const topLanguagesTbody = document.getElementById('topLanguagesTbody');
    const noTopLanguagesMessage = document.getElementById('noTopLanguagesMessage');

    // Elementos para Top Repositórios
    const topReposTbody = document.getElementById('topReposTbody');
    const noTopReposMessage = document.getElementById('noTopReposMessage');

    // Elementos para Tabela de Todos os Repositórios
    const allReposTable = document.getElementById('allReposTable');
    const allReposTbody = document.getElementById('allReposTbody');
    const allReposTableHeaders = document.querySelectorAll('#allReposTable thead tr:first-child th');
    const allReposFilterInputs = document.querySelectorAll('#allReposTable #filterRow .filter-input');

    // Elementos para Tabela de Clusters
    const clustersTbody = document.getElementById('clustersTbody');
    const noClustersMessage = document.getElementById('noClustersMessage');

    // === Elementos de Paginação ADICIONADOS ===
    const prevPageBtn = document.getElementById('prevPageBtn');
    const nextPageBtn = document.getElementById('nextPageBtn');
    const pageInfoSpan = document.getElementById('pageInfo');


    // === Variáveis de Dados ===
    let allInstitutionsData = []; // Dados brutos das instituições (do JSON)
    let clusterDescriptions = []; // Descrições dos clusters (do JSON)
    let allFlattenedRepos = []; // Todos os repositórios, achatados em uma lista
    let calculatedTop5Languages = []; // Para armazenar as top 5 linguagens calculadas

    let availableLanguages = new Set();
    let availableLicenses = new Set();

    // Variáveis de estado para ordenação da tabela principal
    let currentSortColumn = null;
    let currentSortDirection = 'asc'; // 'asc' ou 'desc'

    // Objeto para armazenar os valores dos filtros de coluna
    let columnFilters = {};

    // === Variáveis de Paginação ADICIONADAS ===
    let currentPage = 1;
    const itemsPerPage = 50;
    let currentFilteredAndSortedRepos = []; // Armazena os repositórios após filtros e ordenação, antes da paginação


    // === Lógica de Carregamento de Dados ===
    async function fetchAndProcessData() {
        try {
            const response = await fetch('repositorios_federais_com_clusters_visualizado.json');
            if (!response.ok) {
                // Atualiza todas as mensagens de erro se o arquivo não puder ser carregado
                allReposTbody.innerHTML = `<tr><td colspan="8" class="error-message">Erro ao carregar os dados: Arquivo 'repositorios_federais_com_clusters_visualizado.json' não encontrado ou inacessível. Verifique o caminho e nome do arquivo.</td></tr>`;
                topReposTbody.innerHTML = `<tr><td colspan="5" class="error-message">Erro ao carregar top repositórios.</td></tr>`;
                clustersTbody.innerHTML = `<tr><td colspan="2" class="error-message">Erro ao carregar clusters.</td></tr>`;
                topLanguagesTbody.innerHTML = `<tr><td colspan="3" class="error-message">Erro ao carregar top linguagens.</td></tr>`;
                throw new Error(`Erro ao carregar o JSON: ${response.statusText} (Status: ${response.status})`);
            }
            const jsonData = await response.json();

            allInstitutionsData = jsonData.institutions_data || [];
            clusterDescriptions = jsonData.cluster_descriptions || [];

            const tempLanguageCounts = {}; // Objeto temporário para contar linguagens

            allInstitutionsData.forEach(institution => {
                const institutionName = institution['Nome Completo'];
                const institutionSigla = institution.Sigla;
                institution.Repositorios.forEach(repo => {
                    repo.Instituicao = institutionName;
                    repo.SiglaInstituicao = institutionSigla;
                    
                    // Garante que Cluster_ID existe, mesmo que seja 'N/A'
                    if (repo['Cluster_ID'] === undefined || repo['Cluster_ID'] === null) {
                        repo['Cluster_ID'] = 'N/A';
                    }
                    allFlattenedRepos.push(repo);

                    // Coleta linguagens disponíveis para o filtro
                    if (repo['Linguagem Principal'] && repo['Linguagem Principal'] !== 'N/A' && repo['Linguagem Principal'] !== 'null') {
                        availableLanguages.add(repo['Linguagem Principal']);
                        // Conta a linguagem para o ranking top 5
                        const lang = repo['Linguagem Principal'];
                        tempLanguageCounts[lang] = (tempLanguageCounts[lang] || 0) + 1;
                    }
                    // Coleta licenças disponíveis para o filtro
                    if (repo.Licenca && repo.Licenca !== 'N/A' && repo.Licenca !== 'null') {
                        availableLicenses.add(repo.Licenca);
                    }
                });
            });

            // Calcula as top 5 linguagens com base na contagem
            calculatedTop5Languages = Object.entries(tempLanguageCounts)
                .map(([language, count]) => ({ language, count }))
                .sort((a, b) => b.count - a.count) // Ordena em ordem decrescente de contagem
                .slice(0, 5); // Pega apenas as 5 primeiras

            populateFilter(languageFilter, Array.from(availableLanguages).sort());
            populateFilter(licenseFilter, Array.from(availableLicenses).sort());
            
            populateClustersTable(); // Popula a tabela de clusters
            displayTop5LanguagesTable(calculatedTop5Languages); // Passa os dados calculados

            // Após carregar os dados, aplica filtros e exibe a primeira página
            applyFiltersAndDisplay(true); // Chamada inicial reseta a página para 1

        } catch (error) {
            console.error("Erro ao carregar ou processar os dados:", error);
        }
    }

    // === Funções Auxiliares ===
    function populateFilter(selectElement, optionsArray) {
        selectElement.innerHTML = '<option value="">Todas</option>';
        optionsArray.forEach(optionText => {
            const option = document.createElement('option');
            option.value = optionText;
            option.textContent = optionText;
            selectElement.appendChild(option);
        });
    }

    function getMostCommon(list) {
        if (list.length === 0) return 'N/A';
        const counts = {};
        let maxCount = 0;
        let mostCommonItem = 'N/A';

        for (const item of list) {
            counts[item] = (counts[item] || 0) + 1;
            if (counts[item] > maxCount) {
                maxCount = counts[item];
                mostCommonItem = item;
            }
        }
        return mostCommonItem;
    }

    // === Funções de Atualização de UI ===
    function updateGlobalStatistics(reposToConsider) {
        let totalRepos = reposToConsider.length;
        const allLanguages = reposToConsider.map(repo => repo['Linguagem Principal']).filter(l => l && l !== 'N/A' && l !== 'null');
        const allLicenses = reposToConsider.map(repo => repo.Licenca).filter(l => l && l !== 'N/A' && l !== 'null');

        totalReposGlobal.textContent = allFlattenedRepos.length; // Total geral sem filtros
        filteredReposCount.textContent = totalRepos; // Total de repos filtrados
        mostUsedLanguageGlobal.textContent = getMostCommon(allLanguages);
        mostUsedLicenseGlobal.textContent = getMostCommon(allLicenses);
    }

    function displayTop5LanguagesTable(data) {
        topLanguagesTbody.innerHTML = ''; // Limpa o conteúdo atual da tabela
        noTopLanguagesMessage.classList.add('hidden'); // Oculta a mensagem de "nenhuma linguagem"

        if (!data || data.length === 0) {
            noTopLanguagesMessage.classList.remove('hidden'); // Exibe a mensagem se não houver dados
            return;
        }

        data.forEach((item, index) => {
            const row = topLanguagesTbody.insertRow();
            row.insertCell().textContent = index + 1; // Posição
            row.insertCell().textContent = item.language; // Linguagem
            row.insertCell().textContent = item.count; // Número de Repositórios
        });
    }


    function displayTop10ActiveRepos(reposData) {
        topReposTbody.innerHTML = '';
        noTopReposMessage.classList.add('hidden');

        // Note: top 10 ativos ainda usa allFlattenedRepos, não os filtrados da tabela principal.
        // Se quiser que seja os 10 mais ativos *dentre os filtrados*, mude reposData para currentFilteredAndSortedRepos
        const activeRepos = reposData.filter(repo => repo['Ultima Atualizacao'])
                                     .sort((a, b) => new Date(b['Ultima Atualizacao']).getTime() - new Date(a['Ultima Atualizacao']).getTime());

        const top10Repos = activeRepos.slice(0, 10);

        if (top10Repos.length === 0) {
            noTopReposMessage.classList.remove('hidden');
            return;
        }

        top10Repos.forEach(repo => {
            const row = topReposTbody.insertRow();
            row.insertCell().innerHTML = `<a href="${repo['Link de Acesso']}" target="_blank">${repo['Nome do Repositório']}</a>`;
            row.insertCell().textContent = repo.SiglaInstituicao || 'N/A';
            row.insertCell().textContent = repo['Linguagem Principal'] || 'N/A';
            row.insertCell().textContent = `${repo.Estrelas} ⭐`;
            row.insertCell().textContent = repo['Ultima Atualizacao'] ? new Date(repo['Ultima Atualizacao']).toLocaleDateString('pt-BR') : 'N/A';
        });
    }

    // MODIFICADA para receber APENAS os repositórios da página atual
    function displayAllReposTable(reposOnCurrentPage) {
        allReposTbody.innerHTML = '';
        if (reposOnCurrentPage.length === 0) {
            const row = allReposTbody.insertRow();
            const cell = row.insertCell();
            const numCols = document.querySelectorAll('#allReposTable thead th').length;
            cell.colSpan = numCols; 
            cell.textContent = 'Nenhum repositório encontrado com os filtros e paginação aplicados.';
            cell.style.textAlign = 'center';
            cell.style.fontStyle = 'italic';
            cell.classList.add('no-results-message');
            return;
        }

        reposOnCurrentPage.forEach(repo => {
            const row = allReposTbody.insertRow();
            
            const repoNameCell = row.insertCell();
            const link = document.createElement('a');
            link.href = repo['Link de Acesso'];
            link.target = '_blank';
            link.textContent = repo['Nome do Repositório'] || 'N/A';
            repoNameCell.appendChild(link);

            row.insertCell().textContent = repo.SiglaInstituicao || repo.Instituicao || 'N/A';
            row.insertCell().textContent = repo.Descricao || 'N/A';
            row.insertCell().textContent = repo['Linguagem Principal'] || 'N/A';
            row.insertCell().textContent = repo.Estrelas !== undefined ? repo.Estrelas : 'N/A';
            row.insertCell().textContent = repo.Licenca || 'N/A';
            row.insertCell().textContent = repo['Ultima Atualizacao'] ? new Date(repo['Ultima Atualizacao']).toLocaleDateString('pt-BR') : 'N/A';
            row.insertCell().textContent = repo['Cluster_ID'] !== undefined ? repo['Cluster_ID'] : 'N/A';
        });
    }

    function populateClustersTable() {
        clustersTbody.innerHTML = '';
        noClustersMessage.classList.add('hidden');

        if (clusterDescriptions.length === 0) {
            noClustersMessage.classList.remove('hidden');
            clustersTbody.innerHTML = '<tr><td colspan="2" class="no-results-message">Nenhuma descrição de cluster encontrada nos dados JSON.</td></tr>';
            return;
        }

        const sortedClusterDescriptions = [...clusterDescriptions].sort((a, b) => a.id - b.id);

        sortedClusterDescriptions.forEach(cluster => {
            const row = clustersTbody.insertRow();
            row.insertCell().textContent = cluster.id;
            row.insertCell().textContent = cluster.description || 'N/A';
        });
    }

    // === Nova Função para Atualizar os Controles de Paginação ===
    function updatePaginationControls() {
        const totalItems = currentFilteredAndSortedRepos.length;
        const totalPages = Math.ceil(totalItems / itemsPerPage);

        pageInfoSpan.textContent = `Página ${currentPage} de ${totalPages || 1}`;
        prevPageBtn.disabled = (currentPage === 1);
        nextPageBtn.disabled = (currentPage === totalPages || totalPages === 0);
    }


    // === Lógica Unificada de Filtragem e Ordenação ===
    function applyFiltersAndDisplay(resetPage = false) { // Adicionado parâmetro resetPage
        let dataToProcess = [...allFlattenedRepos]; // Começa com uma cópia dos dados originais

        if (resetPage) { // Se resetPage for true, volta para a primeira página
            currentPage = 1;
        }

        // --- 1. Aplicar Filtros Globais (Busca Geral, Linguagem, Licença) ---
        const generalSearchTerm = generalSearchInput.value.toLowerCase().trim();
        const selectedLanguage = languageFilter.value;
        const selectedLicense = licenseFilter.value;

        dataToProcess = dataToProcess.filter(repo => {
            const repoName = (repo['Nome do Repositório'] || '').toLowerCase();
            const repoDesc = (repo.Descricao || '').toLowerCase();
            const repoInst = (repo.Instituicao || '').toLowerCase();
            const repoSiglaInst = (repo.SiglaInstituicao || '').toLowerCase();
            const repoLang = (repo['Linguagem Principal'] || '').toLowerCase();
            const repoLicense = (repo.Licenca || '').toLowerCase();

            // Filtro de busca geral (busca em várias colunas)
            const matchesGeneralSearch = !generalSearchTerm || 
                                         repoName.includes(generalSearchTerm) ||
                                         repoDesc.includes(generalSearchTerm) ||
                                         repoInst.includes(generalSearchTerm) ||
                                         repoSiglaInst.includes(generalSearchTerm) ||
                                         repoLang.includes(generalSearchTerm) ||
                                         repoLicense.includes(generalSearchTerm);

            // Filtro por linguagem
            const matchesLanguage = !selectedLanguage || repoLang === selectedLanguage.toLowerCase();

            // Filtro por licença
            const matchesLicense = !selectedLicense || repoLicense === selectedLicense.toLowerCase();

            return matchesGeneralSearch && matchesLanguage && matchesLicense;
        });

        // --- 2. Aplicar Filtros por Coluna (novos inputs) ---
        // Atualiza o objeto columnFilters com os valores atuais dos inputs de filtro por coluna
        allReposFilterInputs.forEach(input => {
            const filterKey = input.dataset.filterKey;
            columnFilters[filterKey] = input.value.toLowerCase().trim();
        });

        dataToProcess = dataToProcess.filter(repo => {
            for (const key in columnFilters) {
                const filterValue = columnFilters[key];
                if (filterValue) { // Se há um valor no filtro desta coluna
                    let repoValue = repo[key];

                    // Tratamento especial para datas no filtro de coluna (se for filtrar pela string formatada)
                    if (key === 'Ultima Atualizacao' && repoValue) {
                        repoValue = new Date(repoValue).toLocaleDateString('pt-BR'); // Formata para comparar com a string do input
                    } else if (repoValue === null || repoValue === undefined) {
                        repoValue = ''; // Trata null/undefined para comparação
                    } else {
                        repoValue = String(repoValue); // Converte para string
                    }
                    
                    // Verifica se o valor da coluna COMEÇA COM o valor do filtro
                    if (!repoValue.toLowerCase().startsWith(filterValue)) { 
                        return false; // Se não corresponder a este filtro de coluna, a linha não é incluída
                    }
                }
            }
            return true; // A linha corresponde a todos os filtros de coluna
        });

        // --- 3. Aplicar Ordenação ---
        if (currentSortColumn) {
            dataToProcess.sort((a, b) => {
                let valA = a[currentSortColumn];
                let valB = b[currentSortColumn];

                // Tratamento de valores nulos/indefinidos para ordenação
                if (valA === null || valA === undefined || valA === 'N/A' || valA === 'null') valA = '';
                if (valB === null || valB === undefined || valB === 'N/A' || valB === 'null') valB = '';

                // Conversão de tipos para comparação adequada
                if (currentSortColumn === 'Estrelas' || currentSortColumn === 'Cluster_ID') {
                    valA = parseInt(valA) || 0; // Trata N/A/null como 0 para estrelas/ID
                    valB = parseInt(valB) || 0;
                } else if (currentSortColumn === 'Ultima Atualizacao') {
                    valA = valA ? new Date(valA).getTime() : 0; // Trata datas inválidas/nulas como 0
                    valB = valB ? new Date(valB).getTime() : 0;
                } else { // Para strings (Nome, Instituicao, Descricao, Linguagem, Licenca)
                    valA = String(valA).toLowerCase();
                    valB = String(valB).toLowerCase();
                }

                if (valA < valB) return currentSortDirection === 'asc' ? -1 : 1;
                if (valA > valB) return currentSortDirection === 'asc' ? 1 : -1;
                return 0;
            });
        }

        // === NOVO: Salva os dados filtrados e ordenados antes da paginação ===
        currentFilteredAndSortedRepos = dataToProcess;

        // === REMOVIDO: Antigo reset de página condicional. Agora o reset é feito via parâmetro 'resetPage'.
        // const totalPagesAfterFilter = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
        // if (currentPage > totalPagesAfterFilter && totalPagesAfterFilter > 0) {
        //     currentPage = totalPagesAfterFilter;
        // } else if (totalPagesAfterFilter === 0) {
        //     currentPage = 1; // Se não houver resultados, volta para a página 1
        // }
        
        // --- 4. Aplicar Paginação ---
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const reposToDisplay = currentFilteredAndSortedRepos.slice(startIndex, endIndex);

        // --- 5. Atualizar Estatísticas e Renderizar Tabelas ---
        updateGlobalStatistics(currentFilteredAndSortedRepos); // Estatísticas com base nos dados filtrados (total antes da paginação)
        displayTop10ActiveRepos(allFlattenedRepos); // Top 10 ainda é global, usa todos os dados
        displayAllReposTable(reposToDisplay); // Renderiza a tabela principal APENAS com a página atual
        updatePaginationControls(); // Atualiza os botões e info da paginação
    }

    // === Event Listeners ===
    generalSearchInput.addEventListener('input', () => applyFiltersAndDisplay(true)); // Passa true para resetar a página
    languageFilter.addEventListener('change', () => applyFiltersAndDisplay(true)); // Passa true para resetar a página
    licenseFilter.addEventListener('change', () => applyFiltersAndDisplay(true)); // Passa true para resetar a página
    
    // Event listeners para os novos inputs de filtro por coluna
    allReposFilterInputs.forEach(input => {
        input.addEventListener('input', () => applyFiltersAndDisplay(true)); // Passa true para resetar a página
    });

    clearFiltersBtn.addEventListener('click', () => {
        // Limpa filtros globais
        generalSearchInput.value = '';
        languageFilter.value = '';
        licenseFilter.value = '';
        
        // Limpa os inputs de filtro por coluna
        allReposFilterInputs.forEach(input => {
            input.value = '';
        });
        columnFilters = {}; // Reseta o objeto de filtros de coluna

        // Reseta a ordenação para o estado inicial
        currentSortColumn = null;
        currentSortDirection = 'asc';
        allReposTableHeaders.forEach(th => {
            th.classList.remove('asc', 'desc'); // Remove classes de ordenação
            const icon = th.querySelector('i.fas');
            // Apenas redefine o ícone se ele existir e for um cabeçalho que pode ser ordenado
            if (icon && th.dataset.sortKey) {
                icon.className = 'fas fa-sort'; // Volta para a seta neutra
            }
        });

        // Reseta a paginação para a primeira página
        currentPage = 1; // Já está sendo feito explicitamente aqui, mas a chamada abaixo também fará

        applyFiltersAndDisplay(true); // Re-aplica filtros e re-renderiza, reseta a página
    });

    // Event listeners para ordenação dos cabeçalhos da tabela principal
    allReposTableHeaders.forEach(header => {
        // Verifica se o cabeçalho possui o atributo data-sort-key antes de adicionar o listener
        if (header.dataset.sortKey) {
            header.addEventListener('click', () => {
                const column = header.dataset.sortKey; // Pega a chave da coluna para ordenar
                
                // Remove classes de ordenação e redefine ícones de todos os cabeçalhos ordenáveis
                allReposTableHeaders.forEach(th => {
                    if (th.dataset.sortKey) { // Apenas para cabeçalhos que podem ser ordenados
                        th.classList.remove('asc', 'desc');
                        const icon = th.querySelector('i.fas');
                        if (icon && th !== header) { 
                            icon.className = 'fas fa-sort';
                        }
                    }
                });

                // Alterna a direção da ordenação ou define para 'asc' se for uma nova coluna
                if (currentSortColumn === column) {
                    currentSortDirection = (currentSortDirection === 'asc') ? 'desc' : 'asc';
                } else {
                    currentSortColumn = column;
                    currentSortDirection = 'asc'; // Padrão é asc na primeira vez que clica
                }

                // Adiciona a classe de ordenação e atualiza o ícone do cabeçalho clicado
                header.classList.add(currentSortDirection);
                const currentIcon = header.querySelector('i.fas');
                if (currentIcon) {
                    currentIcon.className = `fas fa-sort-${currentSortDirection === 'asc' ? 'up' : 'down'}`;
                }

                // Ao mudar a ordenação, reseta para a primeira página
                // currentPage = 1; // Isso será tratado pelo applyFiltersAndDisplay(true)

                applyFiltersAndDisplay(true); // Chama a função que filtra e ordena, reseta a página
            });
        }
    });

    // === Event Listeners para Paginação ADICIONADOS ===
    prevPageBtn.addEventListener('click', () => {
        if (currentPage > 1) {
            currentPage--;
            applyFiltersAndDisplay(false); // NÃO reseta a página ao navegar
        }
    });

    nextPageBtn.addEventListener('click', () => {
        const totalPages = Math.ceil(currentFilteredAndSortedRepos.length / itemsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            applyFiltersAndDisplay(false); // NÃO reseta a página ao navegar
        }
    });


    // === Inicia o Carregamento dos Dados ===
    fetchAndProcessData();
});