# seed_db.py
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


def gen_cpf(n: int) -> str:
    base = f"{n:09d}"
    digits = [int(c) for c in base]
    s1 = sum(d * (10 - i) for i, d in enumerate(digits))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    digits.append(d1)
    s2 = sum(d * (11 - i) for i, d in enumerate(digits))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    digits.append(d2)
    s = "".join(str(d) for d in digits)
    return f"{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}"


def gen_cnpj(n: int) -> str:
    base = f"{n:08d}0001"
    digits = [int(c) for c in base]
    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(d * w1[i] for i, d in enumerate(digits))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    digits.append(d1)
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s2 = sum(d * w2[i] for i, d in enumerate(digits))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    digits.append(d2)
    s = "".join(str(d) for d in digits)
    return f"{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}"


VALID_DDDS = [
    11, 12, 13, 14, 15, 16, 17, 18, 19,
    21, 22, 24, 27, 28,
    31, 32, 33, 34, 35, 37, 38,
    41, 42, 43, 44, 45, 46, 47, 48, 49,
    51, 53, 54, 55,
    61, 62, 63, 64, 65, 66, 67, 68, 69,
    71, 73, 74, 75, 77, 79,
    81, 82, 83, 84, 85, 86, 87, 88, 89,
    91, 92, 93, 94, 95, 96, 97, 98, 99
]


def gen_phone(idx: int) -> str:
    ddd = VALID_DDDS[idx % len(VALID_DDDS)]
    part1 = 90000 + (idx * 37) % 9999
    part2 = 1000 + (idx * 53) % 8999
    return f"({ddd}) {part1:05d}-{part2:04d}"


