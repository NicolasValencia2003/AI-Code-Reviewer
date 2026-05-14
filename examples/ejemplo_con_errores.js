/**
 * Archivo de ejemplo con errores intencionales para demostrar el AI Code Reviewer.
 * NO usar este código en producción.
 */

// ── OWASP A02: Credenciales hardcodeadas ─────────────────────────────────────
const apiKey = "sk-abc123xyz789realtoken";
const password = "hardcoded_password_456";

// ── OWASP A03: SQL Injection con template literal ─────────────────────────────
async function getUserByUsername(username) {
    const query = `SELECT * FROM users WHERE username = '${username}'`;
    const result = await db.query(query);
    return result;
}

// ── OWASP A03: SQL Injection con concatenación ────────────────────────────────
function getProductById(id) {
    const query = "SELECT * FROM products WHERE id = " + id;
    return db.execute(query);
}

// ── OWASP A03: eval() con input del usuario ───────────────────────────────────
function calculateFormula(userInput) {
    return eval(userInput);
}

// ── OWASP A07: XSS via innerHTML ─────────────────────────────────────────────
function renderUserProfile(userData) {
    const container = document.getElementById("profile");
    container.innerHTML = "<h2>" + userData.name + "</h2><p>" + userData.bio + "</p>";
}

// ── Clean Code: Función larga + variables de 1 letra + complejidad alta ───────
function processOrder(o, u, p, d) {
    var x = 0;
    var y = 0;
    var z = null;

    if (o.items && o.items.length > 0) {
        for (var i = 0; i < o.items.length; i++) {
            var item = o.items[i];
            if (item.quantity > 0) {
                if (item.price > 0) {
                    if (item.available) {
                        x += item.quantity * item.price;
                        y += item.quantity;
                    }
                }
            }
        }
    }

    if (u && u.isPremium) {
        x = x * 0.9;
    } else if (u && u.isVip) {
        x = x * 0.8;
    } else if (u && u.isGold) {
        x = x * 0.85;
    }

    if (d && d.code === "SAVE10") {
        x = x * 0.9;
    } else if (d && d.code === "SAVE20") {
        x = x * 0.8;
    } else if (d && d.code === "SAVE30") {
        x = x * 0.7;
    }

    if (p === "credit_card") {
        z = "CC";
    } else if (p === "paypal") {
        z = "PP";
    } else if (p === "crypto") {
        z = "CR";
    } else {
        z = "CASH";
    }

    return {
        total: x,
        itemCount: y,
        paymentMethod: z,
        status: "processed"
    };
}
