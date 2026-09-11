# app/validators.py

import re


def validate_cpf(cpf_str: str) -> bool:
    """
    Valida se a string fornecida é um CPF válido (11 dígitos numéricos e dígitos verificadores corretos).
    """
    digits = re.sub(r"\D", "", cpf_str or "")
    if len(digits) != 11:
        return False
    if digits == digits[0] * 11:
        return False

    # Primeiro dígito verificador
    s1 = sum(int(digits[i]) * (10 - i) for i in range(9))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    if d1 != int(digits[9]):
        return False

    # Segundo dígito verificador
    s2 = sum(int(digits[i]) * (11 - i) for i in range(10))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    if d2 != int(digits[10]):
        return False

    return True


def validate_cnpj(cnpj_str: str) -> bool:
    """
    Valida se a string fornecida é um CNPJ válido (14 dígitos numéricos e dígitos verificadores corretos).
    """
    digits = re.sub(r"\D", "", cnpj_str or "")
    if len(digits) != 14:
        return False
    if digits == digits[0] * 14:
        return False

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s1 = sum(int(digits[i]) * w1[i] for i in range(12))
    r1 = s1 % 11
    d1 = 0 if r1 < 2 else 11 - r1
    if d1 != int(digits[12]):
        return False

    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    s2 = sum(int(digits[i]) * w2[i] for i in range(13))
    r2 = s2 % 11
    d2 = 0 if r2 < 2 else 11 - r2
    if d2 != int(digits[13]):
        return False

    return True


def validate_document(doc_str: str) -> tuple[bool, str, str]:
    """
    Valida e formata CPF ou CNPJ.
    Retorna uma tupla: (is_valid, formatted_document, error_message)
    """
    if not doc_str:
        return False, "", "Documento (CPF ou CNPJ) é obrigatório."

    digits = re.sub(r"\D", "", doc_str)

    if len(digits) == 11:
        if validate_cpf(digits):
            formatted = f"{digits[:3]}.{digits[3:6]}.{digits[6:9]}-{digits[9:]}"
            return True, formatted, ""
        return False, "", "CPF inválido. Verifique os dígitos digitados."
    elif len(digits) == 14:
        if validate_cnpj(digits):
            formatted = f"{digits[:2]}.{digits[2:5]}.{digits[5:8]}/{digits[8:12]}-{digits[12:]}"
            return True, formatted, ""
        return False, "", "CNPJ inválido. Verifique os dígitos digitados."
    else:
        return False, "", "Documento inválido. Informe um CPF válido com 11 dígitos ou um CNPJ válido com 14 dígitos."


def validate_phone(phone_str: str) -> tuple[bool, str, str]:
    """
    Valida e formata número de telefone brasileiro (com DDD).
    Retorna uma tupla: (is_valid, formatted_phone, error_message)
    """
    if not phone_str:
        return True, "", ""

    digits = re.sub(r"\D", "", phone_str)
    if not digits:
        return True, "", ""

    if len(digits) not in (10, 11):
        return False, "", "Telefone inválido. Informe o DDD e o número completo (10 ou 11 dígitos)."

    ddd = int(digits[:2])
    if ddd < 11 or ddd > 99:
        return False, "", "Telefone inválido. O DDD informado não é válido."

    if len(digits) == 10:
        formatted = f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    else:
        formatted = f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"

    return True, formatted, ""
