"""Self-contained sample month (2026-01) for a small Greek company — a mix of
the documents a real business receives, so Archon can show classification +
correlation across types, not just one trick.

A coherent, balanced set:
  · 1 sales invoice      (revenue 5,000 + VAT 1,200 = 6,200)
  · 1 purchase invoice   (opex 1,000 + VAT 240 = 1,240)
  · 3 bank transactions  (customer pays 6,200 · we pay vendor 1,240 · payroll net 14,350)
  · 1 payroll run        (gross 23,100 → net 14,350, employer cost 28,249)

Payroll figures are realistic Greek bookkeeping (NOT a "28% gap"):
  gross 23,100  − employee EFKA 3,204 − withheld tax 5,546 = net 14,350
  employer cost = gross 23,100 + employer EFKA 5,149       = 28,249
Only 14,350 leaves the account to employees this month; 13,899 of EFKA+tax is a
payable that settles later — the real, honest cash-timing insight.
"""

SALES_INVOICE = """\
ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ (Sales Invoice)
Αριθμός: INV-2026-014
Ημερομηνία: 12/01/2026
Πελάτης: ACME RETAIL A.E.
Καθαρή αξία: 5.000,00 EUR
ΦΠΑ 24%: 1.200,00 EUR
Σύνολο: 6.200,00 EUR
"""

PURCHASE_INVOICE = """\
ΤΙΜΟΛΟΓΙΟ ΑΓΟΡΑΣ (Purchase Invoice)
Αριθμός: SUP-8841
Ημερομηνία: 08/01/2026
Προμηθευτής: CLOUD VENDOR LTD
Καθαρή αξία: 1.000,00 EUR
ΦΠΑ 24%: 240,00 EUR
Σύνολο: 1.240,00 EUR
"""

BANK_IN = """\
ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ (Bank Transaction)
Ημερομηνία: 20/01/2026
Κατεύθυνση: Εισερχόμενη (in)
Ποσό: 6.200,00 EUR
Αιτιολογία: INV-2026-014
"""

BANK_OUT_VENDOR = """\
ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ (Bank Transaction)
Ημερομηνία: 15/01/2026
Κατεύθυνση: Εξερχόμενη (out)
Ποσό: 1.240,00 EUR
Αιτιολογία: SUP-8841
"""

BANK_OUT_PAYROLL = """\
ΚΙΝΗΣΗ ΛΟΓΑΡΙΑΣΜΟΥ (Bank Transaction)
Ημερομηνία: 31/01/2026
Κατεύθυνση: Εξερχόμενη (out)
Ποσό: 14.350,00 EUR
Αιτιολογία: ΜΙΣΘΟΔΟΣΙΑ ΙΑΝΟΥΑΡΙΟΥ
"""

PAYROLL = """\
ΜΙΣΘΟΔΟΣΙΑ (Payroll Run)
Περίοδος: 01/2026
Εργαζόμενοι: 2
Μικτές αποδοχές: 23.100,00 EUR
Καθαρές πληρωτέες: 14.350,00 EUR
Εργοδοτικές εισφορές ΕΦΚΑ: 5.149,00 EUR
Παρακρατούμενος φόρος (ΦΜΥ): 5.546,00 EUR
Συνολικό εργοδοτικό κόστος: 28.249,00 EUR
"""

PERIOD = "2026-01"

SAMPLE_DOCS: dict[str, str] = {
    "sales_invoice_INV-2026-014.txt": SALES_INVOICE,
    "purchase_invoice_SUP-8841.txt": PURCHASE_INVOICE,
    "bank_in_INV-2026-014.txt": BANK_IN,
    "bank_out_SUP-8841.txt": BANK_OUT_VENDOR,
    "bank_out_payroll.txt": BANK_OUT_PAYROLL,
    "payroll_2026-01.txt": PAYROLL,
}

GROUND_TRUTH = {
    "period": PERIOD,
    "revenue": 5000.00,
    "opex": 1000.00,
    "payroll_expense": 28249.00,
    "net_profit": 5000.00 - 1000.00 - 28249.00,   # -24,249.00
    "cash_in": 6200.00,
    "cash_out": 1240.00 + 14350.00,               # 15,590.00
    "net_cash": 6200.00 - 15590.00,               # -9,390.00
    "payroll_payable_remaining": 5149.00 + 3204.00 + 5546.00,  # EFKA(er+ee)+tax = 13,899
}
