from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import io

def generate_report_pdf(report: dict) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("StampedeShield — Session Report", styles["Title"]))
    elements.append(Spacer(1, 10))

    meta = [
        ["Source", report.get("source", "-")],
        ["Start time", report.get("start_time", "-")],
        ["End time", report.get("end_time", "-")],
        ["Duration (s)", str(report.get("duration_seconds", "-"))],
        ["Frames processed", str(report.get("frame_count", "-"))],
        ["Max people detected", str(report.get("max_people", "-"))],
        ["Max risk score", str(report.get("max_risk_score", "-"))],
        ["Alerts triggered", str(len(report.get("alert_events", [])))],
    ]
    table = Table(meta, colWidths=[180, 250])
    table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, -1), colors.whitesmoke),
        ("FONTSIZE", (0, 0), (-1, -1), 10),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Phase Duration Breakdown", styles["Heading2"]))
    phase_data = [["Phase", "Duration (s)"]] + [
        [k, f'{v:.1f}'] for k, v in report.get("phase_durations", {}).items()
    ]
    phase_table = Table(phase_data, colWidths=[180, 250])
    phase_table.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("BACKGROUND", (0, 0), (0, 0), colors.lightgrey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(phase_table)
    elements.append(Spacer(1, 16))

    elements.append(Paragraph("Alert Events", styles["Heading2"]))
    if report.get("alert_events"):
        alert_data = [["Time", "Message"]] + [
            [e["time"], e["message"]] for e in report["alert_events"]
        ]
        alert_table = Table(alert_data, colWidths=[80, 350])
        alert_table.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("BACKGROUND", (0, 0), (-1, 0), colors.lightgrey),
            ("FONTSIZE", (0, 0), (-1, -1), 8),
            ("PADDING", (0, 0), (-1, -1), 6),
        ]))
        elements.append(alert_table)
    else:
        elements.append(Paragraph("No alerts triggered during this session.", styles["Normal"]))

    doc.build(elements)
    buffer.seek(0)
    return buffer.getvalue()