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