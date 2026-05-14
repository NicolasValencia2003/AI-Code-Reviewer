"""
Archivo de ejemplo con errores intencionales para demostrar el AI Code Reviewer.
NO usar este código en producción.
"""
import os
import sqlite3


# ── OWASP A02: Credenciales hardcodeadas ─────────────────────────────────────
password = "super_secret_123"
api_key = "sk-abc123xyz789realtoken"
db_token = "prod-db-token-hardcoded"


# ── OWASP A03: SQL Injection por concatenación ────────────────────────────────
def get_user_by_id(user_id):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE id = " + user_id)
    row = cursor.fetchone()
    conn.close()
    return row


# ── OWASP A03: SQL Injection por f-string ─────────────────────────────────────
def get_user_by_email(email):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    cursor.execute(f"SELECT * FROM users WHERE email = '{email}'")
    result = cursor.fetchall()
    conn.close()
    return result


# ── OWASP A03: Command injection ─────────────────────────────────────────────
def generate_thumbnail(filename):
    os.system("convert " + filename + " -resize 100x100 thumb.png")


# ── OWASP A03: eval() con input dinámico ─────────────────────────────────────
def calculate_formula(expression):
    result = eval(expression)
    return result


# ── Clean Code: Función demasiado larga + nombres de 1 letra + anidamiento profundo ──
def validate_and_process_user_data(u, p, e, r, a):
    if u:
        if len(u) > 3:
            if p:
                if len(p) > 5:
                    if "@" in e:
                        if r in ["admin", "user", "guest"]:
                            if a:
                                x = u.strip()
                                y = p.strip()
                                z = e.strip()
                                return {
                                    "username": x,
                                    "password": y,
                                    "email": z,
                                    "role": r,
                                    "active": a,
                                }
                            else:
                                return None
                        else:
                            return None
                    else:
                        return None
                else:
                    return None
            else:
                return None
        else:
            return None
    else:
        return None


# ── Complejidad ciclomática alta ──────────────────────────────────────────────
def calculate_discount(price, user_type, quantity, is_member, coupon, region, day_of_week):
    d = 0
    if user_type == "premium":
        d += 10
    elif user_type == "vip":
        d += 20
    elif user_type == "gold":
        d += 15
    if quantity > 10:
        d += 5
    elif quantity > 5:
        d += 3
    if is_member:
        d += 2
    if coupon == "SAVE10":
        d += 10
    elif coupon == "SAVE20":
        d += 20
    elif coupon == "SAVE30":
        d += 30
    if region == "south":
        d += 1
    elif region == "north":
        d += 2
    elif region == "east":
        d += 1
    if day_of_week in ["Saturday", "Sunday"]:
        d += 5
    if d > 50:
        d = 50
    return price * (1 - d / 100)
