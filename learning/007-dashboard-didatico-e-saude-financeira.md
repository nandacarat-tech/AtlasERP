# Apostila 07: Dashboard Didático, Saúde Financeira e Central de Ação do Empreendedor

Bem-vinda à Sétima Apostila do **AtlasERP por NandaTech**!

Nesta aula, estudamos um dos conceitos mais importantes de **Interface Humano-Computador (IHC)** e **Experiência do Usuário (UX)** aplicada a sistemas de gestão: a criação de um **Dashboard Didático, Acessível e Autoexplicativo** voltado para pequenos empresários.

---

## 1. O Desafio da Pequena Empresa (O Empreendedor Centralizador)

Em micro e pequenas empresas (MEIs, comércios de bairro, pequenos distribuidores), é comum existir **apenas uma pessoa cuidando de tudo**:
- Ela atende os clientes e faz as vendas.
- Controla o estoque físico nas prateleiras.
- Cuida das contas a pagar, boletos e salários dos colaboradores.
- Solicita notas fiscais e organiza as entregas da frota.

Se o ERP apresentar telas poluídas com gráficos complexos, termos contábeis avançados e códigos incompreensíveis, o empresário perde tempo e comete erros.

---

## 2. A Solução do AtlasERP: As 4 Seções Didáticas

No arquivo [app/templates/index.html](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/templates/index.html), estruturamos o painel dividindo as informações em 4 blocos de fácil leitura:

### A) Saúde Financeira do Negócio (Dinheiro Entrando x Dinheiro Saindo)
1. **Dinheiro das Vendas (Entrou):** Faturamento com vendas confirmadas.
2. **Contas & Custos (Saiu / A Pagar):** Despesas e custos operacionais.
3. **Resultado do Negócio (Sobrou Dinheiro?):**
   - 🟢 *Verde:* O negócio está no azul (com lucro).
   - 🔴 *Vermelho:* Alerta de que as despesas superam as vendas.
4. **Dinheiro Guardado em Produtos:** Valor financeiro em mercadorias paradas no estoque prontas para venda.

### B) Central de Tarefas ("O que precisa da sua atenção hoje?")
Reúne em um único lugar todos os alertas que exigem ação imediata:
- 💳 **Contas a Pagar a Vencer / Atrasadas** (Financeiro)
- 💰 **Contas a Receber de Clientes** (Financeiro)
- 👥 **Salários e Folha de Pagamento** (Financeiro)
- ⚠️ **Produtos Acabando ou Esgotados** (Estoque)
- 📜 **Notas Fiscais para Emitir na SEFAZ** (Fiscal)
- 🚚 **Entregas que Voltaram do Caminhão** (Frota)

### C) Atalhos Rápidos com Um Clique
Botões diretos para executar as operações mais rotineiras (*Nova Venda*, *Entrada em Compras*, *Lançar Conta a Pagar*, *Planejar Rotas*).

### D) Nível de Estoque Visual
Substituímos tabelas brutas por barras de progresso visualmente coloridas:
- 🟢 **Estoque Ok** (Quantidade segura)
- 🟡 **Estoque Baixo** (Perto da cota mínima)
- 🔴 **Esgotado** (Zerado)

---

## 📝 Exercício Didático de Fixação

1. Acesse o Dashboard em `http://127.0.0.1:5000/dashboard`.
2. Observe o indicador de **Resultado do Negócio**: se os custos superarem as vendas, ele acionará o alerta em vermelho.
3. Observe a **Central de Tarefas**: veja quantas contas a pagar estão pendentes e clique no botão **Ver Contas a Pagar** para ir direto ao módulo financeiro!
