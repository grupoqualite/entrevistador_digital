"""Interpretação comportamental conservadora e rastreável para a minuta.

Não infere traços de personalidade a partir de cargo, adjetivos soltos, DISC isolado
ou mera presença de palavras-chave. Conecta episódios descritos a condutas observáveis.
Sem LLM, trata-se de uma minuta por regras, sujeita à revisão humana.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher

SPACE = re.compile(r'\s+')
CONTACTS = re.compile(r'(?i)\b[\w.+-]+@[\w-]+(?:\.[\w-]+)+\b|(?:\+?55\s*)?\(?\d{2}\)?\s*9?\d{4}[-\s]?\d{4}')


def compact(value, limit=520):
    s=SPACE.sub(' ',str(value or '')).strip()
    s=CONTACTS.sub('',s).strip(' ;,.')
    if len(s)>limit:
        s=s[:limit].rsplit(' ',1)[0].rstrip(',;:.')+'…'
    return s


def norm(value):
    s=compact(value,10000).lower()
    return re.sub(r'[^\w ]+',' ',s)


def negated(value):
    return bool(re.search(r'(?i)\b(?:nunca fiz|nunca trabalhei|nunca atuei|não tenho experiência|não possuo experiência|não exerci|não fiz|não atuei|não trabalhei|sem experiência)\b',str(value or '')))


# Verbos e situações concretas que podem sustentar uma inferência delimitada.
# Ações descritas em outras competências são aproveitadas, não apenas as perguntas de soft skills.
AXES = [
    dict(name='Comunicação e relacionamento',relevance=r'comunic|relacion|atend|cliente|escut|empati|negocia',
         markers=[(r'\b(?:ouvi|escutei|acolhi|escutava|ouvir)\b','escuta das necessidades'),
                  (r'\b(?:expliquei|esclareci|orientei|informei|comuniquei|orientava)\b','esclarecimento de informações'),
                  (r'\b(?:alinhei|alinhava|negociei|conversei)\b','alinhamento com interlocutores'),
                  (r'\b(?:atendia|atendi|atendimento presencial|atendimento ao cliente|atendimento de balcão)\b','contato direto com clientes')],
         reading='Há elementos para examinar a clareza do contato com clientes e a condução de demandas, sem presumir habilidade persuasiva ou qualidade de comunicação em todas as situações.',
         validation='confirmar como atua diante de reclamações, conflitos e demandas que exigem negociação'),
    dict(name='Organização e acompanhamento',relevance=r'organiza|planeja|disciplina|prioriz|rotina|process|indicad|gestão de tempo',
         markers=[(r'\b(?:organizei|organizava|planejei|priorizei|separava|separei|estruturei)\b','organização das etapas de trabalho'),
                  (r'\b(?:registrei|registrava|registro no crm|registr[oa] tudo|controle de pedidos|planilha)\b','registro e acompanhamento de informações'),
                  (r'\b(?:acompanhava|acompanhei|follow.up|agenda|cronograma)\b','monitoramento de pendências e prazos'),
                  (r'\b(?:indicadores|funil|crm|erp)\b','uso de controles operacionais')],
         reading='As rotinas relatadas são compatíveis com necessidade de sistematização e acompanhamento. Não demonstram, isoladamente, capacidade de priorização sob alta carga ou constância de desempenho.',
         validation='verificar como define prioridades quando há demandas simultâneas e prazos concorrentes'),
    dict(name='Atenção a detalhes e confiabilidade',relevance=r'atenção|detalh|qualidade|confer|cuidad|responsab|precis',
         markers=[(r'\b(?:conferi|conferia|comparava|comparei|verifiquei|verificava|checava|validei|revisava)\b','conferência de informações antes da execução'),
                  (r'\b(?:divergência|erro|inconsistência|falha)\b','identificação de divergências'),
                  (r'\b(?:quantidade|etiqueta|registro de quantidade|documentação)\b','checagem de registros e quantidades')],
         reading='A conduta descrita é pertinente a funções que exigem precisão e prevenção de erros. A regularidade desse cuidado e o domínio dos procedimentos específicos ainda precisam ser confirmados.',
         validation='aprofundar o procedimento utilizado para evitar e corrigir erros na rotina'),
    dict(name='Autonomia e resolução de problemas',relevance=r'autonom|iniciativ|decis|resolv|soluç|proativ|crític',
         markers=[(r'\b(?:decidi|propus|resolvi|implementei|antecipei|replanejei)\b','decisão ou iniciativa própria'),
                  (r'\b(?:identifiquei|detectei|percebi)\b','identificação de problema ou oportunidade'),
                  (r'\b(?:alternativa|contornei|solução|corrigi)\b','busca de encaminhamentos diante de dificuldades'),
                  (r'\b(?:pedi apoio|consultei o responsável|solicitei apoio|supervisor)\b','reconhecimento dos limites de decisão e busca de suporte')],
         reading='A experiência permite discutir como identifica problemas e escolhe encaminhamentos. Solicitar apoio quando necessário não equivale, por si só, a falta de autonomia ou a capacidade de decidir em cenários complexos.',
         validation='esclarecer o que decidiu diretamente, quais alternativas avaliou e qual foi o resultado'),
    dict(name='Colaboração e articulação',relevance=r'equipe|colabora|coopera|lideran|conflit|alinha',
         markers=[(r'\b(?:equipe|supervisor|responsável|colega|fornecedor|prestador)\b','interação com outras pessoas da operação'),
                  (r'\b(?:alinhava|alinhei|coordenei|orientei|deleguei|acompanhei)\b','alinhamento ou coordenação de atividades'),
                  (r'\b(?:solicitei apoio|pedi ajuda|encaminhei)\b','acionamento de suporte quando necessário')],
         reading='Os episódios apontam interfaces de trabalho e permitem avaliar colaboração prática. Não autorizam concluir, sem outros exemplos, sobre liderança, influência ou capacidade de administrar conflitos.',
         validation='examinar um caso de desacordo entre pessoas e como foi construído o encaminhamento'),
    dict(name='Adaptação a imprevistos',relevance=r'adapt|mudan|resili|pressão|imprevist|flexib',
         markers=[(r'\b(?:imprevisto|atraso|mudança|indisponível|não estava disponível)\b','situação diferente da rotina prevista'),
                  (r'\b(?:ajustei|reorganizei|replanejei|antecipei|alterei|oferecer outra opção)\b','ajuste de encaminhamento ou planejamento')],
         reading='Há sinais pontuais de ajuste diante de circunstâncias diferentes das previstas. Isso não basta para classificar resiliência ou reação estável à pressão.',
         validation='confirmar decisões e resultados em situações de pressão com recursos limitados'),
]


def split_document(value):
    raw=str(value or '').replace('•','\n').replace(' | ','\n')
    chunks=re.split(r'(?<=[.!?])\s+|\n+',raw)
    out=[];seen=set()
    for chunk in chunks:
        t=compact(chunk,340)
        if len(t)<40 or len(t)>330 or len(t.split())<6:continue
        if CONTACTS.search(t):continue
        n=norm(t)
        if n in seen:continue
        seen.add(n)
        out.append(t)
    return out[:90]


def collect_evidence(criteria,cv_text,linkedin_text):
    episodes=[];seen=[]
    for c in criteria:
        a=compact(c.get('answer'),1200)
        if len(a)<30 or negated(a):continue
        n=norm(a)
        if any(SequenceMatcher(None,n,s).ratio()>.83 for s in seen):continue
        seen.append(n)
        episodes.append({'type':'episode','text':a,'source_id':str(c.get('id') or ''),'criterion':c.get('criterion') or ''})
    contexts=[];known=set()
    for source,value in [('trajetoria',cv_text),('historico_complementar',linkedin_text)]:
        for line in split_document(value):
            n=norm(line)
            if n in known or len(line)<50:continue
            known.add(n)
            contexts.append({'type':'career','text':line,'source_id':source,'criterion':''})
    return episodes,contexts


def _match_actions(text,axis):
    return [label for pattern,label in axis['markers'] if re.search(pattern,text,re.I)]


def _axis_strength(ev,axis):
    acts=_match_actions(ev['text'],axis)
    if not acts:return 0,[]
    # Episódios concretos valem mais do que listagem de ferramentas/cargos.
    action_verbs=r'\b(?:eu |ouvi|expliquei|organizei|conferi|atendi|verifiquei|registrei|solicitei|pedi|identifiquei|decidi|planejei|reorganizei|comparava|conferia|separava|acompanhava|registrava)\b'
    event=('episode'==ev['type'] and bool(re.search(action_verbs,ev['text'],re.I)))
    strength=(3 if event and len(acts)>=2 else 2 if event else 1)
    return strength,acts


def _natural_list(items,max_len=3):
    out=[]
    for t in items:
        if t not in out:out.append(t)
        if len(out)>=max_len:break
    if not out:return ''
    if len(out)==1:return out[0]
    return ', '.join(out[:-1])+' e '+out[-1]


def disc_paragraph(disc_text,report_disc,axes_seen):
    """Lê tendências explícitas e dimensões do laudo, sem diagnosticar pessoas."""
    observations=(report_disc or {}).get('observations') or []
    labels={'D':'Dominância','I':'Influência','S':'Estabilidade','C':'Conformidade'}
    reverse={v.casefold():k for k,v in labels.items()}
    values={}
    for v in observations:
        raw_name=str(v.get('dimension','')).strip()
        key=raw_name.upper() if raw_name.upper() in labels else reverse.get(raw_name.casefold())
        raw=str(v.get('reported_value','')).strip()
        if raw.endswith('.0'):raw=raw[:-2]
        if key and raw and len(raw)<14:values[key]=raw
    raw=str(disc_text or '')
    # O comparativo costuma ser anexado depois do laudo e não pode desaparecer
    # quando a extração do PDF principal produz um texto extenso.
    marker='COMPARATIVO DISC FORNECIDO:'
    src=(raw[:7000]+'\n'+raw.split(marker,1)[-1][:5500]) if marker in raw else raw[:12000]
    # Formatos compactos D3/I3/S7/C5 são mantidos como valores declarados,
    # sem converter números em níveis psicológicos sem legenda do instrumento.
    if not values:
        for key,raw in re.findall(r'(?<![A-Za-z])([DISC])\s*[:=]?\s*(\d{1,2})(?!\d)',src,re.I):
            if int(raw)<=10:values[key.upper()]=raw
    qualitative=[]
    for dimension in labels.values():
        pattern=rf'(?i)\b{dimension}\s*[:=-]?\s*(?:mais\s+)?(elevad[ao]|alt[ao]|baix[ao]|predominante|moderad[ao])\b'
        m=re.search(pattern,src)
        if m:qualitative.append(f'{dimension.lower()} {m.group(1).lower()}')
    # Um comparativo pode especificar leitura do instrumento, mas não autoriza
    # afirmar comportamento individual comprovado.
    profile_match=re.search(r'(?im)\bperfil(?:\s+comportamental|\s+predominante)?\s*[:=-]\s*([\wÀ-ÿ][\wÀ-ÿ -]{2,40})',src)
    profile=compact(profile_match.group(1),45) if profile_match else ''
    if not observations and not values and not qualitative and not profile:
        return None,'A interpretação do DISC requer conferência técnica das escalas e do conteúdo completo.' if src.strip() else None
    axes_txt=_natural_list([x.lower() for x in axes_seen[:2]]) if axes_seen else 'condutas profissionais observáveis'
    parts=[]
    if profile and len(profile.split())<=5:
        parts.append(f'O relatório DISC descreve o estilo {profile}, classificação que deve ser lida conforme a metodologia do instrumento.')
    if qualitative:
        parts.append('O DISC descreve tendências associadas a '+_natural_list(qualitative,4)+'.')
    elif values:
        ordered=', '.join(f'{labels[k]} ({k}: {values[k]})' for k in 'DISC' if k in values)
        if ('segmentos de 1 a 7' in raw.lower() and ('recrutei' in raw.lower() or 'recrutest' in raw.lower())):
            parts.append(f'O DISC do Recrutei apresenta {ordered}, em escala de sete segmentos.')
            tendencies={
                'D':('preferência relativamente maior por iniciativa e posicionamento', 'menor inclinação espontânea a impor decisões'),
                'I':('maior disposição para comunicação expansiva e influência social', 'estilo mais reservado nas interações'),
                'S':('preferência por constância e previsibilidade das rotinas', 'maior facilidade para alternar o ritmo de execução'),
                'C':('preferência por normas, verificações e padrões explícitos', 'maior flexibilidade em relação a formalizações'),
            }
            hints=[]
            for key in 'DISC':
                try:v=int(float(values.get(key,'')))
                except (ValueError,TypeError):continue
                if key=='S' and v>=6:hints.append('elevada estabilidade, associada a maior preferência por rotinas previsíveis')
                elif key=='I' and v<=2:hints.append('influência baixa, que pode indicar comunicação menos expansiva, sem demonstrar incapacidade de atendimento')
                elif key=='D' and v>=5:hints.append('dominância moderada ou elevada, compatível com maior iniciativa em determinadas situações')
                elif key=='C' and v>=6:hints.append('conformidade elevada, associada à preferência por padrões e verificações')
            if hints:parts.append('Considerados isoladamente, os segmentos sugerem '+ '; '.join(hints[:3])+'. Essas tendências devem ser confrontadas com situações concretas da trajetória e da entrevista.')
        else:
            parts.append(f'O DISC apresenta os indicadores {ordered}. A escala e as condições de aplicação precisam ser verificadas antes de qualquer interpretação qualitativa desses números.')
    parts.append(f'Essas informações são complementares às condutas relatadas, em especial {axes_txt}, e não comprovam, isoladamente, autonomia, desempenho ou reação à pressão.')
    return ' '.join(parts),None


def build_behavioral(criteria,cv_text,linkedin_text,disc_text,disc_report):
    episodes,career=collect_evidence(criteria,cv_text,linkedin_text)
    paragraphs=[];pending=[];trace=[];ranked=[]
    noted_career_context=False
    for ax in AXES:
        matches=[]
        for ev in episodes+career:
            strength,acts=_axis_strength(ev,ax)
            if strength:matches.append((strength,len(acts),ev,acts))
        matches.sort(key=lambda x:(x[0],x[1]),reverse=True)
        if not matches:continue
        main=matches[0]; strength=main[0]
        # Efeito de contexto documental é admissível, mas fraco e explicitado.
        episode_matches=[m for m in matches if m[2]['type']=='episode' and m[0]>=2]
        if episode_matches:
            top=episode_matches[:2]
            labels=_natural_list([a for x in top for a in x[3]],4)
            cross=any(m[2]['type']=='career' for m in matches)
            start=f'Em {ax["name"].lower()}, há exemplos de {labels}.'
            if cross and not noted_career_context:
                start+=' Esse aspecto também encontra contexto no percurso profissional, embora a atividade desempenhada não constitua prova independente da competência comportamental.'
                noted_career_context=True
            else:
                start+=' As ações descritas permitem examinar a atuação efetiva em situações de trabalho, ainda que o relato não cubra todos os cenários da função.'
            paragraphs.append(start+' '+ax['reading'])
            trace.append({'competencia':ax['name'],'origens':[x[2]['source_id'] for x in top],
                          'nivel':'episódio profissional descrito; confirmação externa não realizada',
                          'trechos':[{'origem':x[2]['source_id'],'trecho':compact(x[2]['text'],350)} for x in top]})
            pending.append(ax['validation'][0].upper()+ax['validation'][1:]+'.')
            ranked.append((max(m[0] for m in episode_matches),ax['name']))
        elif career:
            labels=_natural_list([a for x in matches[:2] for a in x[3]],3)
            paragraphs.append(
                f'Na dimensão de {ax["name"].lower()}, a experiência profissional inclui atividades associadas a {labels}. '
                'O histórico oferece contexto para essa competência, mas não permite afirmar, sem um episódio concreto, '
                'como o profissional age, decide ou se comunica em situações de maior exigência.'
            )
            trace.append({'competencia':ax['name'],'origens':[x[2]['source_id'] for x in matches[:2]],
                          'nivel':'indício indireto no histórico, sem confirmação comportamental',
                          'trechos':[{'origem':x[2]['source_id'],'trecho':compact(x[2]['text'],350)} for x in matches[:2]]})
            pending.append(ax['validation'][0].upper()+ax['validation'][1:]+'.')
            ranked.append((1,ax['name']))
    # Não transformar presença de palavras soltas em relatório de seis atributos.
    if len(paragraphs)>3:
        # Priorizar eixos relevantes para os critérios comportamentais definidos pela vaga.
        soft=' '.join(str(c.get('criterion','')) for c in criteria if c.get('category_key')=='soft')
        priority=[]
        for i,ax in enumerate(AXES):
            if i<len(AXES):
                relevance=1 if re.search(ax['relevance'],soft,re.I) else 0
                priority.append((relevance, next((x[0] for x in ranked if x[1]==ax['name']),0), i))
        selected={i for _,_,i in sorted(priority,reverse=True)[:3]}
        # Conserva índice da origem, porque somente eixos que geraram parágrafo contam.
        present_axes=[a for a in AXES if any(x['competencia']==a['name'] for x in trace)]
        selected_names={a['name'] for a in AXES if AXES.index(a) in selected}
        indices=[j for j,a in enumerate(present_axes) if a['name'] in selected_names]
        if len(indices)<3:
            indices=list(range(min(3,len(paragraphs))))
        paragraphs=[paragraphs[j] for j in indices]
        trace=[trace[j] for j in indices]
    axes_seen=[x['competencia'] for x in trace]
    disc_text_out,disc_pending=disc_paragraph(disc_text,disc_report,axes_seen)
    if disc_text_out:paragraphs.append(disc_text_out)
    if disc_pending:pending.append(disc_pending)
    if not paragraphs:
        paragraphs.append(
            'Ainda não há episódios profissionais suficientemente detalhados para sustentar uma leitura comportamental '
            'sobre comunicação, organização, autonomia e reação a imprevistos. Essas dimensões devem ser investigadas '
            'a partir de situações reais, distinguindo a atividade exercida da conduta observável.'
        )
    if axes_seen:
        paragraphs.append(
            'Em conjunto, os elementos mais consistentes dizem respeito a '+_natural_list([x.lower() for x in axes_seen],3)+'. '
            'Essas observações são limitadas às situações efetivamente descritas e não autorizam generalizar '
            'características pessoais ou prever desempenho em todos os contextos. A recomendação deve considerar '
            'a exigência específica da função e eventuais lacunas ainda não esclarecidas.'
        )
    return paragraphs,pending[:4],trace
