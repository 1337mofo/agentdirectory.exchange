import markdown2
from weasyprint import HTML

# Read markdown
with open('Agent_Directory_Whitepaper.md', 'r', encoding='utf-8') as f:
    md_content = f.read()

# Convert to HTML
html_content = markdown2.markdown(md_content, extras=['tables', 'fenced-code-blocks'])

# Wrap in full HTML document with styling
full_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            line-height: 1.6;
            max-width: 800px;
            margin: 40px auto;
            padding: 20px;
            color: #1f2937;
        }}
        h1 {{
            color: #2563eb;
            border-bottom: 3px solid #2563eb;
            padding-bottom: 10px;
            font-size: 32px;
        }}
        h2 {{
            color: #1e40af;
            margin-top: 30px;
            font-size: 24px;
        }}
        h3 {{
            color: #1e3a8a;
            font-size: 20px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin: 20px 0;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 12px;
            text-align: left;
        }}
        th {{
            background-color: #2563eb;
            color: white;
        }}
        code {{
            background-color: #f3f4f6;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Courier New', monospace;
            font-size: 13px;
        }}
        pre {{
            background-color: #f3f4f6;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
        pre code {{
            background-color: transparent;
            padding: 0;
        }}
        strong {{
            color: #1e40af;
        }}
        ul, ol {{
            margin-left: 20px;
        }}
    </style>
</head>
<body>
{html_content}
</body>
</html>"""

# Generate PDF
HTML(string=full_html).write_pdf('Agent_Directory_Whitepaper.pdf')

print("✅ PDF generated successfully: Agent_Directory_Whitepaper.pdf")
