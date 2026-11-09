"""Leitura conservadora do Comparativo DISC textualmente extraível da Recrutei.

Não converte pontuações do assessment em aptidão comprovada ou nota de
seleção. O DISC individual ilustrado pode ser armazenado mesmo sem texto;
para a leitura dos índices exige o comparativo legível.
"""
from __future__ import annotations
import re
import unicodedata

KEYS=(('D','Dominância'),('I','Influência'),('S','Estabilidade'),('C','Conformidade'))

def _plain(s):
    return ''.join(c for c in unicodedata.normalize('NFD',s) if unicodedata.category(c)!='Mn')

def extract_disc_fields(text:str)->dict:
    raw=text or ''
    if not re.search(r'(?i)\b(?:recrutest|recrutei|relat[oó]rio disc completo)\b', raw):
        return {'source':'desconhecida','values':{},'profile':None,'scale':None,'warnings':['Formato não confirmado como comparativo Recrutei.']}
    values={}
    normalized=_plain(raw)
    for key,label in KEYS:
        # Exige dimensão e valor na MESMA linha; o sumário usa nomes em uma
        # linha e números de página na seguinte (não são escores DISC).
        pat=rf'(?im)^[ \t]*{_plain(label)}[ \t]*[:=\-]?[ \t]*([1-7])(?:[ \t]*/[ \t]*7)?[ \t]*$'
        m=re.search(pat,normalized)
        if m:values[key]=int(m.group(1))
    if len(values)<4:
        for key,_ in KEYS:
            m=re.search(rf'(?im)^[ \t]*{key}[ \t]*[:=][ \t]*([1-7])[ \t]*$',normalized)
            if m and key not in values:values[key]=int(m.group(1))
    profile=None
    m=re.search(r'(?i)\bPerfil[ \t]+Disc[ \t]*\n([^\n]+)',raw)
    if m:
        value=re.split(r'[ \t]{2,}',m.group(1).strip())[-1].strip()
        if 1<=len(value.split())<=3 and len(value)<40:profile=value
    if not profile:
        m=re.search(r'(?im)^[ \t]*Perfil[ \t]*[:=][ \t]*([A-Za-zÀ-ÿ][A-Za-zÀ-ÿ -]{2,35})[ \t]*$',raw)
        if m:profile=m.group(1).strip()
    warnings=[]
    if len(values)<4:warnings.append('Não foram identificadas as quatro dimensões de modo seguro.')
    if re.search(r'(?i)\bdesenvolvedor\s+back.end\b',raw) and re.search(r'(?i)\bauxiliar de far?m[aá]cia\b',raw):
        warnings.append('O comparativo contém referência incompatível a outro cargo; priorizar os indicadores e verificar manualmente os textos de aderência.')
    return {'source':'Recrutei / Recrutest','values':values,'profile':profile,'scale':'segmentos de 1 a 7','warnings':warnings}

def enrich_disc_comparative(text:str)->str:
    if not str(text or '').strip():return ''
    data=extract_disc_fields(text)
    if data['source']=='desconhecida':return text
    lines=['COMPARATIVO DISC FORNECIDO:', 'Instrumento: Recrutei / Recrutest', 'Escala: segmentos de 1 a 7']
    if data['profile']:lines.append('Perfil: '+data['profile'])
    for key,label in KEYS:
        if key in data['values']:lines.append(f'{label} ({key}): {data["values"][key]}/7')
    if data['warnings']:lines.append('VALIDAÇÃO INTERNA: '+' '.join(data['warnings']))
    lines.append('Tendências comportamentais complementares; não comprovam competências profissionais nem substituem avaliação humana.')
    return '\n'.join(lines)+'\n\nTEXTO ORIGINAL DO COMPARATIVO:\n'+text


