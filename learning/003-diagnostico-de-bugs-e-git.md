# Apostila 03: Diagnóstico de Bugs, SQLAlchemy e Git para GitHub

Bem-vinda à Terceira Apostila do **AtlasERP por NandaTech**!

Nesta aula, vamos analisar o caso real que ocorreu durante o desenvolvimento do AtlasERP e aprender como gerenciar seu repositório no **Git** e no **GitHub** como uma desenvolvedora profissional.

---

## 1. O Diagnóstico do Bug `InvalidRequestError` no SQLAlchemy

Durante a criação do Módulo de Frota, ocorreu um erro no terminal:
`sqlalchemy.exc.InvalidRequestError: Multiple classes found for path "FleetVehicle" in the registry of this declarative base.`

### O que causou isso?
Ao colar código no arquivo [app/models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/models.py), as classes `FleetVehicle`, `Driver` e `FleetMaintenance` acabaram sendo declaradas **duas vezes no mesmo arquivo**:
1. A primeira declaração usava IDs numéricos (`id = db.Column(db.Integer)`).
2. A segunda declaração usava IDs UUID (`id = db.Column(db.String)`).

Quando o Flask tentava iniciar o servidor, o SQLAlchemy tentava registrar a mesma classe duas vezes no seu dicionário interno e travava.

### Como resolvemos?
- Unificamos o arquivo [app/models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/models.py), mantendo apenas **uma única classe de cada modelo** com IDs numéricos consistentes.
- Em seguida, executamos `flask db migrate` e `flask db upgrade` para atualizar o banco de dados SQLite.
- Resultado: **100% dos 125 testes do `pytest` voltaram a passar com sucesso!**

---

## 2. Passo a Passo do Git pelo PowerShell

O **Git** é o sistema de controle de versão que registra o histórico de alterações do seu projeto. O **GitHub** é a plataforma na nuvem onde você publica seu código para exibir no seu portfólio.

### Comandos Essenciais que Você Deve Conhecer:

1. **Verificar o estado dos arquivos modificados:**
   ```powershell
   git status
   ```
   *Exibe em vermelho os arquivos alterados e pendentes de salvar no histórico.*

2. **Adicionar arquivos à área de preparação (Staging):**
   ```powershell
   git add .
   ```
   *O ponto `.` significa "adicionar todas as alterações da pasta atual".*

3. **Criar um Commit (Registro de versão):**
   ```powershell
   git commit -m "fix(models): resolve duplicidade no sqlalchemy e atualiza ui por nandatech"
   ```
   *O parâmetro `-m` recebe uma mensagem explicativa do que foi feito.*

4. **Enviar para o GitHub (Push):**
   ```powershell
   git push origin main
   ```
   *Envia o histórico de commits para a sua conta no GitHub.*

---

## 3. Padrão de Mensagens de Commit (Conventional Commits)

No seu projeto AtlasERP, estamos utilizando o padrão profissional **Conventional Commits**:
- `fix(...)`: Para correção de bugs.
- `feat(...)`: Para novas funcionalidades.
- `style(...)`: Para alterações de design, CSS ou layout.
- `docs(...)`: Para inclusão de documentação ou apostilas.

Isso torna o seu repositório no GitHub extremamente elegante e fácil de entender por recrutadores e outros desenvolvedores!
