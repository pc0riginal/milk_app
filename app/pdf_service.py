from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime
import io
from .database import get_monthly_purchases, get_people

async def generate_monthly_pdf(year: int, month: int):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=0.3*inch, bottomMargin=0.3*inch)
    styles = getSampleStyleSheet()
    
    # Compact styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=8,
        textColor=colors.HexColor('#007bff'),
        alignment=1
    )
    
    story = []
    
    # Compact header
    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                   'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
    
    story.append(Paragraph(f"🥛 MILK TRACKER - {month_names[month-1]} {year}", title_style))
    story.append(Spacer(1, 10))
    
    # Get data
    purchases = await get_monthly_purchases(year, month)
    
    if not purchases:
        story.append(Paragraph("○ No purchases found for this month.", styles['Normal']))
        story.append(Spacer(1, 20))
        story.append(Paragraph("Start tracking your milk purchases to see detailed reports here!", styles['Normal']))
    else:
        # Overall summary with icons
        total_quantity = sum(p.quantity for p in purchases)
        total_cost = sum(p.total_cost for p in purchases)
        
        summary_data = [
            ['▣ SUMMARY', ''],
            ['● Total Quantity', f'{total_quantity:.1f} Liters'],
            ['$ Total Cost', f'Rs.{total_cost:.2f}'],
            ['# Total Purchases', str(len(purchases))],
            ['~ Average per Day', f'{total_quantity/30:.1f}L']
        ]
        
        summary_table = Table(summary_data, colWidths=[2.5*inch, 2*inch])
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#007bff')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 14),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8f9fa')),
            ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 1), (-1, -1), 12),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('TOPPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
        ]))
        
        story.append(summary_table)
        story.append(Spacer(1, 30))
        
        # Group purchases by person
        person_purchases = {}
        person_costs = {}
        for purchase in purchases:
            person = purchase.person
            if person not in person_purchases:
                person_purchases[person] = []
                person_costs[person] = 0
            person_purchases[person].append(purchase)
            person_costs[person] += purchase.total_cost
        
        # Person-wise cost overview
        story.append(Paragraph("▶ COST BREAKDOWN BY PERSON", title_style))
        story.append(Spacer(1, 10))
        
        person_summary_data = [['Person', 'Total Cost', 'Total Quantity', 'Avg Rate']]
        for person, cost in person_costs.items():
            person_qty = sum(p.quantity for p in person_purchases[person])
            avg_rate = cost / person_qty if person_qty > 0 else 0
            person_summary_data.append([
                f'● {person}', 
                f'Rs.{cost:.2f}', 
                f'{person_qty:.1f}L',
                f'Rs.{avg_rate:.2f}/L'
            ])
        
        person_summary_table = Table(person_summary_data, colWidths=[1.5*inch, 1.2*inch, 1.2*inch, 1.2*inch])
        person_summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f8fff8')),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
        ]))
        
        story.append(person_summary_table)
        story.append(Spacer(1, 40))
        
        # Detailed purchases by person
        for person, person_purchase_list in person_purchases.items():
            # Person header with stats
            person_total = sum(p.total_cost for p in person_purchase_list)
            person_qty = sum(p.quantity for p in person_purchase_list)
            
            story.append(Paragraph(f"🧑‍💼 {person.upper()} - DETAILED PURCHASES", person_header_style))
            
            # Person stats
            person_stats_data = [
                ['📊 Personal Summary', ''],
                ['💰 Total Spent', f'₹{person_total:.2f}'],
                ['🥛 Total Quantity', f'{person_qty:.1f} Liters'],
                ['📝 Number of Purchases', str(len(person_purchase_list))],
                ['📈 Average per Purchase', f'₹{person_total/len(person_purchase_list):.2f}']
            ]
            
            person_stats_table = Table(person_stats_data, colWidths=[2*inch, 1.5*inch])
            person_stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#17a2b8')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f0f8ff')),
                ('FONTNAME', (0, 1), (0, -1), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
                ('TOPPADDING', (0, 0), (-1, -1), 8),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
            ]))
            
            story.append(person_stats_table)
            story.append(Spacer(1, 15))
            
            # Person's purchase details
            purchase_data = [['Date', 'Qty (L)', 'Rate (Rs)', 'Total (Rs)', 'Time']]
            for purchase in sorted(person_purchase_list, key=lambda x: x.date):
                purchase_data.append([
                    f'• {purchase.date.strftime("%d %b")}',
                    f'{purchase.quantity:.1f}',
                    f'{purchase.price_per_liter:.2f}',
                    f'{purchase.total_cost:.2f}',
                    purchase.date.strftime('%I:%M %p')
                ])
            
            purchase_table = Table(purchase_data, colWidths=[1*inch, 0.8*inch, 0.8*inch, 0.9*inch, 0.9*inch])
            purchase_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#6f42c1')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 9),
                ('FONTSIZE', (0, 1), (-1, -1), 8),
                ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#faf9ff')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
                ('TOPPADDING', (0, 0), (-1, -1), 6),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#dee2e6'))
            ]))
            
            story.append(purchase_table)
            story.append(Spacer(1, 30))
    
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