"""Criar um PDF simples para teste do Docling."""

from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch

# Criar PDF
pdf_path = "test_docling.pdf"
c = canvas.Canvas(pdf_path, pagesize=letter)

# Título
c.setFont("Helvetica-Bold", 24)
c.drawString(2*inch, 10*inch, "Relatório Técnico")

# Conteúdo
c.setFont("Helvetica", 12)
c.drawString(2*inch, 9*inch, "Este é um documento de teste para Docling.")
c.drawString(2*inch, 8.5*inch, "O Docling processa documentos de forma avançada:")

# Lista
y = 7.5*inch
items = [
    "- Layout understanding",
    "- Tabelas estruturadas",
    "- Fórmulas matemáticas",
    "- OCR integrado"
]

for item in items:
    c.drawString(2*inch, y, item)
    y -= 0.3*inch

# Tabela
c.setFont("Helvetica-Bold", 12)
c.drawString(2*inch, 5.5*inch, "Tabela de Exemplo")
c.setFont("Helvetica", 10)

# Cabeçalho da tabela
y = 5*inch
headers = ["Item", "Valor", "Status"]
x_positions = [2*inch, 3.5*inch, 5*inch]

for i, header in enumerate(headers):
    c.drawString(x_positions[i], y, header)

y -= 0.3*inch

# Linha separadora
c.line(2*inch, y, 5.5*inch, y)
y -= 0.3*inch

# Dados da tabela
data = [
    ["A", "100", "OK"],
    ["B", "200", "OK"],
    ["C", "300", "Pendente"]
]

for row in data:
    for i, cell in enumerate(row):
        c.drawString(x_positions[i], y, cell)
    y -= 0.3*inch

# Rodapé
c.setFont("Helvetica", 10)
c.drawString(2*inch, 1*inch, "Documento gerado automaticamente para teste do Docling")

c.save()
print(f"✅ PDF criado: {pdf_path}")

