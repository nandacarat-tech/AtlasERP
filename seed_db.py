# seed_db.py
"""
Script de Povoamento de Dados (Seed Data) para o AtlasERP por NandaTech.
Simula uma empresa madura em operação há vários anos com equipe de 10 funcionários
e grande volume de dados para demonstração em ambientes de nuvem.
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import random

from app import create_app, db
from app.customer_models import Customer
from app.financial_models import (
    FinancialCategory,
    FinancialTransaction,
    Invoice,
    PayrollExpense,
)
from app.models import (
    DeliveryReturn,
    Driver,
    FleetMaintenance,
    FleetVehicle,
    Product,
    Route,
)
from app.purchase_models import Purchase, PurchaseItem
from app.sale_models import Sale, SaleItem
from app.stock_movement_models import StockMovement
from app.supplier_models import Supplier


def seed_database():
    app = create_app()

    with app.app_context():
        print("[1/7] Limpando registros antigos do banco de dados...")
        db.session.query(DeliveryReturn).delete()
        db.session.query(Route).delete()
        db.session.query(FleetMaintenance).delete()
        db.session.query(Driver).delete()
        db.session.query(FleetVehicle).delete()
        db.session.query(Invoice).delete()
        db.session.query(PayrollExpense).delete()
        db.session.query(FinancialTransaction).delete()
        db.session.query(FinancialCategory).delete()
        db.session.query(StockMovement).delete()
        db.session.query(PurchaseItem).delete()
        db.session.query(Purchase).delete()
        db.session.query(SaleItem).delete()
        db.session.query(Sale).delete()
        db.session.query(Supplier).delete()
        db.session.query(Customer).delete()
        db.session.query(Product).delete()
        db.session.commit()

        print("[2/7] Cadastrando 20 Produtos em Estoque...")
        products_data = [
            ("PROD-001", "Notebook Pro15 Intel i7 16GB", "Laptop de alta performance para uso corporativo", "4500.00", 18, 5),
            ("PROD-002", "Monitor LED 27 IPS UltraWide", "Monitor para produtividade e design", "1350.00", 25, 5),
            ("PROD-003", "Cadeira Ergonômica Executive Pro", "Cadeira ajustável NR17 com apoio lombar", "980.00", 12, 3),
            ("PROD-004", "Teclado Mecânico RGB Wireless", "Teclado silencioso para escritório", "320.00", 45, 10),
            ("PROD-005", "Mouse Ergológico Vertical Bluetooth", "Mouse ergonômico anti-LER", "180.00", 30, 8),
            ("PROD-006", "Impressora Multifuncional Laser Tank", "Impressora de grande volume de impressão", "2100.00", 6, 2),
            ("PROD-007", "Mesa Corporativa L 160x140cm", "Mesa em MDF resistente com passa cabos", "750.00", 8, 2),
            ("PROD-008", "Nobreak Senoidal 1500VA Bivolt", "Proteção de energia para servidores e estações", "1150.00", 10, 3),
            ("PROD-009", "Switch Gigabit 24 Portas Rack", "Switch gerenciável para infraestrutura", "890.00", 14, 4),
            ("PROD-010", "Cabo de Rede Cat6 305m", "Caixa de cabo homologado ANATEL", "420.00", 22, 5),
            ("PROD-011", "Webcam 4K UltraHD com Microfone", "Câmera para videoconferência com tampa de privacidade", "450.00", 3, 5), # Estoque baixo
            ("PROD-012", "Headset Corporate USB Noise Canceling", "Fone de ouvido profissional com cancelamento de ruído", "280.00", 2, 5), # Estoque baixo
            ("PROD-013", "HD Externo 4TB USB 3.2", "Disco rígido portátil reforçado", "520.00", 0, 5), # Esgotado
            ("PROD-014", "Filtro de Linha Dimerizado 8 Tomadas", "Régua de tomadas com proteção de surto", "95.00", 50, 10),
            ("PROD-015", "Roteador Wi-Fi 6 Mesh Tri-Band", "Roteador empresarial de alta velocidade", "680.00", 15, 4),
            ("PROD-016", "Suporte Duplo para Monitores Articulado", "Suporte a gás para 2 monitores até 32 pol", "240.00", 28, 6),
            ("PROD-017", "Gabinete Mid Tower ATX Ventilado", "Gabinete corporativo silencioso", "310.00", 9, 3),
            ("PROD-018", "SSD NVMe 1TB PCIe 4.0", "Armazenamento ultra-rápido para PCs e servidores", "410.00", 0, 8), # Esgotado
            ("PROD-019", "Projetor Full HD 4000 Lumens", "Projetor para salas de reunião e treinamentos", "3200.00", 4, 1),
            ("PROD-020", "Kit Manutenção e Ferramentas TI", "Maleta com alicates, testador de cabo e chaves", "190.00", 11, 3),
        ]

        products = []
        for sku, name, desc, price, qty, min_qty in products_data:
            p = Product(
                sku=sku,
                name=name,
                description=desc,
                price=Decimal(price),
                stock_quantity=qty,
                minimum_stock=min_qty,
                is_active=True
            )
            db.session.add(p)
            products.append(p)
        db.session.commit()

        print("[3/7] Cadastrando 12 Clientes e 8 Fornecedores...")
        customers_data = [
            ("Tecnologia Viva S.A.", "12.345.678/0001-90", "contato@tecnologiaviva.com.br", "(11) 3456-7890"),
            ("Logística Express Brasil", "23.456.789/0001-01", "compras@logexpress.com.br", "(11) 3210-4321"),
            ("Supermercados Cidade Ltda", "34.567.890/0001-12", "financeiro@supercidade.com.br", "(19) 3871-9988"),
            ("Hospital & Clínica Vida", "45.678.901/0001-23", "suprimentos@clinicavida.med.br", "(21) 2543-1122"),
            ("Academia Performance Fit", "56.789.012/0001-34", "adm@performancefit.com.br", "(11) 98765-4321"),
            ("Escola Futuro do Saber", "67.890.123/0001-45", "diretoria@futurosaber.edu.br", "(15) 3233-4455"),
            ("Restaurante Tempero Real", "78.901.234/0001-56", "gerencia@temperoreal.com.br", "(11) 3344-5566"),
            ("Carlos Eduardo Oliveira", "123.456.789-00", "carlos.oliveira@gmail.com", "(11) 99887-6655"),
            ("Juliana Mendes Santos", "234.567.890-11", "juliana.mendes@outlook.com", "(21) 98112-3344"),
            ("Marcos Antonio Pereira", "345.678.901-22", "marcos.pereira@yahoo.com.br", "(31) 99223-4455"),
            ("Indústria Metalúrgica MetalSulfur", "89.012.345/0001-67", "compras@metalsulfur.com.br", "(19) 3412-8800"),
            ("Construtora & Engenharia Alvorada", "90.123.456/0001-78", "suprimentos@alvoradaeng.com.br", "(11) 3090-7700"),
        ]
        customers = []
        for name, doc, email, phone in customers_data:
            c = Customer(name=name, document=doc, email=email, phone=phone, is_active=True)
            db.session.add(c)
            customers.append(c)

        suppliers_data = [
            ("Distribuidora Tech Master Brasil", "11.222.333/0001-81", "vendas@techmaster.com.br", "(11) 4004-1000"),
            ("Dell Computadores do Brasil Ltda", "72.381.189/0001-10", "corporativo@dell.com.br", "(11) 0800-701-0000"),
            ("Móveis Corporativos Flexform", "55.444.333/0001-22", "atendimento@flexform.com.br", "(11) 4689-9000"),
            ("Kalunga Comércio e Suprimentos", "43.283.811/0001-50", "vendascorpo@kalunga.com.br", "(11) 3346-9999"),
            ("Giga Security & Networking", "33.666.999/0001-44", "contato@gigasecurity.com.br", "(11) 2107-8888"),
            ("Auto Peças & Oficina Central Frota", "22.555.888/0001-33", "atendimento@centralfrota.com.br", "(11) 3838-2200"),
            ("Posto de Combustíveis PetroShell S.A.", "88.999.000/0001-11", "faturamento@petroshell.com.br", "(11) 3232-1100"),
            ("Imobiliária & Seguros Patrimonial", "77.888.999/0001-00", "alugueis@patrimonial.com.br", "(11) 3100-5000"),
        ]
        suppliers = []
        for name, doc, email, phone in suppliers_data:
            s = Supplier(name=name, document=doc, email=email, phone=phone, is_active=True)
            db.session.add(s)
            suppliers.append(s)
        db.session.commit()

        print("[4/7] Cadastrando Equipe de 10 Funcionarios na Folha de Pagamento...")
        employees_data = [
            ("Fernanda Santos", "Gerente Geral / CEO", "12500.00", "3400.00", "1500.00", "PAID"),
            ("Lucas Gabriel Silva", "Desenvolvedor Full Stack Senior", "9500.00", "2600.00", "1200.00", "PAID"),
            ("Amanda Rodrigues", "Analista Financeiro Pleno", "5800.00", "1600.00", "900.00", "PENDING"),
            ("Rodrigo Barbosa", "Supervisor de Vendas Comercial", "6500.00", "1800.00", "950.00", "PAID"),
            ("Camila Alcantara", "Assistente de Suporte e Atendimento", "3200.00", "880.00", "650.00", "PENDING"),
            ("Marcelo Costa", "Motorista de Frota Senior", "3800.00", "1050.00", "700.00", "PAID"),
            ("Robson Oliveira", "Motorista Entregador", "3400.00", "940.00", "650.00", "PENDING"),
            ("Diego Alves", "Encarregado de Estoque e Almoxarifado", "3600.00", "990.00", "680.00", "PAID"),
            ("Patricia Lima", "Auxiliar de Logística", "2800.00", "770.00", "600.00", "PENDING"),
            ("Thiago Martins", "Técnico de Manutenção TI", "4200.00", "1150.00", "750.00", "PAID"),
        ]
        payroll_records = []
        for emp, role, base, charges, ben, st in employees_data:
            p = PayrollExpense(
                employee_name=emp,
                role=role,
                base_salary=Decimal(base),
                charges_amount=Decimal(charges),
                benefits_amount=Decimal(ben),
                status=st,
                notes="Folha de pagamento mensal referente a Setembro/2026"
            )
            db.session.add(p)
            payroll_records.append(p)
        db.session.commit()

        print("[5/7] Cadastrando Categorias e Lancamentos Financeiros (DRE)...")
        cat_fixa = FinancialCategory(name="Custos Fixos & Sede", category_type="FIXED_COST", description="Aluguel, luz, água e internet")
        cat_var = FinancialCategory(name="Insumos & Fretes", category_type="VARIABLE_COST", description="Mercadorias e fretes")
        cat_pess = FinancialCategory(name="Folha de Pagamento", category_type="PAYROLL", description="Salários e encargos")
        cat_rec = FinancialCategory(name="Receitas de Vendas", category_type="REVENUE", description="Faturamento com vendas de produtos")

        db.session.add_all([cat_fixa, cat_var, cat_pess, cat_rec])
        db.session.commit()

        transactions_data = [
            ("Aluguel Sede Corporativa Av. Paulista", "8500.00", "EXPENSE", "PAID", cat_fixa.id, date(2026, 9, 1), date(2026, 9, 1)),
            ("Energia Elétrica Enel Matriz", "1850.00", "EXPENSE", "PENDING", cat_fixa.id, date(2026, 9, 15), None),
            ("Internet Fibra Óptica 1Gbps Dedicado", "890.00", "EXPENSE", "PAID", cat_fixa.id, date(2026, 9, 5), date(2026, 9, 5)),
            ("Assinatura AWS Nuvem e Servidores", "3400.00", "EXPENSE", "PAID", cat_fixa.id, date(2026, 9, 10), date(2026, 9, 10)),
            ("Seguro Frota de Veículos Porto", "2100.00", "EXPENSE", "PENDING", cat_fixa.id, date(2026, 9, 20), None),
            ("Compra de Lote Notebooks Dell Pro", "28000.00", "EXPENSE", "PAID", cat_var.id, date(2026, 8, 25), date(2026, 8, 25)),
            ("Faturamento Venda Corporativa Tecnologia Viva", "18000.00", "REVENUE", "PAID", cat_rec.id, date(2026, 9, 2), date(2026, 9, 2)),
            ("Faturamento Venda Logística Express", "14500.00", "REVENUE", "PAID", cat_rec.id, date(2026, 9, 4), date(2026, 9, 4)),
            ("Faturamento Venda Supermercados Cidade", "9200.00", "REVENUE", "PENDING", cat_rec.id, date(2026, 9, 18), None),
            ("Faturamento Venda Hospital Vida", "22400.00", "REVENUE", "PAID", cat_rec.id, date(2026, 9, 8), date(2026, 9, 8)),
        ]

        for desc, amt, t_type, st, cat_id, due, pay in transactions_data:
            t = FinancialTransaction(
                description=desc,
                amount=Decimal(amt),
                transaction_type=t_type,
                status=st,
                category_id=cat_id,
                due_date=due,
                payment_date=pay,
                notes="Lançamento automático de sistema"
            )
            db.session.add(t)
        db.session.commit()

        print("[6/7] Cadastrando 15 Vendas e 8 Compras de Suprimentos...")
        # Vendas
        sales = []
        for i in range(1, 16):
            cust = customers[(i - 1) % len(customers)]
            st = "CONFIRMED" if i <= 11 else ("OPEN" if i <= 14 else "CANCELLED")
            sale = Sale(customer_id=cust.id, status=st, total_amount=Decimal("0.00"))
            db.session.add(sale)
            sales.append(sale)
        db.session.commit()

        # Itens de Venda e Estoque
        for idx, sale in enumerate(sales):
            p1 = products[idx % len(products)]
            p2 = products[(idx + 3) % len(products)]
            qty1 = random.randint(1, 4)
            qty2 = random.randint(1, 3)

            item1 = SaleItem(sale_id=sale.id, product_id=p1.id, quantity=qty1, unit_price=p1.price)
            item2 = SaleItem(sale_id=sale.id, product_id=p2.id, quantity=qty2, unit_price=p2.price)
            db.session.add_all([item1, item2])
            sale.recalculate_total()

            # Movimentação de estoque e NF-e para vendas confirmadas
            if sale.status == "CONFIRMED":
                m1 = StockMovement(
                    product_id=p1.id,
                    sale_id=sale.id,
                    movement_type="OUT",
                    quantity=qty1,
                    stock_before=p1.stock_quantity + qty1,
                    stock_after=p1.stock_quantity
                )
                m2 = StockMovement(
                    product_id=p2.id,
                    sale_id=sale.id,
                    movement_type="OUT",
                    quantity=qty2,
                    stock_before=p2.stock_quantity + qty2,
                    stock_after=p2.stock_quantity
                )
                db.session.add_all([m1, m2])

                # NF-e
                inv_status = "ISSUED" if idx <= 8 else "PENDING_EMISSION"
                uf, yymm, cnpj = "35", "2609", "11222333000181"
                num = f"{sale.id:09d}"
                rnd = f"{abs(hash(sale.id)) % 100000000:09d}"[:9]
                key = f"{uf}{yymm}{cnpj}55001{num}{rnd}"[:44]

                inv = Invoice(
                    sale_id=sale.id,
                    customer_id=sale.customer_id,
                    invoice_number=f"NF-e {sale.id:06d}",
                    access_key=key if inv_status == "ISSUED" else None,
                    status=inv_status,
                    sefaz_status_code="100" if inv_status == "ISSUED" else None,
                    sefaz_message="Autorizado o uso da NF-e (Ambiente SEFAZ Nuvem)" if inv_status == "ISSUED" else None,
                    issued_at=datetime.now(timezone.utc) if inv_status == "ISSUED" else None
                )
                db.session.add(inv)
        db.session.commit()

        # Compras
        for i in range(1, 9):
            supp = suppliers[(i - 1) % len(suppliers)]
            st = "RECEIVED" if i <= 6 else "OPEN"
            purchase = Purchase(supplier_id=supp.id, status=st, total_amount=Decimal("0.00"))
            db.session.add(purchase)
            db.session.commit()

            p = products[i % len(products)]
            qty = random.randint(5, 15)
            cost = Decimal(str(p.price)) * Decimal("0.65")

            p_item = PurchaseItem(purchase_id=purchase.id, product_id=p.id, quantity=qty, unit_cost=cost)
            db.session.add(p_item)
            purchase.total_amount = cost * qty

            if st == "RECEIVED":
                purchase.received_at = datetime.now(timezone.utc) - timedelta(days=i * 3)
                m = StockMovement(
                    product_id=p.id,
                    purchase_id=purchase.id,
                    movement_type="IN",
                    quantity=qty,
                    stock_before=p.stock_quantity - qty if p.stock_quantity >= qty else 0,
                    stock_after=p.stock_quantity
                )
                db.session.add(m)
        db.session.commit()

        print("[7/7] Cadastrando Frota, Motoristas, Manutencoes, Rotas e Devolucoes...")
        vehicles_data = [
            ("ABC-1D23", "Van Carga Express", "Mercedes-Benz", "Sprinter 416 CDi", 2023, "1800.00", 42500, "IN_USE"),
            ("BCD-2E34", "Caminhão Baú VUC", "Volkswagen", "Delivery Express 4.150", 2022, "3500.00", 68200, "IN_USE"),
            ("CDE-3F45", "Furgão Utilitário", "Fiat", "Fiorino Endurance 1.4", 2024, "650.00", 18400, "AVAILABLE"),
            ("DEF-4G56", "Caminhão Pesado Sider", "Mercedes-Benz", "Atego 1719", 2021, "8500.00", 112000, "MAINTENANCE"),
            ("EFG-5H67", "Van Refrigerada", "Peugeot", "Expert Refrigerada", 2023, "1400.00", 35100, "AVAILABLE"),
            ("FGH-6I78", "Furgão Médio Carga", "Renault", "Master L1H1", 2022, "1500.00", 54800, "IN_USE"),
        ]
        vehicles = []
        for plate, vtype, brand, model, yr, cap, km, st in vehicles_data:
            v = FleetVehicle(
                plate=plate,
                vehicle_type=vtype,
                brand=brand,
                model=model,
                manufacture_year=yr,
                capacity_kg=Decimal(cap),
                current_mileage=km,
                status=st,
                notes="Veículo rastreado por GPS em tempo real"
            )
            db.session.add(v)
            vehicles.append(v)
        db.session.commit()

        drivers_data = [
            ("Marcelo Costa", "111.222.333-44", "(11) 98888-1111", "99887766554", "D", date(2028, 5, 20), "ACTIVE", vehicles[0].id),
            ("Robson Oliveira", "222.333.444-55", "(11) 97777-2222", "88776655443", "C", date(2027, 8, 15), "ACTIVE", vehicles[1].id),
            ("Alexandre Souza", "333.444.555-66", "(11) 96666-3333", "77665544332", "B", date(2026, 11, 10), "ACTIVE", vehicles[2].id),
            ("Fernando Henrique", "444.555.666-77", "(19) 95555-4444", "66554433221", "E", date(2029, 3, 30), "ACTIVE", vehicles[3].id),
            ("Gabriel Ribeiro", "555.666.777-88", "(11) 94444-5555", "55443322110", "D", date(2028, 1, 12), "ACTIVE", vehicles[4].id),
            ("Eduardo Paes", "666.777.888-99", "(21) 93333-6666", "44332211009", "C", date(2027, 9, 25), "ACTIVE", vehicles[5].id),
        ]
        drivers = []
        for name, cpf, phone, cnh, cat, exp, st, v_id in drivers_data:
            d = Driver(
                name=name,
                cpf=cpf,
                phone=phone,
                license_number=cnh,
                license_category=cat,
                license_expiry=exp,
                status=st,
                vehicle_id=v_id,
                notes="Motorista qualificado em direção defensiva"
            )
            db.session.add(d)
            drivers.append(d)
        db.session.commit()

        # Manutenções
        maint1 = FleetMaintenance(
            vehicle_id=vehicles[3].id,
            maintenance_type="PREVENTIVE",
            description="Revisão geral de 100 mil km, troca de freios e embreagem",
            workshop="Mecânica & Truck Center Diesel",
            opened_at=date(2026, 9, 1),
            scheduled_at=date(2026, 9, 2),
            mileage=112000,
            cost=Decimal("4500.00"),
            status="OPEN",
            next_maintenance_at=date(2027, 3, 1),
            notes="Aguardando peça de reposição do câmbio"
        )
        maint2 = FleetMaintenance(
            vehicle_id=vehicles[0].id,
            maintenance_type="PREVENTIVE",
            description="Troca de óleo de motor, filtro de combustível e alinhamento",
            workshop="Auto Centro Express Mooca",
            opened_at=date(2026, 8, 10),
            completed_at=date(2026, 8, 11),
            mileage=40000,
            cost=Decimal("780.00"),
            status="COMPLETED",
            next_maintenance_at=date(2027, 2, 10),
            notes="Revisão preventiva realizada dentro do prazo"
        )
        db.session.add_all([maint1, maint2])

        # Rotas
        routes_data = [
            ("Rota 01 - SP Capital Z.Sul & Centro", vehicles[0].id, drivers[0].id, date(2026, 9, 11), "IN_PROGRESS", "Entrega de lotes eletrônicos corporativos"),
            ("Rota 02 - Campinas & R.Metropolitana", vehicles[1].id, drivers[1].id, date(2026, 9, 11), "IN_PROGRESS", "Abastecimento de redes de supermercado"),
            ("Rota 03 - Baixada Santista & Litoral", vehicles[2].id, drivers[2].id, date(2026, 9, 10), "COMPLETED", "Entrega urgente de equipamentos de TI"),
            ("Rota 04 - Vale do Paraíba & SJCampos", vehicles[4].id, drivers[4].id, date(2026, 9, 12), "PENDING", "Logística programada para hospitais"),
            ("Rota 05 - SP Zona Oeste & Alphaville", vehicles[5].id, drivers[5].id, date(2026, 9, 11), "IN_PROGRESS", "Distribuição em escritórios corporativos"),
        ]
        routes = []
        for rname, vid, did, sdate, st, desc in routes_data:
            r = Route(
                route_name=rname,
                vehicle_id=vid,
                driver_id=did,
                start_date=sdate,
                status=st,
                description=desc
            )
            db.session.add(r)
            routes.append(r)
        db.session.commit()

        # Retorno de Entregas (Logística Reversa)
        ret1 = DeliveryReturn(
            sale_id=sales[0].id,
            route_id=routes[0].id,
            driver_id=drivers[0].id,
            vehicle_id=vehicles[0].id,
            customer_name="Tecnologia Viva S.A.",
            attempt_date=date(2026, 9, 11),
            reason="CLIENT_ABSENT",
            status="PENDING_RETURN",
            action_taken="",
            notes="Portaria fechada no momento da chegada. Reentrega será agendada."
        )
        ret2 = DeliveryReturn(
            sale_id=sales[1].id,
            route_id=routes[1].id,
            driver_id=drivers[1].id,
            vehicle_id=vehicles[1].id,
            customer_name="Logística Express Brasil",
            attempt_date=date(2026, 9, 10),
            reason="ADDRESS_NOT_FOUND",
            status="RETURNED_TO_STOCK",
            action_taken="Mercadoria conferida e reestocada no galpão central.",
            notes="Número de galpão incorreto na nota fiscal."
        )
        ret3 = DeliveryReturn(
            sale_id=sales[2].id,
            route_id=routes[2].id,
            driver_id=drivers[2].id,
            vehicle_id=vehicles[2].id,
            customer_name="Supermercados Cidade Ltda",
            attempt_date=date(2026, 9, 9),
            reason="CARGO_DAMAGED",
            status="PENDING_RETURN",
            action_taken="",
            notes="Caixa avariada durante o manuseio. Aguardando laudo do seguro."
        )
        db.session.add_all([ret1, ret2, ret3])
        db.session.commit()

        print("[OK] POVOAMENTO CONCLUIDO COM SUCESSO!")
        print("--------------------------------------------------")
        print(f"- Produtos cadastrados: {Product.query.count()}")
        print(f"- Clientes cadastrados: {Customer.query.count()}")
        print(f"- Fornecedores cadastrados: {Supplier.query.count()}")
        print(f"- Equipe / Folha de Pagamento: {PayrollExpense.query.count()} funcionarios")
        print(f"- Lancamentos Financeiros (DRE): {FinancialTransaction.query.count()}")
        print(f"- Vendas Registradas: {Sale.query.count()}")
        print(f"- Compras de Suprimentos: {Purchase.query.count()}")
        print(f"- Notas Fiscais (NF-e SEFAZ): {Invoice.query.count()}")
        print(f"- Veiculos de Frota: {FleetVehicle.query.count()}")
        print(f"- Motoristas: {Driver.query.count()}")
        print(f"- Rotas de Entrega: {Route.query.count()}")
        print(f"- Devolucoes / Logistica Reversa: {DeliveryReturn.query.count()}")
        print("--------------------------------------------------")


if __name__ == "__main__":
    seed_database()
