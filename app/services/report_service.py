import io
import csv
import pandas as pd
from datetime import datetime

# Wrap reportlab imports to ensure clean error messages if missing
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


class ReportService:
    @staticmethod
    def generate_csv_report(headers, rows):
        """Generates a CSV string in memory and returns a BytesIO buffer."""
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(rows)
        
        # Convert to bytes
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        return bytes_output

    @staticmethod
    def generate_excel_report(headers, rows, sheet_name="Report"):
        """Generates an Excel spreadsheet in memory using pandas/openpyxl and returns BytesIO."""
        df = pd.DataFrame(rows, columns=headers)
        output = io.BytesIO()
        
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name=sheet_name, index=False)
            
        output.seek(0)
        return output

    @classmethod
    def generate_pdf_report(cls, title, headers, rows):
        """
        Generates a professionally-styled table-based PDF document using ReportLab.
        Falls back to a CSV download if ReportLab is not available.
        """
        if not REPORTLAB_AVAILABLE:
            # Return CSV fallback as bytes
            return cls.generate_csv_report(headers, rows)
            
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )
        
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles using HSL-like dark/primary colors
        title_style = ParagraphStyle(
            name='ReportTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=22,
            leading=26,
            textColor=colors.HexColor('#2563eb'), # Primary blue
            spaceAfter=6
        )
        
        meta_style = ParagraphStyle(
            name='ReportMeta',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=9,
            leading=12,
            textColor=colors.HexColor('#64748b'), # Slate grey
            spaceAfter=20
        )
        
        # Title and metadata
        story.append(Paragraph(title, title_style))
        story.append(Paragraph(f"Exported: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC | DemandAI Core Engine", meta_style))
        story.append(Spacer(1, 10))
        
        # Format table data
        table_data = [headers]
        for row in rows:
            formatted_row = [str(cell) for cell in row]
            table_data.append(formatted_row)
            
        # Create Table and set widths (letter width is 612. Printable area is ~540)
        col_width = 540 / len(headers)
        t = Table(table_data, colWidths=[col_width] * len(headers))
        
        # Style Table
        t_style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#0f172a')), # Dark header
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0')), # Border light
        ])
        
        # Add alternating row backgrounds
        for i in range(1, len(table_data)):
            if i % 2 == 0:
                t_style.add('BACKGROUND', (0, i), (-1, i), colors.HexColor('#f8fafc'))
                
        t.setStyle(t_style)
        story.append(t)
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        return buffer
