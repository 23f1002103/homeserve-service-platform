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
                ["Service", cell(booking.service_name)],
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
                [cell(booking.service_name), cell(f"INR {payment.amount}")],
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


def create_package_invoice_pdf(order):
    """Build one customer invoice covering every job in a package order."""
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
        "PackageInvoiceCell",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
    )

    def cell(value):
        return Paragraph(escape(str(value)), cell_style)

    first_job = order.jobs[0]
    details = Table(
        [
            ["Package order", cell(f"HSP-{order.id:05d}")],
            ["Customer", cell(order.customer.user.username)],
            ["Package", cell(order.service_package.name)],
            ["Service address", cell(first_job.service_address)],
            [
                "Scheduled for",
                cell(
                    first_job.scheduled_for.strftime("%d %b %Y, %I:%M %p")
                    if first_job.scheduled_for
                    else "Not scheduled"
                ),
            ],
            ["Payment status", cell(first_job.payments[0].status.title())],
        ],
        colWidths=[45 * mm, 115 * mm],
    )
    rows = [["Included service", "Amount"]]
    rows.extend(
        [cell(job.service_type.name), cell(f"INR {job.payments[0].amount}")]
        for job in order.jobs
    )
    rows.append([cell("Total paid"), cell(f"INR {order.total_amount}")])
    charges = Table(rows, colWidths=[115 * mm, 45 * mm])
    table_style = TableStyle(
        [
            ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#BAC1BC")),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F5B47")),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("PADDING", (0, 0), (-1, -1), 8),
        ]
    )
    details.setStyle(table_style)
    charges.setStyle(table_style)
    document.build(
        [
            Paragraph("HomeServe", styles["Title"]),
            Paragraph("PACKAGE INVOICE", styles["Heading2"]),
            Spacer(1, 8 * mm),
            details,
            Spacer(1, 10 * mm),
            charges,
            Spacer(1, 12 * mm),
            Paragraph(
                "This invoice covers all professional jobs in the package order.",
                styles["BodyText"],
            ),
        ]
    )
    buffer.seek(0)
    return buffer
