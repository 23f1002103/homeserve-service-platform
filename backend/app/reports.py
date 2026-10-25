from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


def create_invoice_pdf(booking):
    """Build a small PDF invoice in memory for one paid customer booking."""
    payment = booking.payments[0]
    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=20 * mm,
        leftMargin=20 * mm,
        topMargin=18 * mm,
        bottomMargin=18 * mm,
    )
    styles = getSampleStyleSheet()
    cell_style = ParagraphStyle(
        "InvoiceCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        spaceAfter=0,
    )
    header_cell_style = ParagraphStyle(
        "InvoiceHeaderCell",
        parent=cell_style,
        textColor=colors.white,
        fontName="Helvetica-Bold",
    )

    def cell(value, style=cell_style):
        """Create a table value that wraps instead of crossing its cell border."""
        return Paragraph(escape(str(value)), style)

    story = [
        Paragraph("HomeServe", styles["Title"]),
        Paragraph("SERVICE INVOICE", styles["Heading2"]),
        Spacer(1, 8 * mm),
        Table(
            [
                ["Invoice number", cell(f"HS-{booking.id:05d}", header_cell_style)],
                ["Customer", cell(booking.customer.user.username)],
                ["Service", cell(booking.service_type.name)],
                ["Service address", cell(booking.service_address)],
                [
                    "Scheduled for",
                    cell(
                        booking.scheduled_for.strftime("%d %b %Y, %I:%M %p")
                        if booking.scheduled_for
                        else "Not scheduled"
                    ),
                ],
                [
                    "Payment method",
                    cell(payment.payment_method.replace("_", " ").title()),
                ],
                ["Payment status", cell(payment.status.title())],
            ],
            colWidths=[45 * mm, 115 * mm],
        ),
        Spacer(1, 10 * mm),
        Table(
            [
                ["Description", "Amount"],
                [cell(booking.service_type.name), cell(f"INR {payment.amount}")],
                [cell("Total paid"), cell(f"INR {payment.amount}")],
            ],
            colWidths=[115 * mm, 45 * mm],
        ),
        Spacer(1, 12 * mm),
        Paragraph(
            "This invoice was generated electronically by HomeServe.",
            styles["BodyText"],
        ),
    ]
    for table in (story[3], story[5]):
        table.setStyle(
            TableStyle(
                [
                    ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BAC1BC")),
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F5B47")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"),
                    ("PADDING", (0, 0), (-1, -1), 8),
                ]
            )
        )
    document.build(story)
    buffer.seek(0)
    return buffer
