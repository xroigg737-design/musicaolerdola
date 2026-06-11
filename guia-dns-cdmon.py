from fpdf import FPDF

class GuiaPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Helvetica', 'B', 22)
            self.set_text_color(74, 25, 66)
            self.cell(0, 12, 'Configurar DNS a CDmon', new_x="LMARGIN", new_y="NEXT", align='C')
            self.set_font('Helvetica', '', 11)
            self.set_text_color(120, 90, 120)
            self.cell(0, 8, 'Domini: musicaolerdola.cat', new_x="LMARGIN", new_y="NEXT", align='C')
            self.ln(4)
            self.set_draw_color(200, 168, 78)
            self.set_line_width(0.8)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'musicaolerdola.cat - Configuracio DNS - Pag. {self.page_no()}', align='C')

    def section_title(self, title):
        self.set_font('Helvetica', 'B', 14)
        self.set_text_color(74, 25, 66)
        self.cell(0, 10, title, new_x="LMARGIN", new_y="NEXT")
        self.ln(2)

    def body_text(self, text):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 6.5, text)
        self.ln(2)

    def step(self, number, text):
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(200, 168, 78)
        x = self.get_x()
        self.cell(10, 7, f'{number}.')
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def bold_value(self, label, value):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        self.cell(8, 7, '')
        self.cell(self.get_string_width(label) + 1, 7, label)
        self.set_font('Helvetica', 'B', 12)
        self.set_text_color(74, 25, 66)
        self.cell(0, 7, value, new_x="LMARGIN", new_y="NEXT")
        self.ln(1)

    def info_box(self, text):
        self.set_fill_color(250, 248, 244)
        self.set_draw_color(200, 168, 78)
        self.set_font('Helvetica', 'B', 11)
        self.set_text_color(100, 70, 100)
        x = self.get_x()
        y = self.get_y()
        self.rect(x, y, 170, 14, style='DF')
        self.set_xy(x + 4, y + 3.5)
        self.cell(0, 7, text)
        self.set_xy(x, y + 18)

    def table_row(self, cols, header=False):
        widths = [25, 30, 115]
        if header:
            self.set_font('Helvetica', 'B', 10)
            self.set_fill_color(74, 25, 66)
            self.set_text_color(255, 255, 255)
        else:
            self.set_font('Helvetica', '', 10)
            self.set_fill_color(250, 248, 244)
            self.set_text_color(50, 50, 50)
        for i, col in enumerate(cols):
            self.cell(widths[i], 8, col, border=1, fill=True, align='C' if i < 2 else 'L')
        self.ln()


pdf = GuiaPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=20)

# Pas 1
pdf.section_title('Pas 1 - Entra al panell')
pdf.step(1, "Obre el navegador i ves a:  panel.cdmon.com")
pdf.step(2, "Inicia sessio amb l'email i contrasenya del compte CDmon que acabes de crear")
pdf.ln(4)

# Pas 2
pdf.section_title('Pas 2 - Accedeix als DNS del domini')
pdf.step(1, "Al Llistat basic de serveis, clica l'opcio \"Domini\"")
pdf.step(2, "Dins la seccio \"DNS\", clica el boto \"Gestionar registres\"")
pdf.ln(4)

# Pas 3
pdf.section_title('Pas 3 - Crea el primer registre (arrel @)')
pdf.step(1, "Clica el boto \"Nou registre\"")
pdf.step(2, "A \"Tipus de registre\", selecciona:  A")
pdf.step(3, "Selecciona l'opcio:  \"El domini (Registre @)\"")
pdf.step(4, "Al camp IP, escriu:")
pdf.ln(1)
pdf.info_box("    IP:   13.63.16.49")
pdf.ln(2)
pdf.step(5, "Clica \"Desar\"")
pdf.ln(4)

# Pas 4
pdf.section_title('Pas 4 - Crea el segon registre (www)')
pdf.step(1, "Clica \"Nou registre\" una altra vegada")
pdf.step(2, "A \"Tipus de registre\", selecciona:  A")
pdf.step(3, "Selecciona l'opcio:  \"Un subdomini concret\"")
pdf.step(4, "Al camp subdomini, escriu:")
pdf.ln(1)
pdf.info_box("    Subdomini:   www")
pdf.ln(2)
pdf.step(5, "Al camp IP, escriu:")
pdf.ln(1)
pdf.info_box("    IP:   13.63.16.49")
pdf.ln(2)
pdf.step(6, "Clica \"Desar\"")
pdf.ln(4)

# Pas 5
pdf.section_title('Pas 5 - Espera i verifica')
pdf.body_text(
    "Els canvis es propaguen en aproximadament 5 minuts dins CDmon. "
    "Pot trigar fins a 24-48 hores globalment, pero normalment es molt mes rapid."
)
pdf.ln(2)

# Resum taula
pdf.section_title('Resum dels registres a crear')
pdf.table_row(['Tipus', 'Nom', 'Valor'], header=True)
pdf.table_row(['A', '@', '13.63.16.49'])
pdf.table_row(['A', 'www', '13.63.16.49'])
pdf.ln(6)

pdf.body_text("Un cop fet, avisa al Claude i configurarem el certificat SSL (HTTPS) al servidor.")

pdf.ln(4)
pdf.set_draw_color(200, 168, 78)
pdf.set_line_width(0.5)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())
pdf.ln(4)
pdf.set_font('Helvetica', 'I', 9)
pdf.set_text_color(150, 150, 150)
pdf.cell(0, 6, "Associacio Amics de la Musica d'Olerdola - Juny 2026", align='C')

output_path = '/mnt/c/users/xroig/Downloads/Guia-DNS-CDmon-musicaolerdola.pdf'
pdf.output(output_path)
print(f'PDF generat a: {output_path}')
