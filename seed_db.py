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
    base = f'{n:09d}'
    digits = [int(c) for c in base]
    s1 = sum(d * (10 - i) for i, d in enumerate(digits))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    digits.append(d1)
    s2 = sum(d * (11 - i) for i, d in enumerate(digits))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    digits.append(d2)
    s = ''.join(str(d) for d in digits)
    return f'{s[:3]}.{s[3:6]}.{s[6:9]}-{s[9:]}'


def gen_cnpj(n: int) -> str:
    base = f'{n:08d}0001'
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
    s = ''.join(str(d) for d in digits)
    return f'{s[:2]}.{s[2:5]}.{s[5:8]}/{s[8:12]}-{s[12:]}'


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
    return f'({ddd}) {part1:05d}-{part2:04d}'


def seed_database():
    app = create_app()

    with app.app_context():
        print('[1/7] Limpando registros operacionais do banco de dados...')
        is_mysql = 'mysql' in str(db.engine.url)
        if is_mysql:
            db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 0;'))

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
                db.session.execute(db.text('SET FOREIGN_KEY_CHECKS = 1;'))
                db.session.commit()

        print('[2/7] Cadastrando 20 Produtos em Estoque...')
        products_data = [
            ('PROD-001', 'Notebook Pro15 Intel i7 16GB', 'Laptop de alta performance para uso corporativo', '4500.00', 25, 5),
            ('PROD-002', 'Monitor LED 27 IPS UltraWide', 'Monitor para produtividade e design', '1350.00', 40, 8),
            ('PROD-003', 'Cadeira Ergonomica Executive Pro', 'Cadeira ajustavel NR17 com apoio lombar', '980.00', 18, 5),
            ('PROD-004', 'Teclado Mecanico RGB Wireless', 'Teclado silencioso para escritorio', '320.00', 60, 10),
            ('PROD-005', 'Mouse Ergologico Vertical Bluetooth', 'Mouse ergonomico anti-LER', '180.00', 45, 10),
            ('PROD-006', 'Impressora Multifuncional Laser Tank', 'Impressora de grande volume de impressao', '2100.00', 10, 3),
            ('PROD-007', 'Mesa Corporativa L 160x140cm', 'Mesa em MDF resistente com passa cabos', '750.00', 15, 3),
            ('PROD-008', 'Nobreak Senoidal 1500VA Bivolt', 'Protecao de energia para servidores e estacoes', '1150.00', 14, 4),
            ('PROD-009', 'Switch Gigabit 24 Portas Rack', 'Switch gerenciavel para infraestrutura', '890.00', 20, 5),
            ('PROD-010', 'Cabo de Rede Cat6 305m', 'Caixa de cabo homologado ANATEL', '420.00', 35, 6),
            ('PROD-011', 'Webcam 4K UltraHD com Microfone', 'Camera para videoconferencia com tampa de privacidade', '450.00', 4, 6),
            ('PROD-012', 'Headset Corporate USB Noise Canceling', 'Fone de ouvido profissional com cancelamento de ruido', '280.00', 3, 6),
            ('PROD-013', 'HD Externo 4TB USB 3.2', 'Disco rigido portatil reforcado', '520.00', 1, 5),
            ('PROD-014', 'Filtro de Linha Dimerizado 8 Tomadas', 'Regua de tomadas com protecao de surto', '95.00', 75, 15),
            ('PROD-015', 'Roteador Wi-Fi 6 Mesh Tri-Band', 'Roteador empresarial de alta velocidade', '680.00', 22, 5),
            ('PROD-016', 'Suporte Duplo para Monitores Articulado', 'Suporte a gas para 2 monitores ate 32 pol', '240.00', 32, 6),
            ('PROD-017', 'Gabinete Mid Tower ATX Ventilado', 'Gabinete corporativo silencioso', '310.00', 12, 4),
            ('PROD-018', 'SSD NVMe 1TB PCIe 4.0', 'Armazenamento ultra-rapido para PCs e servidores', '410.00', 2, 8),
            ('PROD-019', 'Projetor Full HD 4000 Lumens', 'Projetor para salas de reuniao e treinamentos', '3200.00', 5, 2),
            ('PROD-020', 'Kit Manutencao e Ferramentas TI', 'Maleta com alicates, testador de cabo e chaves', '190.00', 16, 4),
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

        print('[3/7] Cadastrando 500 Clientes (250 B2B e 250 B2C) e 15 Fornecedores...')
        b2b_prefixes = [
            'Alfa', 'Beta', 'Delta', 'Sigma', 'Prime', 'Elite', 'Nexus', 'Vanguard', 'Global', 'Nacional',
            'Brasil', 'Master', 'Solucoes', 'Alianca', 'Uniao', 'Horizonte', 'Metropole', 'Pinnacle', 'Atlas', 'Nova',
            'Pro', 'Tech', 'Apex', 'Omni', 'Inova'
        ]
        b2b_sectors = [
            'Tecnologia', 'Logistica', 'Comercio', 'Industria', 'Alimentos', 'Consultoria', 'Distribuicao',
            'Engenharia', 'Servicos', 'Sistemas', 'Transportes', 'Atacado', 'Varejo', 'Farmaceutica', 'Quimica',
            'Metalurgica', 'Embalagens', 'Textil', 'Energia', 'Telecom'
        ]
        b2b_suffixes = [
            'Ltda', 'S.A.', 'EIRELI', 'do Brasil', 'Corporativa', 'Express', 'Brasil Ltda', 'Comercial Ltda',
            'Servicos Integrados', 'Participacoes'
        ]

        first_names = [
            'Ana', 'Bruno', 'Carlos', 'Daniela', 'Eduardo', 'Fernanda', 'Gabriel', 'Helena', 'Igor', 'Juliana',
            'Lucas', 'Mariana', 'Nelson', 'Olivia', 'Pedro', 'Rafaela', 'Rodrigo', 'Sofia', 'Thiago', 'Vanessa',
            'Marcio', 'Aline', 'Felipe', 'Beatriz', 'Rafael'
        ]
        last_names = [
            'Silva', 'Santos', 'Oliveira', 'Souza', 'Rodrigues', 'Ferreira', 'Alves', 'Pereira', 'Lima', 'Gomes',
            'Costa', 'Ribeiro', 'Martins', 'Carvalho', 'Almeida', 'Lopes', 'Soares', 'Fernandes', 'Vieira', 'Barbosa',
            'Rocha', 'Dias', 'Nascimento', 'Andrade', 'Moreira'
        ]

        customers = []

        # 250 Clientes B2B
        for i in range(1, 251):
            pfx = b2b_prefixes[(i * 3) % len(b2b_prefixes)]
            sct = b2b_sectors[(i * 7) % len(b2b_sectors)]
            sfx = b2b_suffixes[(i * 5) % len(b2b_suffixes)]
            name = f'{pfx} {sct} {sfx}'
            doc = gen_cnpj(11000000 + i)
            clean_slug = f'{pfx.lower()}{sct.lower()}{i}'
            email = f'contato@{clean_slug}.com.br'
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
            name = f'{fn} {ln1} {ln2}'
            doc = gen_cpf(200000000 + i)
            email = f'{fn.lower()}.{ln1.lower()}.{i}@emailbrasil.com'
            phone = gen_phone(250 + i)
            is_act = i % 20 != 0

            c = Customer(name=name, document=doc, email=email, phone=phone, is_active=is_act)
            db.session.add(c)
            customers.append(c)

        db.session.flush()

        # 15 Fornecedores com CNPJs validos
        suppliers_raw = [
            ('Distribuidora Tech Master Brasil', '(11) 4004-1000'),
            ('Dell Computadores do Brasil Ltda', '(11) 3718-2000'),
            ('Moveis Corporativos Flexform', '(11) 4689-9000'),
            ('Kalunga Comercio e Suprimentos', '(11) 3346-9999'),
            ('Giga Security & Networking', '(11) 2107-8888'),
            ('Auto Pecas & Oficina Central Frota', '(11) 3838-2200'),
            ('Posto de Combustiveis PetroShell S.A.', '(11) 3232-1100'),
            ('Imobiliaria & Seguros Patrimonial', '(11) 3100-5000'),
            ('EletroCabos do Brasil Industrial', '(19) 3456-1122'),
            ('Logistica Aerea & Cargas Rapidas', '(11) 2445-3344'),
            ('Papelaria & Insumos Empresariais', '(21) 2233-4455'),
            ('Sistemas de Refrigeracao Polar', '(41) 3322-5566'),
            ('Metalurgica Central Estruturas', '(31) 3211-7788'),
            ('Provedor Cloud & DataCenter Brasil', '(11) 4123-9988'),
            ('Equipamentos Medicos & Seguranca', '(11) 3088-7711'),
        ]

        suppliers = []
        for idx, (s_name, s_phone) in enumerate(suppliers_raw, start=1):
            s_doc = gen_cnpj(55000000 + idx)
            slug = s_name.split()[0].lower()
            s_email = f'contato@{slug}{idx}.com.br'
            s = Supplier(name=s_name, document=s_doc, email=s_email, phone=s_phone, is_active=True)
            db.session.add(s)
            suppliers.append(s)

        db.session.commit()

        print('[4/7] Cadastrando Equipe de 10 Funcionarios na Folha de Pagamento...')
        employees_data = [
            ('Fernanda Santos', 'Gerente Geral / CEO', '12500.00', '3400.00', '1500.00', 'PAID'),
            ('Lucas Gabriel Silva', 'Desenvolvedor Full Stack Senior', '9500.00', '2600.00', '1200.00', 'PAID'),
            ('Amanda Rodrigues', 'Analista Financeiro Pleno', '5800.00', '1600.00', '900.00', 'PENDING'),
            ('Rodrigo Barbosa', 'Supervisor de Vendas Comercial', '6500.00', '1800.00', '950.00', 'PAID'),
            ('Camila Alcantara', 'Assistente de Suporte e Atendimento', '3200.00', '880.00', '650.00', 'PENDING'),
            ('Marcelo Costa', 'Motorista de Frota Senior', '3800.00', '1050.00', '700.00', 'PAID'),
            ('Robson Oliveira', 'Motorista Entregador', '3400.00', '940.00', '650.00', 'PENDING'),
            ('Diego Alves', 'Encarregado de Estoque e Almoxarifado', '3600.00', '990.00', '680.00', 'PAID'),
            ('Patricia Lima', 'Auxiliar de Logistica', '2800.00', '770.00', '600.00', 'PENDING'),
            ('Thiago Martins', 'Tecnico de Manutencao TI', '4200.00', '1150.00', '750.00', 'PAID'),
        ]
        for emp, role, base, charges, ben, st in employees_data:
            p = PayrollExpense(
                employee_name=emp,
                role=role,
                base_salary=Decimal(base),
                charges_amount=Decimal(charges),
                benefits_amount=Decimal(ben),
                status=st,
                notes='Folha de pagamento mensal corporativa',
            )
            db.session.add(p)
        db.session.commit()

        print('[5/7] Cadastrando Categorias e Lancamentos Financeiros (DRE)...')
        cat_fixa = FinancialCategory(name='Custos Fixos & Sede', category_type='FIXED_COST', description='Aluguel, luz, agua e internet')
        cat_var = FinancialCategory(name='Insumos & Fretes', category_type='VARIABLE_COST', description='Mercadorias e fretes')
        cat_pess = FinancialCategory(name='Folha de Pagamento', category_type='PAYROLL', description='Salarios e encargos')
        cat_rec = FinancialCategory(name='Receitas de Vendas', category_type='REVENUE', description='Faturamento com vendas de produtos')

        db.session.add_all([cat_fixa, cat_var, cat_pess, cat_rec])
        db.session.commit()

        transactions_data = [
            ('Aluguel Sede Corporativa Av. Paulista', '8500.00', 'EXPENSE', 'PAID', cat_fixa.id, date(2026, 9, 1), date(2026, 9, 1)),
            ('Energia Eletrica Matriz', '1850.00', 'EXPENSE', 'PENDING', cat_fixa.id, date(2026, 9, 15), None),
            ('Internet Fibra Optica 1Gbps Dedicado', '890.00', 'EXPENSE', 'PAID', cat_fixa.id, date(2026, 9, 5), date(2026, 9, 5)),
            ('Servicos Cloud & Infraestrutura GCP', '3400.00', 'EXPENSE', 'PAID', cat_fixa.id, date(2026, 9, 10), date(2026, 9, 10)),
            ('Seguro Frota de Veiculos', '2100.00', 'EXPENSE', 'PENDING', cat_fixa.id, date(2026, 9, 20), None),
            ('Compra de Lote Hardware Corporativo', '28000.00', 'EXPENSE', 'PAID', cat_var.id, date(2026, 8, 25), date(2026, 8, 25)),
            ('Faturamento Contrato B2B Alfa Tecnologia', '24500.00', 'REVENUE', 'PAID', cat_rec.id, date(2026, 9, 2), date(2026, 9, 2)),
            ('Faturamento Venda Delta Logistica', '18200.00', 'REVENUE', 'PAID', cat_rec.id, date(2026, 9, 4), date(2026, 9, 4)),
            ('Faturamento Venda Supermercados Cidade', '12400.00', 'REVENUE', 'PENDING', cat_rec.id, date(2026, 9, 18), None),
            ('Faturamento Venda Hospital Vida', '31200.00', 'REVENUE', 'PAID', cat_rec.id, date(2026, 9, 8), date(2026, 9, 8)),
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
                notes='Lancamento automatico de sistema',
            )
            db.session.add(t)
        db.session.commit()

        print('[6/7] Cadastrando 60 Pedidos de Venda e 15 Compras de Suprimentos...')
        sales = []
        for i in range(1, 61):
            cust = customers[(i * 7) % len(customers)]
            st = 'CONFIRMED' if i <= 45 else ('OPEN' if i <= 55 else 'CANCELLED')
            sale = Sale(customer_id=cust.id, status=st, total_amount=Decimal('0.00'))
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

            if sale.status == 'CONFIRMED':
                m1 = StockMovement(
                    product_id=p1.id,
                    sale_id=sale.id,
                    movement_type='OUT',
                    quantity=qty1,
                    stock_before=p1.stock_quantity + qty1,
                    stock_after=p1.stock_quantity,
                )
                m2 = StockMovement(
                    product_id=p2.id,
                    sale_id=sale.id,
                    movement_type='OUT',
                    quantity=qty2,
                    stock_before=p2.stock_quantity + qty2,
                    stock_after=p2.stock_quantity,
                )
                db.session.add_all([m1, m2])

                inv_status = 'ISSUED' if idx <= 35 else 'PENDING_EMISSION'
                uf, yymm, cnpj = '35', '2609', '11222333000181'
                num = f'{sale.id:09d}'
                rnd = f'{abs(hash(sale.id)) % 100000000:09d}'[:9]
                key = f'{uf}{yymm}{cnpj}55001{num}{rnd}'[:44]

                inv = Invoice(
                    sale_id=sale.id,
                    customer_id=sale.customer_id,
                    invoice_number=f'NF-e {sale.id:06d}',
                    access_key=key if inv_status == 'ISSUED' else None,
                    status=inv_status,
                    sefaz_status_code='100' if inv_status == 'ISSUED' else None,
                    sefaz_message='Autorizado o uso da NF-e (Ambiente SEFAZ Nuvem)' if inv_status == 'ISSUED' else None,
                    issued_at=datetime.now(timezone.utc) if inv_status == 'ISSUED' else None,
                )
                db.session.add(inv)
        db.session.commit()

        for i in range(1, 16):
            supp = suppliers[(i - 1) % len(suppliers)]
            st = 'RECEIVED' if i <= 11 else 'OPEN'
            purchase = Purchase(supplier_id=supp.id, status=st, total_amount=Decimal('0.00'))
            db.session.add(purchase)
            db.session.commit()

            p = products[i % len(products)]
            qty = random.randint(5, 15)
            cost = Decimal(str(p.price)) * Decimal('0.65')

            p_item = PurchaseItem(purchase_id=purchase.id, product_id=p.id, quantity=qty, unit_cost=cost)
            db.session.add(p_item)
            purchase.total_amount = cost * qty

            if st == 'RECEIVED':
                purchase.received_at = datetime.now(timezone.utc) - timedelta(days=i * 2)
                m = StockMovement(
                    product_id=p.id,
                    purchase_id=purchase.id,
                    movement_type='IN',
                    quantity=qty,
                    stock_before=p.stock_quantity - qty if p.stock_quantity >= qty else 0,
                    stock_after=p.stock_quantity,
                )
                db.session.add(m)
        db.session.commit()

        print('[7/7] Cadastrando Frota, Motoristas, Manutencoes, Rotas e Devolucoes...')
        vehicles_data = [
            ('ABC-1D23', 'Van Carga Express', 'Mercedes-Benz', 'Sprinter 416 CDi', 2023, '1800.00', 42500, 'IN_USE'),
            ('BCD-2E34', 'Caminhao Bau VUC', 'Volkswagen', 'Delivery Express 4.150', 2022, '3500.00', 68200, 'IN_USE'),
            ('CDE-3F45', 'Furgao Utilitario', 'Fiat', 'Fiorino Endurance 1.4', 2024, '650.00', 18400, 'AVAILABLE'),
            ('DEF-4G56', 'Caminhao Pesado Sider', 'Mercedes-Benz', 'Atego 1719', 2021, '8500.00', 112000, 'MAINTENANCE'),
            ('EFG-5H67', 'Van Refrigerada', 'Peugeot', 'Expert Refrigerada', 2023, '1400.00', 35100, 'AVAILABLE'),
            ('FGH-6I78', 'Furgao Medio Carga', 'Renault', 'Master L1H1', 2022, '1500.00', 54800, 'IN_USE'),
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
                notes='Veiculo rastreado por GPS em tempo real',
            )
            db.session.add(v)
            vehicles.append(v)
        db.session.commit()

        drivers_data = [
            ('Marcelo Costa', gen_cpf(300000001), '(11) 98888-1111', '99887766554', 'D', date(2028, 5, 20), 'ACTIVE', vehicles[0].id),
            ('Robson Oliveira', gen_cpf(300000002), '(11) 97777-2222', '88776655443', 'C', date(2027, 8, 15), 'ACTIVE', vehicles[1].id),
            ('Alexandre Souza', gen_cpf(300000003), '(11) 96666-3333', '77665544332', 'B', date(2026, 11, 10), 'ACTIVE', vehicles[2].id),
            ('Fernando Henrique', gen_cpf(300000004), '(19) 95555-4444', '66554433221', 'E', date(2029, 3, 30), 'ACTIVE', vehicles[3].id),
            ('Gabriel Ribeiro', gen_cpf(300000005), '(11) 94444-5555', '55443322110', 'D', date(2028, 1, 12), 'ACTIVE', vehicles[4].id),
            ('Eduardo Paes', gen_cpf(300000006), '(21) 93333-6666', '44332211009', 'C', date(2027, 9, 25), 'ACTIVE', vehicles[5].id),
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
                notes='Motorista qualificado em direcao defensiva',
            )
            db.session.add(d)
            drivers.append(d)
        db.session.commit()

        maint1 = FleetMaintenance(
            vehicle_id=vehicles[3].id,
            maintenance_type='PREVENTIVE',
            description='Revisao geral de 100 mil km, troca de freios e embreagem',
            workshop='Mecanica & Truck Center Diesel',
            opened_at=date(2026, 9, 1),
            scheduled_at=date(2026, 9, 2),
            mileage=112000,
            cost=Decimal('4500.00'),
            status='OPEN',
            next_maintenance_at=date(2027, 3, 1),
            notes='Aguardando peca de reposicao do cambio',
        )
        maint2 = FleetMaintenance(
            vehicle_id=vehicles[0].id,
            maintenance_type='PREVENTIVE',
            description='Troca de oleo de motor, filtro de combustivel e alinhamento',
            workshop='Auto Centro Express Mooca',
            opened_at=date(2026, 8, 10),
            completed_at=date(2026, 8, 11),
            mileage=40000,
            cost=Decimal('780.00'),
            status='COMPLETED',
            next_maintenance_at=date(2027, 2, 10),
            notes='Revisao preventiva realizada dentro do prazo',
        )
        db.session.add_all([maint1, maint2])

        routes_data = [
            ('Rota 01 - SP Capital Z.Sul & Centro', vehicles[0].id, drivers[0].id, date(2026, 9, 11), 'IN_PROGRESS', 'Entrega de lotes eletronicos corporativos'),
            ('Rota 02 - Campinas & R.Metropolitana', vehicles[1].id, drivers[1].id, date(2026, 9, 11), 'IN_PROGRESS', 'Abastecimento de redes de supermercado'),
            ('Rota 03 - Baixada Santista & Litoral', vehicles[2].id, drivers[2].id, date(2026, 9, 10), 'COMPLETED', 'Entrega urgente de equipamentos de TI'),
            ('Rota 04 - Vale do Paraiba & SJCampos', vehicles[4].id, drivers[4].id, date(2026, 9, 12), 'PENDING', 'Logistica programada para hospitais'),
            ('Rota 05 - SP Zona Oeste & Alphaville', vehicles[5].id, drivers[5].id, date(2026, 9, 11), 'IN_PROGRESS', 'Distribuicao em escritorios corporativos'),
        ]
        routes = []
        for rname, vid, did, sdate, st, desc in routes_data:
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

        ret1 = DeliveryReturn(
            sale_id=sales[0].id,
            route_id=routes[0].id,
            driver_id=drivers[0].id,
            vehicle_id=vehicles[0].id,
            customer_name=customers[0].name,
            attempt_date=date(2026, 9, 11),
            reason='CLIENT_ABSENT',
            status='PENDING_RETURN',
            action_taken='',
            notes='Portaria fechada no momento da chegada. Reentrega sera agendada.',
        )
        ret2 = DeliveryReturn(
            sale_id=sales[1].id,
            route_id=routes[1].id,
            driver_id=drivers[1].id,
            vehicle_id=vehicles[1].id,
            customer_name=customers[1].name,
            attempt_date=date(2026, 9, 10),
            reason='ADDRESS_NOT_FOUND',
            status='RETURNED_TO_STOCK',
            action_taken='Mercadoria conferida e reestocada no galpao central.',
            notes='Numero de galpao incorreto na nota fiscal.',
        )
        ret3 = DeliveryReturn(
            sale_id=sales[2].id,
            route_id=routes[2].id,
            driver_id=drivers[2].id,
            vehicle_id=vehicles[2].id,
            customer_name=customers[2].name,
            attempt_date=date(2026, 9, 9),
            reason='CARGO_DAMAGED',
            status='PENDING_RETURN',
            action_taken='',
            notes='Caixa avariada durante o manuseio. Aguardando laudo do seguro.',
        )
        db.session.add_all([ret1, ret2, ret3])
        db.session.commit()

        print('[OK] POVOAMENTO CONCLUIDO COM SUCESSO!')
        print('--------------------------------------------------')
        print(f'- Produtos cadastrados: {Product.query.count()}')
        print(f'- Clientes cadastrados: {Customer.query.count()}')
        print(f'- Fornecedores cadastrados: {Supplier.query.count()}')
        print(f'- Equipe / Folha de Pagamento: {PayrollExpense.query.count()} funcionarios')
        print(f'- Lancamentos Financeiros (DRE): {FinancialTransaction.query.count()}')
        print(f'- Vendas Registradas: {Sale.query.count()}')
        print(f'- Compras de Suprimentos: {Purchase.query.count()}')
        print(f'- Notas Fiscais (NF-e SEFAZ): {Invoice.query.count()}')
        print(f'- Veiculos de Frota: {FleetVehicle.query.count()}')
        print(f'- Motoristas: {Driver.query.count()}')
        print(f'- Rotas de Entrega: {Route.query.count()}')
        print(f'- Devolucoes / Logistica Reversa: {DeliveryReturn.query.count()}')
        print('--------------------------------------------------')


if __name__ == '__main__':
    seed_database()
