from fpdf import FPDF

class GuiaPDF(FPDF):
    def header(self):
        if self.page_no() == 1:
            self.set_font('Helvetica', 'B', 22)
            self.set_text_color(74, 25, 66)
            self.cell(0, 12, 'Guia: Registrar musicaolerdola.cat', new_x="LMARGIN", new_y="NEXT", align='C')
            self.set_font('Helvetica', '', 11)
            self.set_text_color(120, 90, 120)
            self.cell(0, 8, 'Registrador recomanat: CDmon', new_x="LMARGIN", new_y="NEXT", align='C')
            self.ln(4)
            self.set_draw_color(200, 168, 78)
            self.set_line_width(0.8)
            self.line(20, self.get_y(), 190, self.get_y())
            self.ln(8)

    def footer(self):
        self.set_y(-15)
        self.set_font('Helvetica', 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'musicaolerdola.cat - Guia de registre - Pag. {self.page_no()}', align='C')

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
        self.cell(10, 7, f'{number}.')
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        self.multi_cell(0, 7, text)
        self.ln(1)

    def bullet(self, text, bold_part=None):
        self.set_font('Helvetica', '', 11)
        self.set_text_color(50, 50, 50)
        x = self.get_x()
        self.cell(8, 7, '-')
        if bold_part:
            self.set_font('Helvetica', 'B', 11)
            self.cell(self.get_string_width(bold_part) + 2, 7, bold_part)
            self.set_font('Helvetica', '', 11)
            self.multi_cell(0, 7, text)
        else:
            self.multi_cell(0, 7, text)
        self.ln(1)

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

    def info_box(self, text):
        self.set_fill_color(250, 248, 244)
        self.set_draw_color(200, 168, 78)
        self.set_font('Helvetica', 'I', 10)
        self.set_text_color(100, 70, 100)
        x = self.get_x()
        y = self.get_y()
        self.rect(x, y, 170, 20, style='DF')
        self.set_xy(x + 4, y + 3)
        self.multi_cell(162, 5.5, text)
        self.ln(6)


pdf = GuiaPDF()
pdf.add_page()
pdf.set_auto_page_break(auto=True, margin=20)

# Pas 1
pdf.section_title('Pas 1 - Comprar el domini')
pdf.step(1, "Ves a cdmon.com/ca/dominis/cat")
pdf.step(2, "Escriu 'musicaolerdola' al cercador i comprova disponibilitat")
pdf.step(3, "Afegeix a la cistella i crea un compte CDmon si no en tens")
pdf.step(4, "Omple les dades del titular (nom de l'associacio o personal)")
pdf.step(5, "Activa la proteccio de privacitat WHOIS (recomanat)")
pdf.step(6, "Paga - aproximadament 19,95 EUR/any")
pdf.ln(4)

# Pas 2
pdf.section_title('Pas 2 - Confirmar email de la Fundacio puntCAT')
pdf.body_text(
    "Rebras un email de la Fundacio puntCAT on has d'acceptar les condicions "
    "d'us del domini .cat."
)
pdf.info_box(
    "Requisit important: la web ha de tenir contingut en catala. "
    "La nostra web ja ho es, aixi que no hi ha cap problema."
)
pdf.ln(2)

# Pas 3
pdf.section_title('Pas 3 - Configurar DNS')
pdf.step(1, "Entra al panell: panel.cdmon.com")
pdf.step(2, "Ves a Domini > DNS > Gestionar registres")
pdf.step(3, "Crea dos registres A:")
pdf.ln(2)

pdf.table_row(['Tipus', 'Nom', 'Valor'], header=True)
pdf.table_row(['A', '@', '13.63.16.49'])
pdf.table_row(['A', 'www', '13.63.16.49'])
pdf.ln(4)

pdf.step(4, "Desa els canvis. Propagacio: ~5 minuts dins CDmon, fins a 24-48h globalment.")
pdf.ln(4)

# Pas 4
pdf.section_title('Pas 4 - Avisa al Xavi (o al Claude)')
pdf.body_text("Un cop el domini estigui comprat i el DNS configurat, cal configurar el servidor:")
pdf.bullet("Configurar el ", "server block de nginx ")
pdf.bullet("Instal·lar el ", "certificat SSL ")
pdf.bullet("Redirigir ", "www cap al domini principal")
pdf.ln(4)

# Info addicional
pdf.section_title("Informacio addicional")
pdf.body_text("Servidor AWS: 13.63.16.49 (i-xr.duckdns.org)")
pdf.body_text("L'Ajuntament d'Olerdola utilitza Nominalia per al seu domini olerdola.cat, "
              "pero Nominalia te la renovacio mes cara (59,45 EUR/any). "
              "CDmon ofereix un preu molt millor a llarg termini (21,05 EUR/any).")

pdf.ln(4)
pdf.set_draw_color(200, 168, 78)
pdf.set_line_width(0.5)
pdf.line(20, pdf.get_y(), 190, pdf.get_y())
pdf.ln(4)
pdf.set_font('Helvetica', 'I', 9)
pdf.set_text_color(150, 150, 150)
pdf.cell(0, 6, "Generat el juny de 2026 per a l'Associacio Amics de la Musica d'Olerdola", align='C')

output_path = '/mnt/c/users/xroig/Downloads/Guia-Registre-musicaolerdola-cat.pdf'
pdf.output(output_path)
print(f'PDF generat a: {output_path}')
