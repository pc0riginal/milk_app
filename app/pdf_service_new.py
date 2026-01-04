from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from datetime import datetime
import io
from .database import get_monthly_purchases

async def generate_monthly_pdf(year: int, month: int):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.3*inch, bottomMargin=0.3*inch)
    styles = getSampleStyleSheet()
    
    title_style = ParagraphStyle(
        'Title',
        parent=styles['Heading1'],
        fontSize=16,
        spaceAfter=10,
        textColor=colors.HexColor('#007bff'),
        alignment=1
    )
    
    story = []
    
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    story.append(Paragraph(f"🥛 MILK TRACKER - {month_names[month-1]} {year}", title_style))
    story.append(Spacer(1, 10))
    
    purchases = await get_monthly_purchases(year, month)
    
    if not purchases:
        story.append(Paragraph("📭 No purchases found.", styles['Normal']))
    else:
        total_quantity = sum(p.quantity for p in purchases)
        total_cost = sum(p.total_cost for p in purchases)
        
        # Person costs
        person_costs = {}
        for purchase in purchases:
            person = purchase.person
            if person not in person_costs:
                person_costs[person] = 0
            person_costs[person] += purchase.total_cost
        
        # Summary table
        summary_data = [
            ['📊 SUMMARY', '', '👥 PEOPLE', ''],
            ['🥛 Total Qty', f'{total_quantity:.1f}L', 'Person', 'Cost'],
            ['💰 Total Cost', f'Rs.{total_cost:.0f}', '', ''],
            ['📝 Purchases', str(len(purchases)), '', '']
        ]
        
        row = 2
        for person, cost in person_costs.items():
            if row < len(summary_data):
                summary_data[row][2] = person
                summary_data[row][3] = f'Rs.{cost:.0f}'
            else:
                summary_data.append(['', '', person, f'Rs.{cost:.0f}'])
            row += 1
        
        summary_table = Table(summary_data, colWidths=[1.5*inch, 1*inch, 1.5*inch, 1*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (1, 0), colors.HexColor('#007bff')),
            ('BACKGROUND', (2, 0), (3, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (3, 0), colors.white),
            ('FONTNAME', (0, 0), (3, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (3, 0), 9),
            ('FONTSIZE', (0, 1), (3, -1), 8),
            ('ALIGN', (0, 0), (3, -1), 'LEFT'),
            ('BOTTOMPADDING', (0, 0), (3, -1), 4),
            ('TOPPADDING', (0, 0), (3, -1), 4),
            ('GRID', (0, 0), (3, -1), 1, colors.black)
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 10))
        
        # All purchases
        purchase_data = [['👤 Person', '📅 Date', '🥛 Qty', '💰 Cost']]
        for purchase in sorted(purchases, key=lambda x: (x.person, x.date)):
            purchase_data.append([
                purchase.person,
                purchase.date.strftime('%d/%m'),
                f'{purchase.quantity:.1f}L',
                f'Rs.{purchase.total_cost:.0f}'
            ])
        
        purchase_table = Table(purchase_data, colWidths=[1.5*inch, 1*inch, 1*inch, 1.5*inch])
        purchase_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 8),
            ('FONTSIZE', (0, 1), (-1, -1), 7),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(purchase_table)
    
    # Footer
    story.append(Spacer(1, 8))
    footer_text = f"📄 Generated: {datetime.now().strftime('%d/%m/%Y')}"
    footer_style = ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6c757d'),
        alignment=1
    )
    story.append(Paragraph(footer_text, footer_style))
    
    doc.build(story)
    buffer.seek(0)
    return buffer