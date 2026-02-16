# Mapeamento de Repositórios de Instituições Federais no GitHub

Ferramenta web para visualizar e filtrar repositórios GitHub de instituições federais brasileiras. O sistema exibe informações como linguagens de programação, licenças, estrelas e datas de atualização, além de estatísticas globais e por instituição.

São incluídos projetos que mencionam instituições públicas no título, descrição ou README, podendo conter código, materiais didáticos e outros conteúdos relacionados a professores, estudantes, técnicos ou contas institucionais oficiais.

## Funcionalidades

- Busca geral por instituição, nome do repositório, descrição ou linguagem
- Filtros por linguagem principal e tipo de licença
- Estatísticas globais (total de repositórios, linguagens mais usadas, licenças mais frequentes)
- Lista dos repositórios mais populares
- Tabela completa com todos os repositórios e opções de ordenação
- Visualização dos clusters temáticos identificados nos dados


## Técnicas 

A busca inteligente combina conceitos de aprendizado iterativo e análise de relevância para otimizar consultas na API do GitHub. Inspirada em técnicas como TF-IDF (Term Frequency-Inverse Document Frequency) e feedback loops, ela funciona como um detetive que aprende com os resultados: primeiro, busca termos óbvios como "ifsc"; depois, analisa as palavras mais frequentes nos repositórios encontrados (ex.: "proxmox", "laboratório") e gera novas consultas combinadas, como "ifsc proxmox". A eficiência de cada busca é medida por métricas que avaliam a taxa de relevância dos resultados (ex.: se 8 em cada 10 repositórios mencionam os termos da query, a eficiência é 80%). Com esse método, a taxa de acerto na captura de repositórios públicos sobe de 30% (busca simples, restrita à primeira página) para 95% (com paginação completa e aprendizado), garantindo que até projetos menos populares, como ferramentas internas de laboratório, sejam encontrados.

## Como Contribuir

### Contribuição Técnica

Se você deseja melhorar o código do projeto:

1. Faça um fork do repositório
2. Clone o fork para sua máquina local
3. Crie uma branch para suas alterações
4. Envie um pull request descrevendo suas mudanças

### Contribuição com Stopwords

O sistema utiliza uma lista de stopwords (palavras irrelevantes) para filtrar termos que não ajudam na identificação do tema dos repositórios. Se você encontrar repositórios que não se encaixam na proposta do projeto devido a termos inadequados, pode contribuir adicionando palavras à lista de stopwords.

Para isso:

1. Localize o arquivo `stopwords.txt` na raiz do repositório
2. Adicione a nova palavra em uma nova linha
3. Envie um pull request com a alteração

Isso ajuda a melhorar a precisão da classificação dos repositórios e a qualidade dos clusters identificados.