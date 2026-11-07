"""Roteiro e avaliação rastreáveis. Não usa perfis DISC como filtro eliminatório.
A análise de regras não substitui revisão humana; Ollama é opcional.
"""
from __future__ import annotations
import re, unicodedata

STOP = set('a o as os um uma uns umas para por com sem que de da do das dos em no na nos nas ao aos e ou se sua seu seus suas como quando onde qual quais foi foram sobre tem ter tinha isso esse esta este está esta ser são mais menos cada todos todas assim forma meio caso dado dados para entre mas porque ainda também'.split())

def norm(s: str) -> str:
    return ''.join(x for x in unicodedata.normalize('NFKD',s or '') if not unicodedata.combining(x)).lower()

def tokens(s: str) -> set[str]:
    return set(x for x in re.findall(r'[a-z0-9]{3,}',norm(s)) if x not in STOP)

SOFT = re.compile(r'comunic|colabora|trabalho em equipe|equipes?|autonomi|iniciativ|proativ|resilien|empati|escuta ativa|flexibil|adaptab|organiz|disciplina|etica|lideran|negocia|senso critic|pensamento analit|criativ|orienta.{0,12}resultad|soluc.{0,12}problema|gestao de conflitos|inteligencia emocional|relacionamento interpessoal|comprometimento|responsabil|postura|assertiv|capacidade de aprender',re.I)
HARD = re.compile(r'\bexcel\b|\bpower ?bi\b|\bsql\b|\bpython\b|\bcrm\b|\berp\b|sap|totvs|pipedrive|salesforce|hubspot|metas ads|google ads|\biso\b|\bnr ?\d+\b|\bcrea\b|cad|autocad|revit|word ?press|photoshop|canva|capcut|prospe[cç]|outbound|inbound|qualifica[cç]|gest[aã]o de funil|funil de vendas|pipeline|an[aá]lise de dados|relat[oó]rios gerenciais|gest[aã]o financeira|contas a pagar|contas a receber|concilia[cç]|faturamento|tribut|compras|cota[cç]|log[ií]stica|gest[aã]o de projetos|compliance|auditoria|legisla[cç]|vendas consultivas|negocia[cç][aã]o comercial|fechamento de vendas|desenvolvimento de software|infraestrutura|pavimenta[cç]|drenagem|saneamento|tratamento de (a[gá]ua|esgoto)',re.I)
ACTION = re.compile(r'^(executar|realizar|conduzir|gerenciar|coordenar|desenvolver|implantar|implementar|acompanhar|respons[aá]vel|planejar|controlar|analisar|monitorar|elaborar|apresentar|atender|prospectar|negociar|efetuar|organizar|produzir|operar|garantir|apurar|validar|construir|criar|vender|fechar|captar|prestar|registrar|lidar|manter|identificar|solucionar|avaliar|participar|atuar|fazer|gest[aã]o de|gest[aã]o da|gest[aã]o do)\b',re.I)
DIFF = re.compile(r'\bdiferencial\b|\bdesej[aá]vel\b|\bser[aá] um plus\b|\bser[aá] considerado|\bser[aá] valorizado\b|\bpreferencial\b|\bn[aã]o obrigat[oó]ri',re.I)
REQUIRED = re.compile(r'\bobrigat[oó]ri|\bindispens[aá]vel|\bnecess[aá]ri|\brequisito[s]?\b|\bexig[eê]ncia|\bimprescind[ií]vel',re.I)
LOGISTICS = re.compile(r'presencial|h[ií]brido|remoto|disponibilidade|contrata[cç][aã]o|clt|pj|s[aá]bado|turno|jornada|hor[aá]rio|cnh|viagens|residir|localiza[cç][aã]o',re.I)
HEADERS = [
 (re.compile(r'^(?:responsabilidades|atribui[cç][oõ]es|atividades|escopo da fun[cç][aã]o|o que (?:voc[eê] )?far[aá]|no dia a dia|principais atividades|entregas esperadas|rotina)$',re.I),'responsabilidade'),
 (re.compile(r'^(?:requisitos t[eé]cnicos|conhecimentos t[eé]cnicos|habilidades t[eé]cnicas|hard skills|ferramentas|tecnologias|forma[cç][aã]o e experi[eê]ncia)$',re.I),'hard'),
 (re.compile(r'^(?:compet[eê]ncias comportamentais|perfil comportamental|soft skills|habilidades comportamentais|caracter[ií]sticas pessoais|perfil desejado)$',re.I),'soft'),
 (re.compile(r'^(?:diferenciais|desej[aá]veis|diferencial|ser[aá] um diferencial|ser[aá] considerado um diferencial)$',re.I),'diferencial'),
 (re.compile(r'^(?:requisitos|qualifica[cç][oõ]es|o que esperamos|o que buscamos|experi[eê]ncia exigida|exig[eê]ncias)$',re.I),'requisito'),
]

