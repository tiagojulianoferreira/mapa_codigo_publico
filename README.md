# Mapeamento de Repositórios de Instituições Federais no GitHub

Ferramenta simples baseada em web para visualizar e filtrar repositórios GitHub de instituições federais brasileiras. Ele exibe informações como linguagens de programação, licenças, estrelas e datas de atualização, além de fornecer estatísticas globais e por instituição.

Contruido com auxílio do Gemini.

## Como Usar

1.  Certifique-se de ter um arquivo `repositorios_federais.json` no mesmo diretório que `index.html` e `style.css`. Este arquivo JSON deve conter os dados dos repositórios.
    * (Se você gerou o `repositorios_federais.json` usando um script Python, execute-o primeiro.)
2.  Abra o arquivo `index.html` em seu navegador web.

## Funcionalidades

* Filtragem por termo de busca geral (instituição, repositório, descrição, linguagem).
* Filtragem por linguagem principal.
* Filtragem por tipo de licença.
* Estatísticas globais de repositórios, linguagens e licenças.
* Tabela dos 5 repositórios mais ativos globalmente.
* Estatísticas por instituição na tabela principal.
* Ordenação da lista de repositórios por data de última atualização (clicando no cabeçalho da coluna).

## Como Contribuir

Sua contribuição é bem-vinda! Se você quiser melhorar este projeto:

1.  **Faça um Fork** deste repositório.
2.  **Clone o Fork** para sua máquina local.
3.  **Crie uma Nova Branch** para suas alterações.
4.  **Faça Suas Alterações** no código (HTML, CSS, JavaScript ou a lógica de geração do JSON).
5.  **Envie Suas Alterações** para sua branch no GitHub.
6.  **Abra um Pull Request** detalhando suas mudanças.

Agradecemos o seu interesse!