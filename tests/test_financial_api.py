from decimal import Decimal
from datetime import date
import pytest
from app import db
from app.financial_models import FinancialCategory, FinancialTransaction, PayrollExpense


def test_financial_categories(client):
    response = client.get("/api/financial/categories")
    assert response.status_code == 200
    data = response.get_json()
    assert len(data) >= 6

    res = client.post("/api/financial/categories", json={
        "name": "Marketing & Publicidade",
        "category_type": "VARIABLE_COST",
        "description": "Anúncios e Campanhas"
    })
    assert res.status_code == 201
    assert res.get_json()["name"] == "Marketing & Publicidade"


def test_financial_transactions(client, app):
    with app.app_context():
        cat = FinancialCategory(name="Energia Elétrica Teste", category_type="FIXED_COST")
        db.session.add(cat)
        db.session.commit()
        cat_id = cat.id

    res = client.post("/api/financial/transactions", json={
        "description": "Conta de Luz Matriz",
        "amount": "450.00",
        "transaction_type": "EXPENSE",
        "status": "PAID",
        "category_id": cat_id,
        "due_date": "2026-09-10"
    })
    assert res.status_code == 201
    trans_id = res.get_json()["id"]

    res_list = client.get("/api/financial/transactions")
    assert res_list.status_code == 200
    assert len(res_list.get_json()) >= 1

    res_upd = client.put(f"/api/financial/transactions/{trans_id}", json={
        "status": "PAID",
        "notes": "Pago via PIX"
    })
    assert res_upd.status_code == 200
    assert res_upd.get_json()["status"] == "PAID"


def test_payroll_expenses(client):
    res = client.post("/api/financial/payroll", json={
        "employee_name": "Fernanda Santos",
        "role": "Engenheira de Software",
        "base_salary": "8500.00",
        "charges_amount": "2300.00",
        "benefits_amount": "1200.00"
    })
    assert res.status_code == 201
    data = res.get_json()
    assert data["employee_name"] == "Fernanda Santos"
    assert Decimal(data["total_cost"]) == Decimal("12000.00")

    res_list = client.get("/api/financial/payroll")
    assert res_list.status_code == 200
    assert len(res_list.get_json()) >= 1


def test_financial_summary(client):
    res = client.get("/api/financial/summary")
    assert res.status_code == 200
    data = res.get_json()
    assert "total_revenue" in data
    assert "total_expenses" in data
    assert "total_payroll" in data
    assert "net_result" in data
