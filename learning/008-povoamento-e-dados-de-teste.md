# Apostila 08: Povoamento Automatizado (Seed Data) e Demonstração em Nuvem

Bem-vinda à Oitava Apostila do **AtlasERP por NandaTech**!

Nesta aula, aprendemos sobre **Povoamento Automatizado de Dados (Database Seeding)** e como preparar uma aplicação para demonstrações profissionais de alta performance em **Ambientes de Nuvem (Cloud Computing)**.

---

## 1. Por que o Povoamento de Dados (Seed Data) é Fundamental?

Quando apresentamos um sistema ou testamos a infraestrutura de um servidor em nuvem (AWS, Azure, GCP, DigitalOcean), utilizar um banco de dados vazio ("com 0 registros") prejudica a experiência por 3 motivos principais:
1. **Dificuldade de Validação Visual:** O usuário não consegue enxergar a riqueza das telas, listas e tabelas.
2. **Falta de Carga para Testes de Performance:** O servidor em nuvem aparenta funcionar rápido porque processa 0 dados. Para provar que o ambiente de nuvem é robusto, o banco de dados precisa conter **massa de dados representativa** (dezenas de produtos, vendas, lançamentos financeiros e rotas).
3. **Simulação de Negócio Real:** Demonstra como o ERP lida com uma empresa madura em operação contínua.

---

## 2. A Estrutura do Script `seed_db.py`

No arquivo [seed_db.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/seed_db.py), construímos um seeder idempotente (que pode ser executado várias vezes sem duplicar dados acidentalmente):

### Módulos Povoados com Dados Realistas:
- **20 Produtos em Estoque:** Notebooks i7, Monitores UltraWide 27", Cadeiras Ergonômicas, Nobreaks, Impressoras e Cabos com controle automático de estoque (Normal, Baixo e Esgotado).
- **12 Clientes & 8 Fornecedores:** Pessoas Jurídicas e Físicas com CNPJ e CPF formatados.
- **Equipe de 10 Colaboradores na Folha:** Gerente Geral, Desenvolvedor Senior, Analistas, Motoristas e Encarregados de Estoque com cálculo de encargos e benefícios.
- **DRE & Lançamentos Financeiros:** Aluguel de sede, energia elétrica, internet dedicada fibra, faturamento de vendas e folha salarial.
- **15 Vendas Comercial & 8 Compras de Suprimentos:** Vendas confirmadas com baixa automática de estoque.
- **11 Notas Fiscais Eletrônicas (NF-e):** Chaves de acesso de 44 dígitos autorizadas com código `100 - Autorizado o uso da NF-e` no simulador SEFAZ.
- **6 Veículos de Frota & 6 Motoristas:** Vans Sprinter, Caminhões VUC VW, Fiorinos e Atego com placas Mercosul (`ABC-1D23`), quilometragens reais e manutenções mecânicas.
- **Rotas & Retorno de Entregas:** Logística de entregas metropolitanas e tratamento de logística reversa.

---

## 3. Como Re-popular o Banco de Dados

Caso deseje resetar e repovoar a base de dados a qualquer momento no seu terminal:

```powershell
python seed_db.py
```

---

## 📝 Exercício Didático de Fixação

1. Abra o terminal e execute `python seed_db.py`.
2. Acesse `http://127.0.0.1:5000/dashboard` e veja a riqueza de números, faturamento, tarefas pendentes do dia e gráficos!
3. Navegue por **Produtos**, **Vendas**, **Financeiro**, **Folha de Pagamento** e **Frota** para ver a empresa funcionando com carga total!
