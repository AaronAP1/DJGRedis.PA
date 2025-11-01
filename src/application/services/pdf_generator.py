"""
Servicio para generar PDF de Carta de Presentación.

Genera un documento oficial con el membrete de la Universidad Peruana Unión.
"""

from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT
from io import BytesIO
from datetime import datetime


def generate_presentation_letter_pdf(letter_request):
    """
    Genera el PDF de la carta de presentación oficial.
    
    Args:
        letter_request: Instancia de PresentationLetterRequest
    
    Returns:
        ContentFile: Archivo PDF generado
    """
    
    # Crear buffer en memoria
    buffer = BytesIO()
    
    # Crear documento PDF
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=72,
        leftMargin=72,
        topMargin=100,
        bottomMargin=72
    )
    
    # Contenedor de elementos
    story = []
    
    # Estilos
    styles = getSampleStyleSheet()
    
    # Estilo personalizado para el título
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=14,
        textColor='black',
        spaceAfter=30,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )
    
    # Estilo para el cuerpo
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_JUSTIFY,
        spaceAfter=12,
        fontName='Helvetica'
    )
    
    # Estilo para datos del destinatario
    recipient_style = ParagraphStyle(
        'Recipient',
        parent=styles['BodyText'],
        fontSize=11,
        alignment=TA_LEFT,
        fontName='Helvetica-Bold'
    )
    
    # ========================================================================
    # CONTENIDO DEL PDF
    # ========================================================================
    
    # Membrete (simulado - en producción usar logo real)
    header = Paragraph(
        """
        <b>UNIVERSIDAD PERUANA UNIÓN</b><br/>
        <font size=9>Facultad de Ingeniería y Arquitectura</font><br/>
        <font size=9>{escuela}</font>
        """.format(escuela=letter_request.ep),
        title_style
    )
    story.append(header)
    story.append(Spacer(1, 0.3 * inch))
    
    # Fecha
    fecha_actual = datetime.now().strftime("%d de %B de %Y")
    fecha_text = Paragraph(
        f"<para align=right>{fecha_actual}</para>",
        body_style
    )
    story.append(fecha_text)
    story.append(Spacer(1, 0.3 * inch))
    
    # Destinatario
    destinatario = Paragraph(
        f"""
        <b>{letter_request.company_representative}</b><br/>
        {letter_request.company_position}<br/>
        {letter_request.company_name}<br/>
        {letter_request.company_address}
        """,
        recipient_style
    )
    story.append(destinatario)
    story.append(Spacer(1, 0.3 * inch))
    
    # Asunto
    asunto = Paragraph(
        "<b>Asunto: CARTA DE PRESENTACIÓN</b>",
        body_style
    )
    story.append(asunto)
    story.append(Spacer(1, 0.2 * inch))
    
    # Saludo
    saludo = Paragraph(
        f"Estimado(a) {letter_request.company_position}:",
        body_style
    )
    story.append(saludo)
    story.append(Spacer(1, 0.2 * inch))
    
    # Cuerpo de la carta
    cuerpo_texto = f"""
    Por medio de la presente, tengo el agrado de dirigirme a usted para presentar a 
    <b>{letter_request.student_full_name}</b>, identificado(a) con código de estudiante 
    <b>{letter_request.student_code}</b>, alumno(a) del <b>{letter_request.year_of_study}</b>, 
    <b>{letter_request.study_cycle}</b> ciclo de estudios de la <b>{letter_request.ep}</b> 
    de nuestra universidad.
    <br/><br/>
    El/La estudiante ha manifestado su interés en realizar sus prácticas pre-profesionales 
    en el área de <b>{letter_request.practice_area}</b> en su prestigiosa institución, 
    con fecha tentativa de inicio el <b>{letter_request.start_date.strftime("%d de %B de %Y")}</b>.
    <br/><br/>
    Las prácticas pre-profesionales constituyen una etapa fundamental en la formación académica 
    de nuestros estudiantes, permitiéndoles aplicar los conocimientos teóricos adquiridos en 
    situaciones reales del ámbito laboral.
    <br/><br/>
    Agradezco de antemano la atención que pueda brindar a la presente solicitud y quedo a su 
    disposición para cualquier información adicional que requiera.
    <br/><br/>
    Sin otro particular, me despido de usted cordialmente.
    """
    
    cuerpo = Paragraph(cuerpo_texto, body_style)
    story.append(cuerpo)
    story.append(Spacer(1, 0.5 * inch))
    
    # Firma (espacio para firma física)
    firma = Paragraph(
        """
        <para align=center>
        ______________________________________<br/>
        <b>Coordinador de Prácticas Profesionales</b><br/>
        {escuela}<br/>
        Universidad Peruana Unión
        </para>
        """.format(escuela=letter_request.ep),
        body_style
    )
    story.append(firma)
    story.append(Spacer(1, 0.3 * inch))
    
    # Datos de contacto del estudiante (pie de página)
    contacto = Paragraph(
        f"""
        <para align=center>
        <font size=9>
        <i>Datos del estudiante: {letter_request.student_email} | 
        Teléfono de contacto de la empresa: {letter_request.company_phone}</i>
        </font>
        </para>
        """,
        body_style
    )
    story.append(contacto)
    
    # Construir PDF
    doc.build(story)
    
    # Obtener contenido del buffer
    pdf_content = buffer.getvalue()
    buffer.close()
    
    # Crear nombre de archivo
    filename = f"carta_presentacion_{letter_request.student_code}_{datetime.now().strftime('%Y%m%d')}.pdf"
    
    # Retornar como ContentFile
    return ContentFile(pdf_content, name=filename)


def get_spanish_month(month_number):
    """Convierte número de mes a nombre en español."""
    meses = {
        1: 'enero', 2: 'febrero', 3: 'marzo', 4: 'abril',
        5: 'mayo', 6: 'junio', 7: 'julio', 8: 'agosto',
        9: 'septiembre', 10: 'octubre', 11: 'noviembre', 12: 'diciembre'
    }
    return meses.get(month_number, '')