def seed_database():
    app = create_app()

    with app.app_context():
        print("[1/7] Limpando registros operacionais do banco de dados...")
        is_mysql = "mysql" in str(db.engine.url)
        if is_mysql:
            db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 0;"))

        try:
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
        finally:
            if is_mysql:
                db.session.execute(db.text("SET FOREIGN_KEY_CHECKS = 1;"))
                db.session.commit()

        print("[2/7] Cadastrando 20 Produtos em Estoque...")
        products_data = [
            ("PROD-001", "Notebook Pro15 Intel i7 16GB", "Laptop de alta performance para uso corporativo", "4500.00", 25, 5),
            ("PROD-002", "Monitor LED 27 IPS UltraWide", "Monitor para produtividade e design", "1350.00", 40, 8),
            ("PROD-003", "Cadeira Ergonomica Executive Pro", "Cadeira ajustavel NR17 com apoio lombar", "980.00", 18, 5),
            ("PROD-004", "Teclado Mecanico RGB Wireless", "Teclado silencioso para escritorio", "320.00", 60, 10),
            ("PROD-005", "Mouse Ergologico Vertical Bluetooth", "Mouse ergonomico anti-LER", "180.00", 45, 10),
            ("PROD-006", "Impressora Multifuncional Laser Tank", "Impressora de grande volume de impressao", "2100.00", 10, 3),
            ("PROD-007", "Mesa Corporativa L 160x140cm", "Mesa em MDF resistente com passa cabos", "750.00", 15, 3),
            ("PROD-008", "Nobreak Senoidal 1500VA Bivolt", "Protecao de energia para servidores e estacoes", "1150.00", 14, 4),
            ("PROD-009", "Switch Gigabit 24 Portas Rack", "Switch gerenciavel para infraestrutura", "890.00", 20, 5),
            ("PROD-010", "Cabo de Rede Cat6 305m", "Caixa de cabo homologado ANATEL", "420.00", 35, 6),
            ("PROD-011", "Webcam 4K UltraHD com Microfone", "Camera para videoconferencia com tampa de privacidade", "450.00", 4, 6),
            ("PROD-012", "Headset Corporate USB Noise Canceling", "Fone de ouvido profissional com cancelamento de ruido", "280.00", 3, 6),
            ("PROD-013", "HD Externo 4TB USB 3.2", "Disco rigido portatil reforcado", "520.00", 1, 5),
            ("PROD-014", "Filtro de Linha Dimerizado 8 Tomadas", "Regua de tomadas com protecao de surto", "95.00", 75, 15),
            ("PROD-015", "Roteador Wi-Fi 6 Mesh Tri-Band", "Roteador empresarial de alta velocidade", "680.00", 22, 5),
            ("PROD-016", "Suporte Duplo para Monitores Articulado", "Suporte a gas para 2 monitores ate 32 pol", "240.00", 32, 6),
            ("PROD-017", "Gabinete Mid Tower ATX Ventilado", "Gabinete corporativo silencioso", "310.00", 12, 4),
            ("PROD-018", "SSD NVMe 1TB PCIe 4.0", "Armazenamento ultra-rapido para PCs e servidores", "410.00", 2, 8),
            ("PROD-019", "Projetor Full HD 4000 Lumens", "Projetor para salas de reuniao e treinamentos", "3200.00", 5, 2),
            ("PROD-020", "Kit Manutencao e Ferramentas TI", "Maleta com alicates, testador de cabo e chaves", "190.00", 16, 4),
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
                is_active=True,
            )
            db.session.add(p)
            products.append(p)
        db.session.commit()

        print("[3/7] Cadastrando 500 Clientes (250 B2B e 250 B2C) e 15 Fornecedores...")
        b2b_prefixes = [
            "Alfa", "Beta", "Delta", "Sigma", "Prime", "Elite", "Nexus", "Vanguard", "Global", "Nacional",
            "Brasil", "Master", "Solucoes", "Alianca", "Uniao", "Horizonte", "Metropole", "Pinnacle", "Atlas", "Nova",
            "Pro", "Tech", "Apex", "Omni", "Inova"
        ]
        b2b_sectors = [
            "Tecnologia", "Logistica", "Comercio", "Industria", "Alimentos", "Consultoria", "Distribuicao",
            "Engenharia", "Servicos", "Sistemas", "Transportes", "Atacado", "Varejo", "Farmaceutica", "Quimica",
            "Metalurgica", "Embalagens", "Textil", "Energia", "Telecom"
        ]
        b2b_suffixes = [
            "Ltda", "S.A.", "EIRELI", "do Brasil", "Corporativa", "Express", "Brasil Ltda", "Comercial Ltda",
            "Servicos Integrados", "Participacoes"
        ]

        first_names = [
            "Ana", "Bruno", "Carlos", "Daniela", "Eduardo", "Fernanda", "Gabriel", "Helena", "Igor", "Juliana",
            "Lucas", "Mariana", "Nelson", "Olivia", "Pedro", "Rafaela", "Rodrigo", "Sofia", "Thiago", "Vanessa",
            "Marcio", "Aline", "Felipe", "Beatriz", "Rafael"
        ]
        last_names = [
            "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira", "Lima", "Gomes",
            "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes", "Soares", "Fernandes", "Vieira", "Barbosa",
            "Rocha", "Dias", "Nascimento", "Andrade", "Moreira"
        ]

        customers = []

        # 250 Clientes B2B
        for i in range(1, 251):
            pfx = b2b_prefixes[(i * 3) % len(b2b_prefixes)]
            sct = b2b_sectors[(i * 7) % len(b2b_sectors)]
            sfx = b2b_suffixes[(i * 5) % len(b2b_suffixes)]
            name = f"{pfx} {sct} {sfx}"
            doc = gen_cnpj(11000000 + i)
            clean_slug = f"{pfx.lower()}{sct.lower()}{i}"
            email = f"contato@{clean_slug}.com.br"
            phone = gen_phone(i)
            is_act = i % 25 != 0

            c = Customer(name=name, document=doc, email=email, phone=phone, is_active=is_act)
            db.session.add(c)
            customers.append(c)

        # 250 Clientes B2C
        for i in range(1, 251):
            fn = first_names[(i * 2) % len(first_names)]
            ln1 = last_names[(i * 3) % len(last_names)]
            ln2 = last_names[(i * 5) % len(last_names)]
            name = f"{fn} {ln1} {ln2}"
            doc = gen_cpf(200000000 + i)
            email = f"{fn.lower()}.{ln1.lower()}.{i}@emailbrasil.com"
            phone = gen_phone(250 + i)
            is_act = i % 20 != 0

            c = Customer(name=name, document=doc, email=email, phone=phone, is_active=is_act)
            db.session.add(c)
            customers.append(c)

        db.session.flush()

        suppliers_raw = [
            ("Distribuidora Tech Master Brasil", "(11) 4004-1000"),
            ("Dell Computadores do Brasil Ltda", "(11) 3718-2000"),
            ("Moveis Corporativos Flexform", "(11) 4689-9000"),
            ("Kalunga Comercio e Suprimentos", "(11) 3346-9999"),
            ("Giga Security & Networking", "(11) 2107-8888"),
            ("Auto Pecas & Oficina Central Frota", "(11) 3838-2200"),
            ("Posto de Combustiveis PetroShell S.A.", "(11) 3232-1100"),
            ("Imobiliaria & Seguros Patrimonial", "(11) 3100-5000"),
            ("EletroCabos do Brasil Industrial", "(19) 3456-1122"),
            ("Logistica Aerea & Cargas Rapidas", "(11) 2445-3344"),
            ("Papelaria & Insumos Empresariais", "(21) 2233-4455"),
            ("Sistemas de Refrigeracao Polar", "(41) 3322-5566"),
            ("Metalurgica Central Estruturas", "(31) 3211-7788"),
            ("Provedor Cloud & DataCenter Brasil", "(11) 4123-9988"),
            ("Equipamentos Medicos & Seguranca", "(11) 3088-7711"),
        ]

        suppliers = []
        for idx, (s_name, s_phone) in enumerate(suppliers_raw, start=1):
            s_doc = gen_cnpj(55000000 + idx)
            slug = s_name.split()[0].lower()
            s_email = f"contato@{slug}{idx}.com.br"
            s = Supplier(name=s_name, document=s_doc, email=s_email, phone=s_phone, is_active=True)
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
            ("Patricia Lima", "Auxiliar de Logistica", "2800.00", "770.00", "600.00", "PENDING"),
            ("Thiago Martins", "Tecnico de Manutencao TI", "4200.00", "1150.00", "750.00", "PAID"),
        ]
        for emp, role, base, charges, ben, st in employees_data:
            p = PayrollExpense(
                employee_name=emp,
                role=role,
                base_salary=Decimal(base),
                charges_amount=Decimal(charges),
                benefits_amount=Decimal(ben),
                status=st,
                notes="Folha de pagamento mensal corporativa",
            )
            db.session.add(p)
        db.session.commit()

        print("[5/7] Cadastrando Categorias e Lancamentos Financeiros (DRE)...")
        cat_fixa = FinancialCategory(name="Custos Fixos & Sede", category_type="FIXED_COST", description="Aluguel, luz, agua e internet")
        cat_var = FinancialCategory(name="Insumos & Fretes", category_type="VARIABLE_COST", description="Mercadorias e fretes")
        cat_pess = FinancialCategory(name="Folha de Pagamento", category_type="PAYROLL", description="Salarios e encargos")
        cat_rec = FinancialCategory(name="Receitas de Vendas", category_type="REVENUE", description="Faturamento com vendas de produtos")

        db.session.add_all([cat_fixa, cat_var, cat_pess, cat_rec])
        db.session.commit()

        transactions_data = [
            ("Aluguel Sede Corporativa Av. Paulista", "8500.00", "EXPENSE", "PAID", cat_fixa.id, date(2026, 9, 1), date(2026, 9, 1)),
            ("Energia Eletrica Matriz", "1850.00", "EXPENSE", "PENDING", cat_fixa.id, date(2026, 9, 15), None),
            ("Internet Fibra Optica 1Gbps Dedicado", "890.00", "EXPENSE", "PAID", cat_fixa.id, date(2026, 9, 5), date(2026, 9, 5)),
            ("Servicos Cloud & Infraestrutura GCP", "3400.00", "EXPENSE", "PAID", cat_fixa.id, date(2026, 9, 10), date(2026, 9, 10)),
            ("Seguro Frota de Veiculos", "2100.00", "EXPENSE", "PENDING", cat_fixa.id, date(2026, 9, 20), None),
            ("Compra de Lote Hardware Corporativo", "28000.00", "EXPENSE", "PAID", cat_var.id, date(2026, 8, 25), date(2026, 8, 25)),
            ("Faturamento Contrato B2B Alfa Tecnologia", "24500.00", "REVENUE", "PAID", cat_rec.id, date(2026, 9, 2), date(2026, 9, 2)),
            ("Faturamento Venda Delta Logistica", "18200.00", "REVENUE", "PAID", cat_rec.id, date(2026, 9, 4), date(2026, 9, 4)),
            ("Faturamento Venda Supermercados Cidade", "12400.00", "REVENUE", "PENDING", cat_rec.id, date(2026, 9, 18), None),
            ("Faturamento Venda Hospital Vida", "31200.00", "REVENUE", "PAID", cat_rec.id, date(2026, 9, 8), date(2026, 9, 8)),
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
                notes="Lancamento automatico de sistema",
            )
            db.session.add(t)
        db.session.commit()

        print("[6/7] Cadastrando 60 Pedidos de Venda e 15 Compras de Suprimentos...")
        sales = []
        for i in range(1, 61):
            cust = customers[(i * 7) % len(customers)]
            st = "CONFIRMED" if i <= 45 else ("OPEN" if i <= 55 else "CANCELLED")
            sale = Sale(customer_id=cust.id, status=st, total_amount=Decimal("0.00"))
            db.session.add(sale)
            sales.append(sale)
        db.session.commit()

        for idx, sale in enumerate(sales):
            p1 = products[idx % len(products)]
            p2 = products[(idx + 4) % len(products)]
            qty1 = random.randint(1, 3)
            qty2 = random.randint(1, 2)

            item1 = SaleItem(sale_id=sale.id, product_id=p1.id, quantity=qty1, unit_price=p1.price)
            item2 = SaleItem(sale_id=sale.id, product_id=p2.id, quantity=qty2, unit_price=p2.price)
            db.session.add_all([item1, item2])
            sale.recalculate_total()

            if sale.status == "CONFIRMED":
                m1 = StockMovement(
                    product_id=p1.id,
                    sale_id=sale.id,
                    movement_type="OUT",
                    quantity=qty1,
                    stock_before=p1.stock_quantity + qty1,
                    stock_after=p1.stock_quantity,
                )
                m2 = StockMovement(
                    product_id=p2.id,
                    sale_id=sale.id,
                    movement_type="OUT",
                    quantity=qty2,
                    stock_before=p2.stock_quantity + qty2,
                    stock_after=p2.stock_quantity,
                )
                db.session.add_all([m1, m2])

                inv_status = "ISSUED" if idx <= 35 else "PENDING_EMISSION"
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
                    issued_at=datetime.now(timezone.utc) if inv_status == "ISSUED" else None,
                )
                db.session.add(inv)
        db.session.commit()

        for i in range(1, 16):
            supp = suppliers[(i - 1) % len(suppliers)]
            st = "RECEIVED" if i <= 11 else "OPEN"
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
                purchase.received_at = datetime.now(timezone.utc) - timedelta(days=i * 2)
                m = StockMovement(
                    product_id=p.id,
                    purchase_id=purchase.id,
                    movement_type="IN",
                    quantity=qty,
                    stock_before=p.stock_quantity - qty if p.stock_quantity >= qty else 0,
                    stock_after=p.stock_quantity,
                )
                db.session.add(m)
        db.session.commit()

        print("[7/7] Cadastrando Frota Massiva: 30 Veiculos, 25 Motoristas, 25 Rotas, 12 Manutencoes e 10 Devolucoes...")
        # 30 Veiculos com status operacionais reais (18 IN_USE, 9 AVAILABLE, 3 MAINTENANCE)
        vehicles_specs = [
            ("ABC-1D23", "Van Carga Express", "Mercedes-Benz", "Sprinter 416 CDi", 2023, "1800.00", 42500, "IN_USE"),
            ("BCD-2E34", "Caminhao Bau VUC", "Volkswagen", "Delivery Express 4.150", 2022, "3500.00", 68200, "IN_USE"),
            ("CDE-3F45", "Furgao Utilitario", "Fiat", "Fiorino Endurance 1.4", 2024, "650.00", 18400, "AVAILABLE"),
            ("DEF-4G56", "Caminhao Pesado Sider", "Mercedes-Benz", "Atego 1719", 2021, "8500.00", 112000, "MAINTENANCE"),
            ("EFG-5H67", "Van Refrigerada", "Peugeot", "Expert Refrigerada", 2023, "1400.00", 35100, "AVAILABLE"),
            ("FGH-6I78", "Furgao Medio Carga", "Renault", "Master L1H1", 2022, "1500.00", 54800, "IN_USE"),
            ("GHI-7J89", "Caminhao Bau 3/4", "Iveco", "Daily 65-170", 2023, "4000.00", 38900, "IN_USE"),
            ("HIJ-8K90", "Cavalo Mecanico Toco", "Scania", "R450 4x2", 2022, "18000.00", 145000, "IN_USE"),
            ("IJK-9L01", "Carreta Graneleiro", "Volvo", "FH 540 6x4", 2021, "32000.00", 210000, "IN_USE"),
            ("JKL-0M12", "Van Passageiros TI", "Mercedes-Benz", "Sprinter 516 Passageiro", 2023, "2200.00", 29000, "AVAILABLE"),
            ("KLM-1N23", "Caminhao Toco Seco", "Ford", "Cargo 1119", 2020, "5500.00", 128000, "MAINTENANCE"),
            ("LMN-2O34", "Furgao Eletrico Urbano", "BYD", "T3 Eletrico", 2024, "800.00", 9200, "AVAILABLE"),
            ("MNO-3P45", "Caminhao Plataforma Guincho", "Volkswagen", "Constellation 14.190", 2022, "6000.00", 74000, "AVAILABLE"),
            ("NOP-4Q56", "Van isotermica Pereciveis", "Renault", "Master Frigorifica", 2023, "1600.00", 41000, "IN_USE"),
            ("OPQ-5R67", "Caminhao Bau Refrigerado", "Mercedes-Benz", "Accelo 1016", 2023, "6500.00", 32000, "IN_USE"),
            ("PQR-6S78", "Furgao de Distribuicao", "Peugeot", "Partner Rapid", 2024, "650.00", 12400, "AVAILABLE"),
            ("QRS-7T89", "Caminhao Bi-Trem", "Volvo", "FH 460 6x4", 2020, "45000.00", 298000, "IN_USE"),
            ("RST-8U90", "Caminhao Tanque Abastecimento", "Scania", "P310", 2021, "15000.00", 132000, "AVAILABLE"),
            ("STU-9V01", "Caminhonete 4x4 Resgate", "Toyota", "Hilux CD 2.8", 2023, "1000.00", 31500, "AVAILABLE"),
            ("TUV-0W12", "Furgao Carga Longa", "Ford", "Transit 350L", 2023, "1800.00", 44000, "IN_USE"),
            ("UVW-1X23", "Caminhao Coleta Seletiva", "Iveco", "Tector 170E28", 2022, "9000.00", 87000, "IN_USE"),
            ("VWX-2Y34", "Van Apoio Tecnico", "Citroen", "Jumpy Cargo", 2023, "1500.00", 26000, "AVAILABLE"),
            ("WXY-3Z45", "Caminhao Rodotrem 9 Eixos", "Mercedes-Benz", "Actros 2651", 2021, "50000.00", 310000, "IN_USE"),
            ("XYZ-4A56", "Caminhao Carga Seca Toco", "Volkswagen", "Delivery 9.170", 2023, "5200.00", 36000, "IN_USE"),
            ("YZA-5B67", "Furgao Utilitario Compacto", "Fiat", "Strada Endurance", 2024, "720.00", 14000, "AVAILABLE"),
            ("ZAB-6C78", "Caminhao Sider Urbano", "MAN", "TGX 28.440", 2020, "22000.00", 265000, "MAINTENANCE"),
            ("ABB-7D89", "Van Entrega Domiciliar", "Mercedes-Benz", "Sprinter 314 Street", 2023, "1400.00", 48000, "IN_USE"),
            ("BCC-8E90", "Caminhao Bau Extra Longo", "DAF", "CF 310", 2022, "12000.00", 94000, "IN_USE"),
            ("CDD-9F01", "Utilitario Express Hibrido", "Renault", "Kangoo E-Tech", 2024, "650.00", 8100, "AVAILABLE"),
            ("DEE-0G12", "Carreta Cegonha Suporte", "Scania", "G410", 2021, "28000.00", 189000, "IN_USE"),
        ]

        vehicles = []
        for plate, vtype, brand, model, yr, cap, km, st in vehicles_specs:
            v = FleetVehicle(
                plate=plate,
                vehicle_type=vtype,
                brand=brand,
                model=model,
                manufacture_year=yr,
                capacity_kg=Decimal(cap),
                current_mileage=km,
                status=st,
                notes="Veiculo com telemetria GPS e monitoramento em tempo real",
            )
            db.session.add(v)
            vehicles.append(v)
        db.session.commit()

        # 25 Motoristas Profissionais
        drivers_names = [
            "Marcelo Costa", "Robson Oliveira", "Alexandre Souza", "Fernando Henrique", "Gabriel Ribeiro",
            "Eduardo Paes", "Marcos Vinicius Lima", "Claudio Roberto Dias", "Paulo Sergio Barbosa", "Fabio Junior Castro",
            "Rodrigo de Paula", "Leandro Antunes", "Valter Silveira", "Adilson Monteiro", "Wellington Prado",
            "Rogerio Ceni Santos", "Danilo Fagundes", "Jefferson Alencar", "Gilberto Gilson", "Luciano Huck Silva",
            "Emerson Fittipaldi Lima", "Nelson Piquet Costa", "Rubens Barrichello Souza", "Ayrton Senna Ramos", "Felipe Massa Moreira"
        ]
        license_cats = ["D", "C", "B", "E", "D", "C", "E", "D", "C", "B", "E", "D", "D", "C", "E", "D", "C", "B", "D", "E", "E", "D", "C", "E", "B"]

        drivers = []
        for i, (name, cat) in enumerate(zip(drivers_names, license_cats), start=1):
            cpf = gen_cpf(300000000 + i)
            phone = gen_phone(300 + i)
            cnh = f"{77889900000 + i}"
            v_id = vehicles[(i - 1) % len(vehicles)].id
            d = Driver(
                name=name,
                cpf=cpf,
                phone=phone,
                license_number=cnh,
                license_category=cat,
                license_expiry=date(2027 + (i % 3), 1 + (i % 12), 10 + (i % 18)),
                status="ACTIVE",
                vehicle_id=v_id,
                notes="Motorista habilitado com certificacao MOPP e direcao defensiva",
            )
            db.session.add(d)
            drivers.append(d)
        db.session.commit()

        # 12 Manutencoes da Frota
        maintenances_data = [
            (vehicles[3].id, "PREVENTIVE", "Revisao geral de 100 mil km, troca de freios e embreagem", "Mecanica Diesel Truck Center", date(2026, 9, 1), date(2026, 9, 2), None, 112000, "4500.00", "OPEN"),
            (vehicles[0].id, "PREVENTIVE", "Troca de oleo de motor, filtro de combustivel e alinhamento", "Auto Centro Express Mooca", date(2026, 8, 10), date(2026, 8, 11), date(2026, 8, 11), 40000, "780.00", "COMPLETED"),
            (vehicles[10].id, "CORRECTIVE", "Substituicao do alternador e revisao da parte eletrica", "EletroDiesel Tatuape", date(2026, 9, 5), date(2026, 9, 6), None, 128000, "1850.00", "OPEN"),
            (vehicles[25].id, "PREVENTIVE", "Troca de lonas de freio, balanceamento e alinhamento laser", "Truck Center Dutra", date(2026, 9, 8), date(2026, 9, 9), None, 265000, "3200.00", "OPEN"),
            (vehicles[1].id, "PREVENTIVE", "Revisao dos 60 mil km e troca de pastilhas de freio", "Auto Truck Anchieta", date(2026, 7, 15), date(2026, 7, 16), date(2026, 7, 16), 60000, "1200.00", "COMPLETED"),
            (vehicles[5].id, "PREVENTIVE", "Troca do jogo de pneus dianteiros Michelin", "Pneus & Cia Bandeirantes", date(2026, 8, 20), date(2026, 8, 21), date(2026, 8, 21), 50000, "2400.00", "COMPLETED"),
            (vehicles[7].id, "PREVENTIVE", "Revisao de sistema de injecao eletronica Common Rail", "Scania Bosch Diesel Center", date(2026, 8, 28), date(2026, 8, 29), date(2026, 8, 29), 140000, "5800.00", "COMPLETED"),
            (vehicles[8].id, "CORRECTIVE", "Reparo no sistema pneumatico de suspensao a ar", "Volvo Truck Service Campinas", date(2026, 8, 2), date(2026, 8, 3), date(2026, 8, 3), 205000, "3600.00", "COMPLETED"),
            (vehicles[13].id, "PREVENTIVE", "Revisao e higienizacao do aparelho de refrigeracao Thermo King", "Polar Frigo Service", date(2026, 8, 14), date(2026, 8, 15), date(2026, 8, 15), 38000, "1450.00", "COMPLETED"),
            (vehicles[14].id, "PREVENTIVE", "Higienizacao do bau refrigerado e calibragem de termometros", "FrigoCenter SP", date(2026, 8, 25), date(2026, 8, 26), date(2026, 8, 26), 30000, "980.00", "COMPLETED"),
            (vehicles[16].id, "PREVENTIVE", "Troca de oleo de transmissao e diferencial pesado", "LubriTruck Castelo Branco", date(2026, 7, 30), date(2026, 7, 31), date(2026, 7, 31), 290000, "4100.00", "COMPLETED"),
            (vehicles[20].id, "PREVENTIVE", "Revisao geral de embreagem e suspensao dianteira", "Iveco Matriz Santo Andre", date(2026, 8, 18), date(2026, 8, 19), date(2026, 8, 19), 85000, "2750.00", "COMPLETED"),
        ]

        for v_id, m_type, desc, w_shop, op_at, sch_at, comp_at, mil, cost, st in maintenances_data:
            m = FleetMaintenance(
                vehicle_id=v_id,
                maintenance_type=m_type,
                description=desc,
                workshop=w_shop,
                opened_at=op_at,
                scheduled_at=sch_at,
                completed_at=comp_at,
                mileage=mil,
                cost=Decimal(cost),
                status=st,
                next_maintenance_at=op_at + timedelta(days=180),
                notes="Registro efetuado pelo modulo de gestao de frotas",
            )
            db.session.add(m)
        db.session.commit()

        # 25 Rotas de Entrega: 15 EM ANDAMENTO (IN_PROGRESS), 6 CONCLUIDAS (COMPLETED), 4 PENDENTES (PENDING)
        routes_specs = [
            ("Rota 01 - SP Capital Z.Sul & Centro", vehicles[0].id, drivers[0].id, date(2026, 9, 11), "IN_PROGRESS", "Entrega expressa corporativa na regiao da Paulista e Itaim"),
            ("Rota 02 - Campinas & R.Metropolitana", vehicles[1].id, drivers[1].id, date(2026, 9, 11), "IN_PROGRESS", "Abastecimento diario de centros logisticos e supermercados"),
            ("Rota 03 - Baixada Santista & Porto", vehicles[5].id, drivers[2].id, date(2026, 9, 11), "IN_PROGRESS", "Carga consolidada para distribuidoras portuarias"),
            ("Rota 04 - Vale do Paraiba & SJCampos", vehicles[6].id, drivers[3].id, date(2026, 9, 11), "IN_PROGRESS", "Entrega agendada de suprimentos de TI para industrias aeroespaciais"),
            ("Rota 05 - SP Zona Oeste & Alphaville", vehicles[7].id, drivers[4].id, date(2026, 9, 11), "IN_PROGRESS", "Distribuicao de lotes de equipamentos em escritorios executivos"),
            ("Rota 06 - Grande ABC & Diadema", vehicles[8].id, drivers[5].id, date(2026, 9, 11), "IN_PROGRESS", "Atendimento de clientes do setor metalurgico e automotivo"),
            ("Rota 07 - Sorocaba & Itu Industrial", vehicles[13].id, drivers[6].id, date(2026, 9, 11), "IN_PROGRESS", "Logistica refrigerada com monitoramento termico constante"),
            ("Rota 08 - Ribeirao Preto & Sertaozinho", vehicles[14].id, drivers[7].id, date(2026, 9, 11), "IN_PROGRESS", "Transporte rodoviario de carga perecivel fracionada"),
            ("Rota 09 - Rio de Janeiro Capital & Barra", vehicles[16].id, drivers[8].id, date(2026, 9, 11), "IN_PROGRESS", "Transferencia interestadual SP-RJ via Rodovia Presidente Dutra"),
            ("Rota 10 - Belo Horizonte & Contagem", vehicles[19].id, drivers[9].id, date(2026, 9, 11), "IN_PROGRESS", "Expedicao pesada via BR-381 Fernao Dias"),
            ("Rota 11 - Curitiba & R.Metropolitana", vehicles[20].id, drivers[10].id, date(2026, 9, 11), "IN_PROGRESS", "Linha direta de abastecimento regiao Sul BR-116"),
            ("Rota 12 - Joinville & Blumenau Textil", vehicles[22].id, drivers[11].id, date(2026, 9, 11), "IN_PROGRESS", "Carga paletizada de equipamentos para polos texteis"),
            ("Rota 13 - Porto Alegre & Canoas", vehicles[23].id, drivers[12].id, date(2026, 9, 11), "IN_PROGRESS", "Corredor logistico Mercosul com rastreamento por satelite"),
            ("Rota 14 - Brasilia DF & Anapolis GO", vehicles[26].id, drivers[13].id, date(2026, 9, 11), "IN_PROGRESS", "Entregas corporativas em orgaos governamentais e embaixadas"),
            ("Rota 15 - Salvador & Lauro de Freitas", vehicles[27].id, drivers[14].id, date(2026, 9, 11), "IN_PROGRESS", "Distribuicao regional nordeste polo Camaçari"),
            ("Rota 16 - Vitoria ES & Vila Velha", vehicles[2].id, drivers[15].id, date(2026, 9, 10), "COMPLETED", "Entrega urgente de equipamentos de rede finalizada"),
            ("Rota 17 - Piracicaba & Limeira", vehicles[4].id, drivers[16].id, date(2026, 9, 10), "COMPLETED", "Roteiro de distribuicao no interior de SP concluido"),
            ("Rota 18 - Marilia & Bauru", vehicles[9].id, drivers[17].id, date(2026, 9, 9), "COMPLETED", "Entregas no centro-oeste paulista com 100% de sucesso"),
            ("Rota 19 - Sao Jose do Rio Preto", vehicles[11].id, drivers[18].id, date(2026, 9, 8), "COMPLETED", "Viagem de entrega para centros medicos e farmaceuticos"),
            ("Rota 20 - Santos & Guaruja Litoral", vehicles[15].id, drivers[19].id, date(2026, 9, 8), "COMPLETED", "Entregas comerciais da linha litoranea finalizadas"),
            ("Rota 21 - Florianopolis & Sao Jose", vehicles[17].id, drivers[20].id, date(2026, 9, 7), "COMPLETED", "Expedicao Sul concluida sem extravios"),
            ("Rota 22 - Goiania & Aparecida de Goiania", vehicles[18].id, drivers[21].id, date(2026, 9, 12), "PENDING", "Saida programada para as 05h da manha"),
            ("Rota 23 - Recife & Jaboatao dos Guararapes", vehicles[21].id, drivers[22].id, date(2026, 9, 12), "PENDING", "Emissao de manifestos de carga eletronica (MDF-e) em andamento"),
            ("Rota 24 - Fortaleza & Maracanau", vehicles[24].id, drivers[23].id, date(2026, 9, 13), "PENDING", "Carregamento agendado na doca 4 do centro de distribuicao"),
            ("Rota 25 - Manaus & Polo Industrial", vehicles[28].id, drivers[24].id, date(2026, 9, 13), "PENDING", "Transporte multimodal rodo-fluvial"),
        ]

        routes = []
        for rname, vid, did, sdate, st, desc in routes_specs:
            r = Route(
                route_name=rname,
                vehicle_id=vid,
                driver_id=did,
                start_date=sdate,
                status=st,
                description=desc,
            )
            db.session.add(r)
            routes.append(r)
        db.session.commit()

        # 10 Devolucoes / Ocorrencias de Logistica Reversa
        returns_specs = [
            (sales[0].id, routes[0].id, drivers[0].id, vehicles[0].id, customers[0].name, date(2026, 9, 11), "CLIENT_ABSENT", "PENDING_RETURN", "", "Portaria fechada no momento da chegada. Reentrega sera agendada."),
            (sales[1].id, routes[1].id, drivers[1].id, vehicles[1].id, customers[1].name, date(2026, 9, 10), "ADDRESS_NOT_FOUND", "RETURNED_TO_STOCK", "Mercadoria conferida e reestocada no galpao central.", "Numero de galpao incorreto na nota fiscal."),
            (sales[2].id, routes[2].id, drivers[2].id, vehicles[5].id, customers[2].name, date(2026, 9, 9), "CARGO_DAMAGED", "PENDING_RETURN", "", "Caixa avariada durante o manuseio. Aguardando laudo do seguro."),
            (sales[3].id, routes[3].id, drivers[3].id, vehicles[6].id, customers[3].name, date(2026, 9, 8), "CLIENT_REFUSED", "RETURNED_TO_STOCK", "Produto devolvido ao almoxarifado sob protocolo 4819.", "Cliente alegou desacordo comercial no faturamento."),
            (sales[4].id, routes[4].id, drivers[4].id, vehicles[7].id, customers[4].name, date(2026, 9, 11), "ORDER_CANCELLED_IN_TRANSIT", "PENDING_RETURN", "", "Pedido cancelado pelo cliente enquanto a van estava em transito."),
            (sales[5].id, routes[5].id, drivers[5].id, vehicles[8].id, customers[5].name, date(2026, 9, 7), "CLIENT_ABSENT", "RETURNED_TO_STOCK", "Mercadoria retornada e agendada nova data com o comprador.", "Destinatario em viagem corporativa."),
            (sales[6].id, routes[6].id, drivers[6].id, vehicles[13].id, customers[6].name, date(2026, 9, 10), "TEMPERATURE_DEVIATION", "PENDING_RETURN", "", "Sensor frigorifico acusou variacao termica temporaria."),
            (sales[7].id, routes[7].id, drivers[7].id, vehicles[14].id, customers[7].name, date(2026, 9, 6), "ADDRESS_NOT_FOUND", "RETURNED_TO_STOCK", "Endereco corrigido no cadastro do cliente.", "Rua nao identificada no mapa GPS legado."),
            (sales[8].id, routes[8].id, drivers[8].id, vehicles[16].id, customers[8].name, date(2026, 9, 5), "CLIENT_ABSENT", "RESCHEDULED", "Reentrega programada com a portaria do condominio industrial.", "Horario de entrega fora do expediente da doca."),
            (sales[9].id, routes[9].id, drivers[9].id, vehicles[19].id, customers[9].name, date(2026, 9, 9), "CARGO_DAMAGED", "RETURNED_TO_STOCK", "Item substituido por nova unidade do estoque.", "Embalagem externa rasgada no transbordo."),
        ]

        for s_id, r_id, d_id, v_id, c_name, att_date, reason, st, act, notes in returns_specs:
            ret = DeliveryReturn(
                sale_id=s_id,
                route_id=r_id,
                driver_id=d_id,
                vehicle_id=v_id,
                customer_name=c_name,
                attempt_date=att_date,
                reason=reason,
                status=st,
                action_taken=act,
                notes=notes,
            )
            db.session.add(ret)
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
        print(f"- Veiculos Ativos/Operacionais: {FleetVehicle.query.filter(FleetVehicle.status.in_(['AVAILABLE', 'IN_USE'])).count()}")
        print(f"- Motoristas Qualificados: {Driver.query.count()}")
        print(f"- Rotas de Entrega: {Route.query.count()}")
        print(f"- Rotas em Andamento: {Route.query.filter_by(status='IN_PROGRESS').count()}")
        print(f"- Manutencoes de Frota: {FleetMaintenance.query.count()}")
        print(f"- Devolucoes / Logistica Reversa: {DeliveryReturn.query.count()}")
        print("--------------------------------------------------")


if __name__ == "__main__":
    seed_database()