# Critérios e perguntas ancoradas em trechos literais da vaga.
SPECIAL = [
 (r'prospe[cç]|outbound|capta[cç][aã]o de clientes', 'Como você gera oportunidades de forma ativa? Explique canais, cadência, volume e resultados de um caso em que atuou pessoalmente.'),
 (r'qualifica[cç][aã]o de leads|qualificar leads', 'Descreva como investigou e qualificou um lead real. Que critérios usou e que decisão tomou?'),
 (r'vendas consultivas|venda consultiva', 'Conte uma venda consultiva real. Como identificou necessidades, construiu a proposta e mediu o resultado?'),
 (r'\bcrm\b|pipeline|funil de vendas|pipedrive|salesforce|hubspot', 'Qual CRM utilizou e como registrava etapas, próximos passos, retornos e previsões? Dê um exemplo concreto.'),
 (r'contas a pagar|contas a receber|concilia[cç]', 'Descreva uma rotina financeira que executou pessoalmente, os controles adotados e como resolveu divergências.'),
 (r'\bexcel\b|planilh|power ?bi', 'Apresente uma planilha, relatório ou painel que desenvolveu e explique fórmulas, fontes e conferências utilizadas.'),
 (r'negocia[cç][aã]o comercial|obje[cç][aã]o|fechamento de vendas', 'Relate uma negociação com objeção relevante. O que você fez, qual foi o desfecho e que resultado pôde verificar?'),
 (r'metas?|indicadores|\bkpi', 'Informe uma meta real, período, resultado e sua participação direta. Como acompanhava o indicador e corrigia desvios?'),
 (r'vendas? de cursos|vendas? de forma[cç][aã]o|educa[cç][aã]o executiva|p[oó]s.gradua[cç][aã]o', 'Você já comercializou cursos, formações ou produtos educacionais? Descreva público, argumento de valor, objeções e resultados. Se não, explique uma experiência transferível.'),
 (r'autonomi|iniciativ|proativ', 'Conte uma situação específica em que precisou agir sem orientação imediata. Qual decisão tomou e o que aconteceu?'),
 (r'comunica[cç]|escuta ativa|relacionamento interpessoal', 'Relate uma situação em que sua comunicação precisou ser adaptada para resolver um problema. O que fez e qual resultado obteve?'),
 (r'resili[eê]ncia|trabalho sob press[aã]o', 'Descreva um contratempo profissional importante. Que ações concretas tomou, que apoio buscou e qual foi o resultado?'),
 (r'negocia[cç][aã]o com fornecedores|cota[cç][aã]o|compras', 'Descreva uma negociação ou compra real, os critérios comparados, o controle de riscos e o resultado alcançado.'),
 (r'auditoria|iso 9001|n[aã]o conformidade', 'Relate uma auditoria ou não conformidade tratada. Que requisito, evidência, ação corretiva e verificação de eficácia foram usados?'),
 (r'\bpython\b|\bsql\b|desenvolvimento de software', 'Explique uma implementação técnica realizada por você, os desafios, os testes e o resultado validado.'),
]

def clean(s: str)->str:
    return re.sub(r'\s+',' ',s or '').strip(' \u2022-\t:;')