def extract_individual_visual_disc(content:bytes)->dict:
    """Lê os quatro SEGMENTOS (1 a 7) do gráfico do DISC individual Recrutei.

    Alguns PDFs exportados pela plataforma são inteiramente rasterizados, sem
    caracteres de texto. Esta rotina NÃO faz OCR nem presume o nome do perfil:
    identifica uma geometria gráfica conhecida e extrai a altura dos quatro
    marcadores D/I/S/C. Se o desenho for diferente, falha de modo explícito.

    A rotina não converte intensidades em habilidades demonstradas.
    """
    import fitz
    from PIL import Image
    if not content or len(content)>12*1024*1024:
        raise ValueError('Arquivo DISC vazio ou acima do limite permitido.')
    try:
        doc=fitz.open(stream=content,filetype='pdf')
    except Exception as exc:
        raise ValueError('PDF individual não pôde ser aberto.') from exc
    try:
        if len(doc)!=3:
            raise ValueError('O padrão visual conhecido do DISC individual do Recrutei tem três páginas.')
        page=doc[2]
        # Evita confundir relatório textual com imagem rasterizada.
        if len(page.get_text('text').strip())>120:
            raise ValueError('O PDF não corresponde ao padrão visual esperado.')
        pix=page.get_pixmap(matrix=fitz.Matrix(1.7,1.7),colorspace=fitz.csRGB,alpha=False)
        im=Image.frombytes('RGB',(pix.width,pix.height),pix.samples)
    finally:
        doc.close()
    w,h=im.size
    px=im.load()
    # Coordenadas normalizadas, calibradas no relatório individual de três
    # páginas fornecido pelo usuário. Não usar fora deste template.
    x_positions=(.43435,.47680,.51830,.55870)
    score_one=.2745
    score_seven=.1571
    step=(score_one-score_seven)/6

    def navy_line(x,y):
        r,g,b=px[x,y]
        return (r<125 and g<135 and b>r+25 and b>g+20)
    # Confere a presença das quatro colunas verticais do gráfico.
    anchors=0
    for xnorm in x_positions:
        cx=round(xnorm*w);cy=round(.237*h)
        if any(navy_line(xx,cy) for xx in range(cx-2,cx+3)):
            anchors+=1
    if anchors<3:
        raise ValueError('As quatro colunas do gráfico DISC não foram reconhecidas.')

    def count_marker(x,y):
        count=0
        for iy in range(max(0,y-6),min(h,y+7)):
            for ix in range(max(0,x-5),min(w,x+6)):
                r,g,b=px[ix,iy]
                # O marcador do gráfico é preto, mas as colunas são azuis.
                if max(r,g,b)<105 and (max(r,g,b)-min(r,g,b))<36:
                    count+=1
        return count

    values={}
    confidence={}
    for dim,xnorm in zip(('D','I','S','C'),x_positions):
        x=round(xnorm*w)
        counts={score:count_marker(x,round((score_one-(score-1)*step)*h)) for score in range(1,8)}
        ranked=sorted(counts.items(),key=lambda it:it[1],reverse=True)
        best,second=ranked[0],ranked[1]
        if best[1]<14 or best[1]-second[1]<8:
            raise ValueError(f'Leitura visual inconclusiva para a dimensão {dim}; confira o gráfico.')
        values[dim]=best[0]
        confidence[dim]={'marker_pixels':best[1],'margin_pixels':best[1]-second[1]}
    return {'source':'Recrutei / DISC individual visual',
            'values':values,'profile':None,'scale':'segmentos de 1 a 7',
            'method':'geometria dos marcadores da página 3',
            'confidence':confidence,
            'warnings':['Perfil nominal e textos narrativos não são extraídos do PDF visual sem OCR. Consulte o laudo ou anexe o comparativo.',
                        'Intensidades DISC representam tendências; não comprovam competências ou desempenho.']}


def enrich_individual_visual_disc(content:bytes)->tuple[str,dict]:
    data=extract_individual_visual_disc(content)
    lines=['LAUDO DISC INDIVIDUAL RECRUTEI (LEITURA DO GRÁFICO):',
           'Escala do gráfico: segmentos de 1 a 7',
           'Fonte: laudo individual PDF, página 3.']
    for key,label in KEYS:
        lines.append(f'{label} ({key}): {data["values"][key]}/7')
    lines.append('Leitura dos quatro segmentos realizada pelo gráfico; revisão visual recomendada.')
    lines.append('Os índices não demonstram capacidades profissionais nem integram automaticamente o score técnico.')
    return '\n'.join(lines),data


def reconcile_disc_sources(individual_text:str,comparative_text:str)->str:
    """Consolida laudo individual e comparativo, sem ocultar divergências."""
    individual=(individual_text or '').strip()
    comparative=(comparative_text or '').strip()
    if not comparative:
        return individual[:120000]
    cmp=extract_disc_fields(comparative)
    indiv_vals={}
    for key,label in KEYS:
        m=re.search(rf'(?im)^{_plain(label)}\s*\({key}\)\s*:\s*([1-7])\s*/\s*7\b',_plain(individual))
        if m:indiv_vals[key]=int(m.group(1))
    divergent=[f'{key}: individual {indiv_vals[key]}/7; comparativo {cmp["values"][key]}/7'
               for key in indiv_vals if key in cmp['values'] and indiv_vals[key]!=cmp['values'][key]]
    sections=[enrich_disc_comparative(comparative)]
    if individual:sections.append('LAUDO DISC INDIVIDUAL:\n'+individual)
    if divergent:
        sections.insert(0,'ALERTA DE DIVERGÊNCIA ENTRE AS FONTES: '+'; '.join(divergent)+'. Conferir manualmente antes de concluir o parecer.')
    return '\n\n'.join(sections)[:120000]
