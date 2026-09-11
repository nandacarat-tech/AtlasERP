# Apostila 06: Gestão de Frota, Logística Reversa e Retorno de Entregas Mal-Sucedidas

Bem-vinda à Sexta Apostila do **AtlasERP por NandaTech**!

Nesta aula, abordamos um dos maiores desafios operacionais na gestão de frotas e logística empresarial: o **Tratamento de Entregas Mal-Sucedidas** e a **Logística Reversa Automática**.

---

## 1. O que é Logística Reversa e por que ela é Vital num ERP?

Nem toda entrega enviada pela empresa chega com sucesso ao cliente final. Diversos fatores operacionais podem interromper o fluxo de entrega:
- **Cliente Ausente:** O veículo chega ao local, mas não há ninguém para receber a carga.
- **Endereço Não Localizado:** Erro no cadastro de endereço ou zona rural inacessível.
- **Recusa pelo Cliente:** Cancelamento ou desistência no momento da entrega.
- **Avaria no Transporte:** Danos físicos ocorridos com a carga durante o trajeto.
- **Item Divergente:** Produto entregue é diferente do pedido realizado.

Sem um controle integrado no ERP, os produtos que voltam no caminhão ficam "perdidos no limbo", gerando furos de estoque e divergências financeiras.

---

## 2. A Arquitetura do Modelo `DeliveryReturn`

No arquivo [app/models.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/models.py), estruturamos a classe `DeliveryReturn`:

```python
class DeliveryReturn(db.Model):
    __tablename__ = "delivery_returns"

    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey("sales.id"), nullable=True)
    route_id = db.Column(db.Integer, db.ForeignKey("routes.id"), nullable=True)
    driver_id = db.Column(db.Integer, db.ForeignKey("drivers.id"), nullable=True)
    vehicle_id = db.Column(db.Integer, db.ForeignKey("fleet_vehicles.id"), nullable=True)
    customer_name = db.Column(db.String(120), nullable=False)
    attempt_date = db.Column(db.Date, nullable=False, default=datetime.utcnow)
    reason = db.Column(db.String(50), nullable=False)
    status = db.Column(db.String(30), nullable=False, default="PENDING_RETURN")
    action_taken = db.Column(db.Text, nullable=True)
    notes = db.Column(db.Text, nullable=True)
```

Essa estrutura nos permite saber exatamente **qual motorista**, **qual veículo** e **qual rota** registraram a ocorrência.

---

## 3. Automação da Devolução ao Estoque em Python

No arquivo [app/routes.py](file:///C:/Users/Fernanda/Projetos/AtlasERP/app/routes.py), implementamos o mecanismo de recomposição de estoque quando o operador altera o status da ocorrência para `RETURNED_TO_STOCK`:

```python
if new_status == "RETURNED_TO_STOCK" and old_status != "RETURNED_TO_STOCK" and delivery_return.sale_id:
    sale = db.session.get(Sale, delivery_return.sale_id)
    if sale:
        for item in sale.items:
            product = db.session.get(Product, item.product_id)
            if product:
                product.stock_quantity += item.quantity
                stock_movement = StockMovement(
                    product_id=product.id,
                    movement_type="IN",
                    quantity=item.quantity,
                    unit_price=item.unit_price,
                    notes=f"Retorno de entrega mal-sucedida #{delivery_return.id} (Cliente: {delivery_return.customer_name})"
                )
                db.session.add(stock_movement)
```

Essa lógica garante que:
1. As unidades físicas que voltaram para o galpão voltam para a contagem de estoque disponível.
2. É registrado um histórico oficial de movimentação de entrada (`movement_type="IN"`) para auditoria.

---

## 📝 Exercício Didático de Fixação

1. Acesse `http://127.0.0.1:5000/ui/sales` e confirme uma venda com 2 unidades de um produto.
2. Anote o saldo de estoque do produto.
3. Acesse **Frota $\rightarrow$ Retorno de Entregas** em `http://127.0.0.1:5000/ui/fleet/returns`.
4. Clique em **+ Registrar Insucesso de Entrega**, informe a venda, selecione o motivo **Cliente Ausente** e salve.
5. Na tabela de ocorrências, clique no botão **Devolver ao Estoque**.
6. Acesse a tela de **Produtos** (`/ui/products`) e comprove que o saldo do produto foi recomposto automaticamente!
