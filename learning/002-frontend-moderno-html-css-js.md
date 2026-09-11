# Apostila 02: Guia Didático de HTML5, CSS3 e JavaScript

Bem-vinda à Segunda Apostila do **AtlasERP por NandaTech**!

Se você já conhece os fundamentos do Python, compreender o **Front-end** (HTML, CSS e JavaScript) se torna muito fácil quando entendemos o papel de cada tecnologia no navegador.

---

## 1. As 3 Camadas da Web (HTML + CSS + JS)

Pense na construção de um site como a construção de um veículo:
1. **HTML (Estrutura / Esqueleto):** Define quais elementos existem na página (títulos, tabelas, botões, formulários).
2. **CSS (Estilo / Pintura e Acabamento):** Define as cores, fontes, espaçamentos, bordas e responsividade.
3. **JavaScript (Motor / Comportamento):** Traz vida à página, fazendo requisições ao servidor em segundo plano e atualizando dados na tela sem recarregar a página.

---

## 2. HTML5: Entendendo as Tags Básicas

O HTML funciona por meio de **Tags** abertas e fechadas.

### Estrutura Principal do AtlasERP:
- `<header>`: O topo da página onde fica o logotipo **AtlasERP por NandaTech**.
- `<nav>`: A barra de navegação com os links do menu.
- `<main>`: Onde o conteúdo principal de cada tela é exibido.
- `<table>`, `<thead>`, `<tbody>`, `<tr>`, `<td>`: Utilizados para exibir listagens organizadas de veículos, produtos e motoristas.
- `<button>`: Botões de ação para abrir formulários ou salvar cadastros.

---

## 3. CSS3: O Design System Moderno SaaS

No arquivo [static/style.css](file:///C:/Users/Fernanda/Projetos/AtlasERP/static/style.css), criamos o novo visual estilo SaaS Dark Slate do AtlasERP.

### Conceitos Chave de CSS:
1. **Variáveis CSS (`:root`):** Permitem guardar cores e reaproveitá-las no projeto:
   ```css
   :root {
       --bg-main: #0f172a;    /* Slate escuro moderno */
       --primary: #3b82f6;    /* Azul vibrante */
       --accent-cyan: #06b6d4;/* Ciano brilhante NandaTech */
   }
   ```
2. **Flexbox (`display: flex;`):** Alinha elementos em linha ou coluna de forma automática (usado na barra de navegação e nos botões).
3. **CSS Grid (`display: grid;`):** Cria grades perfeitas para os Cards Estatísticos do Dashboard.
4. **Hover & Transições:** Criam efeitos visuais quando o usuário passa o mouse sobre botões e cards:
   ```css
   button:hover {
       background-color: #2563eb;
       transform: translateY(-1px);
   }
   ```

---

## 4. JavaScript: Conectando a Tela ao Python via API `fetch()`

Quando o usuário acessa o Painel da Frota ([app/templates/fleet.html](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/templates/fleet.html)), o navegador executa um código em JavaScript que faz uma requisição em segundo plano para o servidor Flask.

### Exemplo Didático do `fetch()`:
```javascript
// O navegador pede os dados da API Flask
fetch('/api/fleet/vehicles/summary')
    .then(response => response.json()) // Transforma a resposta em dados JSON
    .then(data => {
        // Atualiza o número na tela diretamente no elemento HTML!
        document.getElementById('available-vehicles-count').textContent = data.available;
    });
```

Esse ciclo é fantástico: o Python/SQLAlchemy busca os dados no banco, responde em JSON, e o JavaScript insere os dados na tela instantaneamente!

---

## 📝 Dica Didática para Navegação
Sempre que quiser alterar a aparência de algum elemento, o arquivo principal é o [static/style.css](file:///C:/Users/Fernanda/Projetos/AtlasERP/static/style.css). Se quiser mudar os botões ou estruturas das páginas, altere os arquivos dentro da pasta `app/templates/`.
