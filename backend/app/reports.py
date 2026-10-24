from io import BytesIO

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
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
    story = [
        Paragraph("HomeServe", styles["Title"]),
        Paragraph("SERVICE INVOICE", styles["Heading2"]),
        Spacer(1, 8 * mm),
        Table(
            [
                ["Invoice number", f"HS-{booking.id:05d}"],
                ["Customer", booking.customer.user.username],
                ["Service", booking.service_type.name],
                ["Service address", booking.service_address],
                [
                    "Scheduled for",
                    booking.scheduled_for.strftime("%d %b %Y, %I:%M %p")
                    if booking.scheduled_for
                    else "Not scheduled",
                ],
                ["Payment method", payment.payment_method.replace("_", " ").title()],
                ["Payment status", payment.status.title()],
            ],
            colWidths=[45 * mm, 115 * mm],
        ),
        Spacer(1, 10 * mm),
        Table(
            [
                ["Description", "Amount"],
                [booking.service_type.name, f"INR {payment.amount}"],
                ["Total paid", f"INR {payment.amount}"],
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