def fragments(jd: str) -> list[dict]:
    rows=[]; context=None
    raw_lines=(jd or '').replace('\r','\n').split('\n')
    for line_no,raw in enumerate(raw_lines,1):
        line=clean(re.sub(r'^\s*(?:[\u2022•\-*]|\d+[.)])\s*','',raw))
        if not line: continue
        if len(line)>900:
            parts=re.split(r'(?<=[.;])\s+(?=[A-Za-zÀ-ÿ])',line)
        else: parts=[line]
        for part in parts:
            part=clean(part)
            if not part:continue
            hdr=clean(re.sub(r'[:]+$','',part)).lower()
            for pattern,tag in HEADERS:
                if pattern.search(hdr):context=tag;break
            else:
                if len(part)<12:continue
                if re.match(r'^(?:sobre a empresa|benef[ií]cios|oferecemos|o que oferecemos|remunera[cç][aã]o|sal[aá]rio|localiza[cç][aã]o|sobre a vaga)\s*:',part,re.I): continue
                # Listas de competências numa linha são divididas; frases de responsabilidade permanecem inteiras.
                splits=[part]
                if len(part)<240 and (',' in part or ' • ' in part) and not ACTION.search(part):
                    chunks=[clean(x) for x in re.split(r'[,;]|\s+[•|]\s+',part) if len(clean(x))>5]
                    if 2<=len(chunks)<=10 and all(len(x)<115 for x in chunks):splits=chunks
                for chunk in splits:
                    plain=norm(chunk)
                    if DIFF.search(plain) or context=='diferencial': kind='diferencial'
                    elif context in ('responsabilidade','hard','soft'):kind=context
                    elif context=='requisito':kind='soft' if SOFT.search(plain) and not HARD.search(plain) else 'hard'
                    elif LOGISTICS.search(plain) and not HARD.search(plain) and not ACTION.search(plain):kind='logistica'
                    elif SOFT.search(plain) and not HARD.search(plain):kind='soft'
                    elif ACTION.search(plain):kind='responsabilidade'
                    elif HARD.search(plain):kind='hard'
                    elif REQUIRED.search(plain):kind='hard'
                    else:
                        # Trechos soltos sem competência observável não geram pergunta inventada.
                        continue
                    if kind=='diferencial' and SOFT.search(plain):cat='soft'
                    elif kind=='diferencial':cat='hard'
                    else:cat=kind
                    rows.append({'origin':chunk[:370],'line':line_no,'kind':kind,'category':cat,'is_differential':kind=='diferencial'})
    # Remover duplicatas estritas e fragmentos quase iguais
    uniq=[]
    for row in rows:
        ts=tokens(row['origin'])
        if not ts:continue
        if any(row['category']==r['category'] and len(ts & tokens(r['origin']))/max(1,min(len(ts),len(tokens(r['origin']))))>.83 for r in uniq):continue
        uniq.append(row)
    return uniq

def special_question(phrase: str)->str|None:
    for pat,q in SPECIAL:
        if re.search(pat,phrase,re.I):return q
    return None

def make_question(entry:dict, cv:str='',idx:int=0)->dict:
    phrase=entry['origin']
    q=special_question(phrase)
    cat=entry['category']
    if q is None:
        if cat=='responsabilidade':q=f'Conte uma situação real em que precisou executar esta responsabilidade: “{phrase[:160]}”. Explique contexto, suas ações, entregas e resultados.'
        elif cat=='soft':q=f'Relate uma situação concreta em que demonstrou a competência “{phrase[:150]}”. O que fez pessoalmente, como lidou com outras pessoas e qual foi o desfecho?'
        elif cat=='hard':q=f'Como você aplicou, na prática, este conhecimento ou requisito: “{phrase[:155]}”? Cite ferramentas ou métodos, sua contribuição e uma evidência do resultado.'
        else:q=f'Você atende a condição descrita na vaga: “{phrase[:160]}”? Explique sua disponibilidade e eventuais restrições.'
    evidence=''; common=tokens(phrase)&tokens(cv)
    if cv.strip() and cat!='logistica':
        if len(common)>=2:evidence='O currículo contém termos relacionados a este critério; a experiência precisa ser confirmada na entrevista.'
        else:evidence='Não foi identificada menção textual clara no currículo; isso não significa ausência da competência.'
    w={'responsabilidade':3,'hard':3,'soft':2,'logistica':1}.get(cat,2)
    if entry['is_differential']:w=1
    return {'id':f'Q{idx:02d}','category':cat,'category_label':{'responsabilidade':'Responsabilidades','hard':'Hard skills','soft':'Soft skills','logistica':'Condições da vaga'}[cat], 'criterion':phrase[:220], 'origin':phrase,'line':entry['line'],'differential':entry['is_differential'],'weight':w,'question':q,'cv_observation':evidence}

