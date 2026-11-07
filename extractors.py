"""Leitura local de documentos com indicação de páginas/abas."""
import io,os,re
from pathlib import Path
from docx import Document
from openpyxl import load_workbook
import fitz

ACCEPTED={'.pdf','.docx','.xlsx','.xls','.csv','.txt'}
MAX_UPLOAD=12*1024*1024

def extract(filename: str,content:bytes)->dict:
    ext=Path(filename).suffix.lower()
    if ext not in ACCEPTED:raise ValueError('Formato não suportado: use PDF, DOCX, XLSX, XLS, CSV ou TXT.')
    if not content or len(content)>MAX_UPLOAD:raise ValueError('Arquivo vazio ou acima de 12 MB.')
    blocks=[]
    if ext=='.pdf':
        doc=fitz.open(stream=content,filetype='pdf')
        for i,page in enumerate(doc):
            s=page.get_text('text',sort=True).strip()
            if s:blocks.append({'ref':f'página {i+1}','text':s[:24000]})
        doc.close()
    elif ext=='.docx':
        doc=Document(io.BytesIO(content))
        arr=[p.text.strip() for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                s=' | '.join(c.text.strip() for c in row.cells)
                if s.strip(' |'):arr.append(s)
        blocks.append({'ref':'documento Word','text':'\n'.join(arr)})
    elif ext=='.xlsx':
        wb=load_workbook(io.BytesIO(content),read_only=True,data_only=True)
        for ws in wb.worksheets:
            rows=[]
            for n,row in enumerate(ws.iter_rows(values_only=True),1):
                vals=[str(x).strip() for x in row if x is not None and str(x).strip()]
                if vals:rows.append(' | '.join(vals)[:600])
                if n>1000:break
            if rows:blocks.append({'ref':'aba '+ws.title,'text':'\n'.join(rows)})
        wb.close()
    elif ext=='.xls':
        try:import xlrd
        except ImportError:raise ValueError('Para arquivos XLS antigos, instale a dependência opcional xlrd ou converta para XLSX.')
        wb=xlrd.open_workbook(file_contents=content)
        for ws in wb.sheets():
            rows=[]
            for i in range(min(ws.nrows,1000)):
                vals=[str(v).strip() for v in ws.row_values(i) if str(v).strip()]
                if vals:rows.append(' | '.join(vals)[:600])
            if rows:blocks.append({'ref':'aba '+ws.name,'text':'\n'.join(rows)})
    else:
        try:s=content.decode('utf-8-sig')
        except UnicodeDecodeError:s=content.decode('cp1252',errors='replace')
        blocks.append({'ref':'texto','text':s})
    text='\n'.join(b['text'] for b in blocks)[:120000]
    if len(text.strip())<28:raise ValueError('Não foi possível extrair texto suficiente. Arquivos digitalizados podem exigir OCR.')
    return {'filename':filename,'text':text,'sections':[{'ref':b['ref'],'length':len(b['text'])} for b in blocks], 'parts':[{'ref':b['ref'],'text':b['text'][:120000]} for b in blocks], 'chars':len(text)}