def build_questions(jd:str, cv:str='',limit:int=15)->dict:
    items=fragments(jd)
    buckets={c:[r for r in items if r['category']==c] for c in ['responsabilidade','hard','soft','logistica']}
    quotas={'responsabilidade':5,'hard':5,'soft':4,'logistica':1}
    selected=[]
    for cat in ('responsabilidade','hard','soft','logistica'):selected.extend(buckets[cat][:quotas[cat]])
    if len(selected)<min(limit,len(items)):
        for it in items:
            if it not in selected:selected.append(it)
            if len(selected)>=limit:break
    selected=selected[:limit]
    questions=[make_question(r,cv,i+1) for i,r in enumerate(selected)]
    used=set()
    for q in questions:
        nq=norm(q['question'])
        if nq in used:
            criterion=q['criterion'].strip(' .')
            if q['category']=='hard':
                q['question']=f'Explique tecnicamente como você aplica o requisito “{criterion}”. Quais métodos, ferramentas e controles utiliza? Dê um exemplo de resultado.'
            elif q['category']=='soft':
                q['question']=f'Conte uma situação em que precisou demonstrar “{criterion}”. Qual foi o contexto, sua atitude e a reação das pessoas envolvidas?'
            else:
                q['question']=f'Entre as responsabilidades da vaga, há “{criterion}”. Como executava essa entrega na prática, com que frequência e que resultados gerava?'
        used.add(norm(q['question']))
    cats={c:sum(q['category']==c for q in questions) for c in buckets}
    warnings=[]
    if not jd.strip(): warnings.append('A descrição da vaga está vazia. O questionário não pode ser gerado.')
    if not questions: warnings.append('Não foram encontrados requisitos ou atividades explícitos suficientes. Revise o documento extraído.')
    for cat in ['responsabilidade','hard','soft']:
        if cats[cat]==0: warnings.append(f'A descrição não trouxe evidência textual suficiente para perguntas de { {"responsabilidade":"responsabilidades","hard":"hard skills","soft":"soft skills"}[cat] }. Não foram inventados requisitos.')
    return {'questions':questions,'warnings':warnings,'counts':cats,'source_fragments':len(items),'engine':'regras_rastreaveis_v6'}

def evidence_snippet(s:str,terms:set[str])->str:
    chunks=[clean(x) for x in re.split(r'[\n\.!?;]+',s or '') if clean(x)]
    rated=sorted(chunks,key=lambda x:(len(tokens(x)&terms),min(250,len(x))),reverse=True)
    return rated[0][:320] if rated else ''

def disc_summary(text:str)->dict:
    if not text.strip():return {'status':'não fornecido','observations':[],'score_use':'Não integra o índice de aderência.'}
    keys=[('D','Dominância'),('I','Influência'),('S','Estabilidade'),('C','Conformidade')]
    found=[]
    for letter,label in keys:
        pat=rf'\b{label}\s*[:\-=]?\s*(\d{{1,3}}(?:[,.]\d+)?)\s*%?'
        m=re.search(pat,text,re.I)
        if m:
            v=float(m.group(1).replace(',','.'))
            if 0<=v<=100:found.append({'dimension':label,'reported_value':v,'source':'DISC fornecido'})
    if found:
        most=max(found,key=lambda x:x['reported_value'])
        prompts={'Dominância':'Avaliar por exemplos como toma decisões e lida com metas e divergências.','Influência':'Investigar como constrói relacionamentos, comunica ideias e influencia interlocutores.','Estabilidade':'Investigar rotinas, mudanças de prioridade, constância e reação a alterações no trabalho.','Conformidade':'Investigar organização, checagem de dados, procedimentos e decisões diante de ambiguidades.'}
        return {'status':'dimensões numéricas extraídas. Comparação interna apenas indicativa; conferir metodologia, escala e laudo do instrumento.', 'observations':found, 'relative_observation':'Maior valor informado: '+most['dimension']+'. Não implica adequação ou inadequação a qualquer cargo.', 'behavioral_validation': [prompts[x['dimension']] for x in found], 'score_use':'Não integra o índice de aderência, nem constitui critério eliminatório.'}
    return {'status':'documento disponível; dimensões não identificadas com segurança','observations':[],'score_use':'Não integra o índice de aderência. Requer interpretação humana do laudo e contexto do instrumento.'}

