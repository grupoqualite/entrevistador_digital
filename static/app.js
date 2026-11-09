(() => {
// Verificação de compatibilidade: nunca tentar autenticar com HTML e JS de versões diferentes.
const versaoEsperada = '9.7.5-disc-brand';
const versaoPagina = document.querySelector('meta[name="ed-ui-version"]')?.content;
const camposObrigatorios = ['loginForm','identifier','pass','authMsg','currentAccount','changePasswordScreen','passwordChangeForm','usersTab','regenerateQuestions','createUserForm','backupsTab','openRestore','restoreForm','restoreFile','restoreConfirmation'];
const ausentes = camposObrigatorios.filter(id => !document.getElementById(id));
if (versaoPagina !== versaoEsperada || ausentes.length) {
  const aviso = document.getElementById('authMsg');
  if (aviso) aviso.textContent = 'A interface foi carregada com arquivos de versões diferentes. Publique static/index.html e static/app.js juntos, depois abra o endereço em janela anônima.';
  console.error('VERSAO_INCOMPATIVEL', {versaoPagina, versaoEsperada, ausentes});
  return;
}
const $=id=>document.getElementById(id), state={vacancies:[],candidates:[],selectedVacancy:null,editing:[],selectedCandidate:null,report:null,sourceParts:null};

// Sincronizar a versão mostrada no painel com a versão efetivamente executada pelo servidor.
// A consulta não utiliza dados pessoais e não altera a sessão do usuário.
async function atualizarVersaoDoPainel(){
  const indicador=document.getElementById('runtimeVersion');
  if(!indicador)return;
  try{
    const resposta=await fetch('/api/health?_='+Date.now(),{cache:'no-store',credentials:'same-origin'});
    if(!resposta.ok)throw new Error('HTTP '+resposta.status);
    const diagnostico=await resposta.json();
    const versao=typeof diagnostico.version==='string'?diagnostico.version.trim():'';
    if(!versao)throw new Error('Versão ausente no diagnóstico');
    if(versao==='9.7.5-disc-brand'){
      indicador.textContent='V9.7.5 · DISC Recrutei e parecer';
      indicador.title='Servidor verificado: '+versao;
    }else{
      indicador.textContent='Servidor: '+versao;
      indicador.title='O Render está executando versão diferente da V9.7.5. Confira o último commit implantado.';
      indicador.style.color='#a33a2b';
    }
  }catch(erro){
    indicador.textContent='Versão não verificada';
    indicador.title='Falha ao consultar /api/health: '+erro.message;
  }
}
atualizarVersaoDoPainel();

const escapeHTML=s=>String(s??'').replace(/[&<>"']/g,ch=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[ch]));
const fmt=s=>escapeHTML(s).replace(/\n/g,'<br>');
async function call(url,options={}){const res=await fetch(url,options);let data;try{data=await res.json()}catch{data={detail:'Servidor indisponível.'}}if(!res.ok)throw new Error(data.detail||`Erro HTTP ${res.status}`);return data;}
function info(id,text,bad=false){const el=$(id);el.classList.remove('hidden');el.style.background=bad?'#fff2f0':'';el.textContent=text;}
function option(elementId,value,label){const el=$(elementId);if(!el)throw new Error('Campo de seleção ausente: '+elementId);const o=document.createElement('option');o.value=String(value);o.textContent=String(label);el.append(o);return o}
function showTab(tab){document.querySelectorAll('.tabpage').forEach(x=>x.classList.toggle('hidden',x.id!==tab));document.querySelectorAll('[data-tab]').forEach(x=>x.classList.toggle('selected',x.dataset.tab===tab))}
document.querySelectorAll('[data-tab]').forEach(x=>x.onclick=()=>showTab(x.dataset.tab));
// Atalho explícito, disponível a qualquer administrador ativo.
$('openRestore').onclick=()=>{if(activeUser?.role!=='administrador')return;showTab('backups');$('restoreForm').scrollIntoView({behavior:'smooth',block:'start'});};
let activeUser=null;
async function showLoggedIn(){
 const me=await call('/api/admin/me');activeUser=me;
 $('signin').classList.add('hidden');$('logout').classList.remove('hidden');
 $('currentAccount').textContent=me.name+' · '+(me.role==='administrador'?'Administrador':'Recrutador');
 if(me.must_change_password){$('workspace').classList.add('hidden');$('changePasswordScreen').classList.remove('hidden');return;}
 $('changePasswordScreen').classList.add('hidden');$('workspace').classList.remove('hidden');
 $('usersTab').classList.toggle('hidden',me.role!=='administrador');
 $('backupsTab').classList.toggle('hidden',me.role!=='administrador');
 $('backup').classList.toggle('hidden',me.role!=='administrador');
 $('openRestore').classList.toggle('hidden',me.role!=='administrador');
 if(me.role!=='administrador' && document.querySelector('[data-tab="backups"].selected'))showTab('vacancies');
 await refreshAll();if(me.role==='administrador')await refreshStaffUsers();
}
$('loginForm').onsubmit=async e=>{e.preventDefault();try{
 await call('/api/login',{method:'POST',body:new URLSearchParams({identifier:$('identifier').value.trim(),password:$('pass').value})});
 $('authMsg').textContent='';await showLoggedIn();
}catch(err){$('authMsg').textContent=err.message}};
$('logout').onclick=async()=>{await call('/api/logout',{method:'POST'});location.reload()};
$('passwordChangeForm').onsubmit=async e=>{e.preventDefault();try{
 if($('newPersonalPassword').value!==$('confirmPersonalPassword').value)throw new Error('As senhas não coincidem.');await call('/api/admin/me/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:$('oldPersonalPassword').value,new_password:$('newPersonalPassword').value})});
 $('passwordChangeMsg').textContent='';$('oldPersonalPassword').value='';$('newPersonalPassword').value='';$('confirmPersonalPassword').value='';await showLoggedIn();
}catch(err){$('passwordChangeMsg').textContent=err.message}};
async function init(){try{await showLoggedIn()}catch{}}init();
async function refreshAll(){await Promise.all([refreshVacancies(),refreshCandidates()])}
async function refreshVacancies(){state.vacancies=await call('/api/admin/vacancies');let old=state.selectedVacancy||$('vacancySelect').value;for(const id of ['vacancySelect','candidateVacancy']){$(id).innerHTML='';for(const v of state.vacancies)option(id,v.id,v.title)}if(state.vacancies.length){$('vacancySelect').value=state.vacancies.some(v=>v.id===old)?old:state.vacancies[0].id;state.selectedVacancy=$('vacancySelect').value;await loadQuestions();}else{state.editing=[];drawQuestions()}}
async function refreshCandidates(){state.candidates=await call('/api/admin/candidates');const opts=$('reportCandidate');const old=opts.value||state.selectedCandidate;opts.innerHTML='';for(const c of state.candidates)option('reportCandidate',c.id,`${c.name} · ${c.vacancy}`);if(state.candidates.length){opts.value=state.candidates.some(c=>c.id===old)?old:state.candidates[0].id;state.selectedCandidate=opts.value;await selectCandidate();}else{$('reportCandidateInfo').textContent='Sem candidatos cadastrados.';state.selectedCandidate=null;$('answersArea').innerHTML='';$('reportContent').innerHTML='<p class="hint">Cadastre um candidato primeiro.</p>'}drawCandidateList()}
$('jobFile').onchange=async()=>{const f=$('jobFile').files[0];if(!f)return;info('jobMsg','Extraindo o texto do arquivo...');try{const data=new FormData();data.append('file',f);const ex=await call('/api/admin/extract',{method:'POST',body:data});state.sourceParts=ex.parts||[{ref:'Documento completo',text:ex.text}];$('sheets').classList.remove('hidden');$('sheetSelect').innerHTML='';option('sheetSelect','all',`Documento completo (${ex.chars} caracteres)`);for(let i=0;i<state.sourceParts.length;i++)option('sheetSelect',String(i),state.sourceParts[i].ref);if(state.sourceParts.length===1){$('sheetSelect').value='all';$('jobDescription').value=state.sourceParts[0].text;info('jobMsg',`Descrição extraída de ${f.name} e preenchida abaixo (${ex.chars} caracteres). Confira o texto e clique em Gerar questionário fundamentado.`)}else{$('sheetSelect').value='all';$('jobDescription').value='';info('jobMsg',`Arquivo ${f.name} extraído (${ex.chars} caracteres). Selecione a(s) aba(s)/página(s), clique em Aplicar texto selecionado, confira o conteúdo e gere o questionário.`)}}catch(err){state.sourceParts=null;$('sheets').classList.add('hidden');$('jobDescription').value='';info('jobMsg',`Não foi possível importar o arquivo: ${err.message}`,true)}};
$('applySheet').onclick=()=>{if(!state.sourceParts)return;const v=$('sheetSelect').value;$('jobDescription').value=v==='all'?state.sourceParts.map(x=>x.text).join('\n'):state.sourceParts[Number(v)]?.text||'';info('jobMsg','Texto aplicado. Confira a descrição e clique em Gerar questionário.')};
$('vacancyForm').onsubmit=async e=>{e.preventDefault();if($('jobFile').files.length && !$('jobDescription').value.trim())return info('jobMsg','Aplique o texto importado antes de gerar as perguntas.',true);try{const data=new URLSearchParams({title:$('jobTitle').value,description:$('jobDescription').value});const r=await call('/api/admin/vacancies',{method:'POST',body:data});state.selectedVacancy=r.id;await refreshVacancies();info('jobMsg',`Vaga criada com ${r.generated} perguntas. ${r.warnings.join(' ')||'Revise o questionário na área ao lado.'}`);$('vacancySelect').scrollIntoView({behavior:'smooth',block:'nearest'})}catch(err){info('jobMsg',err.message,true)}};
$('vacancySelect').onchange=async()=>{state.selectedVacancy=$('vacancySelect').value;await loadQuestions()};
async function loadQuestions(){if(!state.selectedVacancy)return;const v=await call(`/api/admin/vacancies/${state.selectedVacancy}`);state.editing=v.questions;drawQuestions();$('qMsg').classList.add('hidden')}
function drawQuestions(){const el=$('questions');el.innerHTML='';$('qCounter').textContent=`${state.editing.length} perguntas`;state.editing.forEach((q,index)=>{const box=document.createElement('article');box.className='questioncard';box.innerHTML=`<div class="meta"><span class="category">${escapeHTML(q.category_label||q.category)}</span><button class="btn small outline" data-remove="${index}" type="button">Remover</button></div><textarea rows="3" data-edit="${index}" aria-label="Pergunta ${index+1}">${escapeHTML(q.question)}</textarea><div class="origin"><strong>Foco da pergunta:</strong> ${escapeHTML(q.focus||q.category_label||'Competência da vaga')}<br><strong>O que verificar:</strong> ${escapeHTML(q.expected_evidence||'Experiência prática e resultados verificáveis')}<br><strong>Trecho da vaga:</strong> ${escapeHTML(q.origin||'Inserida manualmente')}<br><strong>Critério:</strong> ${escapeHTML(q.criterion||'')}</div><div class="smallrow"><span class="hint">Peso (1 a 5):</span><select data-weight="${index}">${[1,2,3,4,5].map(w=>`<option ${Number(q.weight)===w?'selected':''} value="${w}">${w}</option>`).join('')}</select><label class="hint" style="margin:0"><input data-diff="${index}" type="checkbox" style="width:auto;display:inline;margin:0" ${q.differential?'checked':''}> Diferencial</label></div>`;el.append(box)});el.querySelectorAll('[data-edit]').forEach(x=>x.onchange=()=>state.editing[Number(x.dataset.edit)].question=x.value);el.querySelectorAll('[data-weight]').forEach(x=>x.onchange=()=>state.editing[Number(x.dataset.weight)].weight=Number(x.value));el.querySelectorAll('[data-diff]').forEach(x=>x.onchange=()=>state.editing[Number(x.dataset.diff)].differential=x.checked);el.querySelectorAll('[data-remove]').forEach(x=>x.onclick=()=>{state.editing.splice(Number(x.dataset.remove),1);drawQuestions()})}
$('addQuestion').onclick=()=>{state.editing.push({question:'',category:'hard',category_label:'Hard skills',criterion:'Novo critério, inserir origem e competência.',origin:'Pergunta inserida manualmente pelo recrutador',weight:2,differential:false});drawQuestions();$('questions').scrollTop=$('questions').scrollHeight};
$('saveQuestions').onclick=async()=>{try{state.editing.forEach((q,i)=>{const field=document.querySelector(`[data-edit="${i}"]`);if(field)q.question=field.value});const res=await call(`/api/admin/vacancies/${state.selectedVacancy}/questions`,{method:'PUT',headers:{'Content-Type':'application/json'},body:JSON.stringify({questions:state.editing})});state.editing=res.questions;drawQuestions();info('qMsg','Questionário salvo e pronto para ser usado com os candidatos.')}catch(err){info('qMsg',err.message,true)}};
$('candidateForm').onsubmit=async e=>{e.preventDefault();try{const body=new FormData();body.append('vacancy_id',$('candidateVacancy').value);body.append('name',$('candidateName').value.trim());body.append('linkedin_url',$('linkedinUrl').value.trim());body.append('linkedin_text',$('linkedinText').value.trim());for(const k of ['cv','disc','disc_comparativo','linkedin_pdf']){const f=$(`[name="${k}"]`)?.files?.[0];if(f)body.append(k,f)}const r=await call('/api/admin/candidates',{method:'POST',body});$('inviteResult').innerHTML=`<strong>Convite individual criado:</strong><div class="invite" id="createdInvite">${escapeHTML(r.invite)}</div><button type="button" class="btn small outline" id="copyInvite">Copiar endereço</button><p class="hint">Funciona no mesmo servidor. Respostas exclusivamente digitadas, com bloqueio de colagem.</p>`;$('inviteResult').classList.remove('hidden');$('copyInvite').onclick=()=>navigator.clipboard?.writeText(r.invite);$('candidateForm').reset();await refreshCandidates()}catch(err){info('inviteResult',err.message,true)}};
function drawCandidateList(){const el=$('candidateCards');el.innerHTML=state.candidates.length?'':'<p class="hint">Ainda não há candidatos.</p>';for(const c of state.candidates){const box=document.createElement('article');box.className='card';box.innerHTML=`<h3>${escapeHTML(c.name)}</h3><p>${escapeHTML(c.vacancy)}</p><p><span class="category">${escapeHTML(c.status)}</span></p><button type="button" class="btn small outline" data-open-candidate="${escapeHTML(c.id)}">Analisar entrevista</button>`;el.append(box)}el.querySelectorAll('[data-open-candidate]').forEach(x=>x.onclick=async()=>{showTab('reports');$('reportCandidate').value=x.dataset.openCandidate;await selectCandidate()})}
$('reportCandidate').onchange=selectCandidate;
$('materialsForm').onsubmit=async e=>{
 e.preventDefault();
 // Guarde o formulário ANTES do primeiro await: currentTarget deixa de existir após o despacho do evento.
 const form=e.currentTarget;
 const cid=state.selectedCandidate;
 if(!cid){info('materialsMsg','Selecione um candidato antes de anexar documentos.',true);return;}
 const fd=new FormData();
 let any=false;
 for(const name of ['cv','disc','disc_comparativo','linkedin_pdf']){
  const file=form.querySelector(`[name="${name}"]`)?.files?.[0];
  if(file && file.name){fd.append(name,file);any=true;}
 }
 if(!any){info('materialsMsg','Selecione pelo menos um documento.',true);return;}
 const sendButton=form.querySelector('button[type="submit"]');
 if(sendButton)sendButton.disabled=true;
 info('materialsMsg','Enviando documentos e extraindo o texto...');
 try{
  const result=await call(`/api/admin/candidates/${encodeURIComponent(cid)}/materials`,{method:'POST',body:fd});
  const extracted=result.extraido||{};
  const confirmation=(result.message||'Documentos recebidos.')+' Texto extraído: currículo '+(extracted.curriculo??0)+', DISC '+(extracted.disc??0)+', LinkedIn '+(extracted.linkedin??0)+' caracteres.';
  // Só apague os arquivos selecionados após o servidor confirmar o recebimento.
  form.reset();
  try{
   if(state.selectedCandidate===cid)await selectCandidate();
   info('materialsMsg',confirmation);
  }catch(refreshError){
   // Uma falha na atualização do painel NÃO deve transformar um upload concluído em erro de envio.
   info('materialsMsg',confirmation+' A atualização do painel falhou; recarregue a página para conferir os documentos.');
  }
 }catch(err){
  info('materialsMsg','Não foi possível confirmar o envio: '+err.message+'. Confira o status do candidato antes de tentar novamente.',true);
 }finally{if(sendButton)sendButton.disabled=false;}
};

$('reprocessDiscExisting').onclick=async()=>{
 const cid=state.selectedCandidate;
 if(!cid)return info('materialsMsg','Selecione um candidato primeiro.',true);
 if(!confirm('A releitura do DISC substitui a minuta não aprovada e exigirá nova revisão. Deseja continuar?'))return;
 const button=$('reprocessDiscExisting');button.disabled=true;
 try{
  const result=await call(`/api/admin/candidates/${encodeURIComponent(cid)}/reprocess-disc`,{method:'POST'});
  await selectCandidate();
  info('materialsMsg',(result.message||'DISC atualizado.')+' Dimensões reconhecidas: '+Object.entries(result.disc_values||{}).map(([k,v])=>k+v).join(', '));
 }catch(err){info('materialsMsg',err.message,true)}
 finally{button.disabled=false}
};
// Áudios históricos ficam acessíveis para transcrição manual, sem iniciar Whisper.
async function refreshTranscriptionStatus(cid){
 const data=await call(`/api/admin/candidates/${cid}/transcription-status`);
 if(state.selectedCandidate!==cid)return;
 $('transcriptionState').textContent=data.pending_audio
   ?`${data.pending_audio} áudio(s) de entrevistas anteriores sem transcrição. Ouça e transcreva manualmente as respostas abaixo; novas entrevistas usam apenas texto.`
   :'Novas entrevistas usam apenas respostas digitadas. Nenhuma transcrição de áudio é necessária.';
}
async function selectCandidate(){const cid=$('reportCandidate').value;if(!cid)return;state.selectedCandidate=cid;let c=await call(`/api/admin/candidates/${cid}`);
 if(c.status==='concluido'&&(!c.report || (!c.report.client_edited_at && !c.report.client_approved_at && !(c.report.client_sections?.tecnicas?.length && c.report.client_sections?.comportamentais?.length && c.report.client_sections?.recomendacao)))){
  try{info('analysisMsg','Preparando automaticamente a minuta com os documentos e respostas existentes.');
      await call(`/api/admin/candidates/${cid}/prepare-dossier`,{method:'POST'});
      c=await call(`/api/admin/candidates/${cid}`);
      info('analysisMsg','Minuta disponível para edição. Revise as três seções e aprove o parecer antes de exportar.');
  }catch(err){info('analysisMsg','Não foi possível preparar a minuta: '+err.message,true)}
 }
 state.detail=c;state.report=c.report;refreshTranscriptionStatus(cid).catch(()=>{});const section=c.report?.client_sections||{};
 $('clientTech').value=(section.tecnicas||[]).join('\n\n');
 $('clientBehavior').value=(section.comportamentais||[]).join('\n\n');
 $('clientRecommendation').value=section.recomendacao||c.report?.reviewer_comment||'';
 if($('clientReportState'))$('clientReportState').textContent=c.report?.client_approved_at
   ?`Parecer aprovado para envio em ${c.report.client_approved_at}. Qualquer alteração no texto exige nova aprovação.`
   :c.report?'Minuta preparada. Confira as fontes, edite as três seções, salve e clique em Aprovar parecer.':'Aguardando preparação da minuta.';
 const evidence=[c.cv_text?'Currículo ✓':'Currículo ausente',c.disc_text?'DISC ✓':'DISC ausente',c.linkedin_text?'LinkedIn exportado ✓':'LinkedIn não extraído'];$('reportCandidateInfo').textContent=`${c.vacancy} · ${c.status} · ${evidence.join(' · ')}`;const area=$('answersArea');area.innerHTML='';for(const q of c.questions){const a=c.answers[q.id],box=document.createElement('section');box.className='answerrow';box.innerHTML=`<strong>${escapeHTML(q.id)} · ${escapeHTML(q.category_label)}</strong><p>${escapeHTML(q.question)}</p>${a?.mode==='audio'?`<audio controls src="/api/admin/candidates/${cid}/audio/${encodeURIComponent(q.id)}"></audio><label>Transcrição do áudio<textarea rows="3" data-transcript="${escapeHTML(q.id)}" placeholder="Registre a transcrição fiel para análise">${escapeHTML(a.transcript||'')}</textarea><button type="button" class="btn small outline" data-save-transcript="${escapeHTML(q.id)}">Salvar transcrição</button>`:`<p class="hint">${escapeHTML(a?.text||'Sem resposta')}</p>`}`;area.append(box)}area.querySelectorAll('[data-save-transcript]').forEach(x=>x.onclick=async()=>{const qid=x.dataset.saveTranscript,text=area.querySelector(`[data-transcript="${qid}"]`).value;try{await call(`/api/admin/candidates/${cid}/transcripts/${qid}`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text})});info('analysisMsg',`Transcrição ${qid} salva. Gere novamente o dossiê.`)}catch(e){info('analysisMsg',e.message,true)}});drawReport()}
$('analyze').onclick=async()=>{if(!state.selectedCandidate)return;try{
 info('analysisMsg','Organizando as respostas escritas e as evidências disponíveis.');
 $('analyze').disabled=true;
 const task=await call(`/api/admin/candidates/${state.selectedCandidate}/analyze`,{method:'POST',body:new URLSearchParams({ollama_model:$('ollamaModel').value.trim(),auto_transcribe:'false'})});
 for(let tries=0;tries<1800;tries++){
   await new Promise(r=>setTimeout(r,1500));
   const j=await call(`/api/admin/jobs/${task.job_id}`);
   info('analysisMsg',`Análise ${j.status} · ${j.progress}/${j.total||'?'} critérios`);
   if(j.status==='failed')throw new Error(j.error||'A análise não pôde ser concluída.');
   if(j.status==='finished'){await selectCandidate();info('analysisMsg','Análise preliminar concluída. Confira cada evidência e ratifique ou retifique.');break;}
 }
}catch(err){info('analysisMsg',err.message,true)}finally{$('analyze').disabled=false}};
function drawReport(){
 const r=state.report,el=$('reportContent');
 if(!r){el.innerHTML='<p class="hint">Selecione um candidato e execute a análise técnica.</p>';return}
 const pct=n=>n==null?'N/D':n+'%';
 let html=`<div class="kpi"><div><strong>${pct(r.technical_percent)}</strong><small>ADERÊNCIA TÉCNICA EVIDENCIADA</small></div><div><strong>${pct(r.technical_coverage)}</strong><small>COBERTURA TÉCNICA</small></div></div>
 <div class="kpi"><div><strong>${pct(r.behavioral_percent)}</strong><small>Soft skills (sem DISC na nota)</small></div><div><strong>${pct(r.adherence_percent)}</strong><small>Aderência global evidenciada</small></div></div>
 <div class="origin"><strong>${escapeHTML(r.review_status||'Pendente de revisão')}</strong> · ${r.reviewed_count||0}/${r.reviewable_count||0} critérios analisados pelo recrutador</div>
 <p class="hint"><strong>Método:</strong> ${escapeHTML(r.analysis_mode)}</p>
 <p class="hint">A escala é 0–4. Sem evidência, o critério permanece sem nota e continua no denominador. Aderência não é aprovação. As notas da IA dependem de revisão humana.</p>`;
 for(const c of r.criteria){
   const proposal=c.auto_score;const value=c.score;
   const quoteList=(c.verified_excerpts||[]).map(x=>`<div class="origin"><strong>${escapeHTML(x.source)}:</strong> “${escapeHTML(x.excerpt)}”</div>`).join('');
   const warnings=(c.pending_validation||[]).map(x=>`<p class="hint">A validar: ${escapeHTML(x)}</p>`).join('');
   html+=`<article class="criterion"><div class="category">${escapeHTML(c.category)}${c.differential?' · Diferencial':''}</div>
       <strong>${escapeHTML(c.id)}. ${escapeHTML(c.criterion)}</strong>
       <p class="hint">Origem na vaga: ${escapeHTML(c.source_jd)}</p>
       <p><strong>Nota sugerida:</strong> ${proposal==null?'Sem evidência para nota':proposal+'/4'} · <strong>Nota vigente:</strong> ${value==null?'Sem nota':value+'/4'} · Peso ${c.weight}</p>
       <p><strong>Justificativa:</strong> ${escapeHTML(c.auto_reason||c.status)}</p>
       ${quoteList||'<p class="hint">A IA não identificou citação literal válida para este critério.</p>'}
       ${warnings}
       <div class="reviewgrid">
         <label>Decisão do recrutador<select data-decision="${escapeHTML(c.id)}"><option value="pendente">Pendente, sem alteração</option><option value="ratificar" ${c.review_decision==='ratificar'?'selected':''} ${proposal==null?'disabled':''}>Ratificar a nota sugerida</option><option value="retificar" ${c.review_decision==='retificar'?'selected':''}>Retificar ou acrescentar nota</option></select></label>
         <label>Nota humana<select data-human-score="${escapeHTML(c.id)}"><option value="">Sem evidência</option>${[0,1,2,3,4].map(v=>`<option value="${v}" ${(c.review_decision==='retificar'?c.human_score:c.auto_score)===v?'selected':''}>${v}/4</option>`).join('')}</select></label>
       </div>
       <label>Justificativa da revisão (obrigatória ao retificar)<textarea data-reason="${escapeHTML(c.id)}" rows="2" placeholder="Explique qual evidência levou à alteração">${escapeHTML(c.review_justification&&c.review_decision==='retificar'?c.review_justification:'')}</textarea></label>
       <small class="hint">Status: ${escapeHTML(c.status||'Pendente')}</small>
   </article>`;
 }
 const audit=r.draft_source_audit;
 if(audit){
  html+=`<details class="criterion"><summary><strong>Auditoria interna de fontes e revisões</strong></summary>
   <p class="hint">Critérios revisados incorporados à redação: ${Number(audit.criterios_revisados||0)} (técnicos: ${Number(audit.tecnicos||0)}; comportamentais: ${Number(audit.comportamentais||0)}).</p>
   <p class="hint">Currículo: ${audit.curriculo_disponivel?'disponível':'não identificado'} · DISC: ${audit.disc_disponivel?'disponível':'não identificado'} · LinkedIn: ${audit.linkedin_disponivel?'disponível':'não identificado'}.</p>
   ${(audit.alertas||[]).map(w=>`<p class="hint"><strong>Atenção:</strong> ${escapeHTML(w)}</p>`).join('')}
   ${(r.draft_technical_trace||[]).map(x=>`<p class="hint"><strong>Técnica · ${escapeHTML(x.criterio)}:</strong> ${escapeHTML(x.origem)} · ${escapeHTML(x.trecho||'Sem trecho localizado')}</p>`).join('')}
   ${(r.draft_behavior_trace||[]).filter(x=>x.criterio).map(x=>`<p class="hint"><strong>Comportamental · ${escapeHTML(x.criterio)}:</strong> ${escapeHTML(x.origem)} · ${escapeHTML(x.trecho||'Sem trecho localizado')}</p>`).join('')}
   <p class="hint">Este registro é exclusivo do painel e não é exibido no PDF do cliente.</p>
  </details>`;
 }
 if(r.client_requires_revalidation){html+='<p class="origin"><strong>O parecer precisa de nova conferência.</strong> As notas foram alteradas depois de uma edição do texto. Reavalie as três seções e salve novamente antes de aprovar.</p>';}
 html+=`<h3>DISC</h3><p>${escapeHTML(r.disc?.status||'Não fornecido')}</p><p class="hint">A avaliação DISC não modifica a aderência técnica nem substitui evidências comportamentais.</p>
 <h3>Condições eliminatórias</h3><p class="hint">Devem ser verificadas separadamente da nota técnica.</p>
 ${(r.eliminatorios_sugeridos||[]).map(x=>`<p>${escapeHTML(x.requisito||'')} · ${escapeHTML(x.estado||'não confirmado')} · ${escapeHTML(x.fundamento||'')}</p>`).join('')}
 <h3>Pendências</h3>${(r.pendencias||[]).map(x=>`<p class="hint">• ${escapeHTML(x)}</p>`).join('')}
 <label>Parecer do recrutador<textarea id="reviewerComment" rows="4" placeholder="Conclusões, riscos e validações que precisam ser confirmadas">${escapeHTML(r.reviewer_comment||'')}</textarea></label>
 <button type="button" id="saveReview" class="btn primary">Salvar ratificações e retificações</button>`;
 el.innerHTML=html;
 $('saveReview').onclick=async()=>{
   const decisions={};
   el.querySelectorAll('[data-decision]').forEach(node=>{
     const action=node.value;
     if(action==='pendente')return;
     const id=node.dataset.decision;
     const input=el.querySelector(`[data-human-score="${id}"]`),note=el.querySelector(`[data-reason="${id}"]`);
     decisions[id]={action,score:input.value===''?null:Number(input.value),justification:note.value};
   });
   try{
      state.report=await call(`/api/admin/candidates/${state.selectedCandidate}/review`,{
        method:'POST',headers:{'Content-Type':'application/json'},
        body:JSON.stringify({decisions,comment:$('reviewerComment').value})
      });
      if(!state.report.client_requires_revalidation && state.report.client_sections){
        const p=state.report.client_sections;
        $('clientTech').value=(p.tecnicas||[]).join('\n\n');
        $('clientBehavior').value=(p.comportamentais||[]).join('\n\n');
        $('clientRecommendation').value=p.recomendacao||'';
      }
      drawReport();
      info('analysisMsg',state.report.client_requires_revalidation
        ? 'Notas salvas. O texto já editado foi preservado; revise e salve novamente o parecer antes de aprovar.'
        : 'Notas salvas e texto do parecer atualizado com as avaliações ratificadas ou retificadas. Confira as três seções antes de aprovar.');
   }catch(err){info('analysisMsg',err.message,true)}
 };
}
$('previewPdf').onclick=async()=>{if(!state.selectedCandidate)return;
 const url=`/api/admin/candidates/${state.selectedCandidate}/report-preview.pdf`;
 try{const res=await fetch(url);if(!res.ok){let x;try{x=await res.json()}catch{}throw new Error(x?.detail||'Prévia indisponível')}
  const b=await res.blob(),u=URL.createObjectURL(b),a=document.createElement('a');a.href=u;a.download='minuta_parecer.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(u),3000);
 }catch(e){info('analysisMsg',e.message,true)}
};
$('downloadPdf').onclick=async()=>{if(!state.selectedCandidate)return;const url=`/api/admin/candidates/${state.selectedCandidate}/report.pdf`;
 try{const res=await fetch(url);if(!res.ok){let x;try{x=await res.json()}catch{}throw new Error(x?.detail||'Parecer indisponível')};const blob=await res.blob();const u=URL.createObjectURL(blob);const a=document.createElement('a');a.href=u;a.download='parecer_cliente.pdf';a.click();setTimeout(()=>URL.revokeObjectURL(u),3000)}catch(e){info('analysisMsg',e.message,true)}};
$('downloadInternalPdf').onclick=()=>{if(state.selectedCandidate)location.href=`/api/admin/candidates/${state.selectedCandidate}/report-interno.pdf`};
$('saveClientReport').onclick=async()=>{
 if(!state.selectedCandidate){info('analysisMsg','Selecione um candidato antes de salvar.',true);return}
 try{const data={tecnicas:$('clientTech').value,comportamentais:$('clientBehavior').value,recomendacao:$('clientRecommendation').value};
  await call(`/api/admin/candidates/${state.selectedCandidate}/client-report`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});
  info('analysisMsg','Texto salvo. Para emitir o documento final, confira a prévia e aprove o parecer.');
  await selectCandidate();
 }catch(err){info('analysisMsg',err.message,true)}
};
$('approveClientReport').onclick=async()=>{
 const cid=state.selectedCandidate;
 if(!cid)return info('analysisMsg','Selecione um candidato.',true);
 const sections={tecnicas:$('clientTech').value.trim(),comportamentais:$('clientBehavior').value.trim(),recomendacao:$('clientRecommendation').value.trim()};
 if(!sections.tecnicas || !sections.comportamentais || !sections.recomendacao){
   const missing=[!sections.tecnicas?'Competências Técnicas':null,!sections.comportamentais?'Competências Comportamentais':null,!sections.recomendacao?'Parecer de Recomendação':null].filter(Boolean).join(', ');
   return info('analysisMsg','Preencha as seções antes de aprovar: '+missing+'.',true);
 }
 if(!confirm('Confirma que conferiu as fontes e revisou as três seções? O texto será salvo, aprovado e o PDF será gerado para o cliente.'))return;
 const button=$('approveClientReport');button.disabled=true;
 info('analysisMsg','Salvando, aprovando e gerando o PDF. Não feche a página.');
 try{
   const res=await fetch(`/api/admin/candidates/${encodeURIComponent(cid)}/approve-and-export.pdf`,{
      method:'POST',headers:{'Content-Type':'application/json'},credentials:'same-origin',
      body:JSON.stringify({confirmed:true,...sections}),cache:'no-store'
   });
   if(!res.ok){let error;try{error=await res.json()}catch{}throw new Error(error?.detail||`Não foi possível gerar o PDF (HTTP ${res.status}).`)}
   const blob=await res.blob();
   if(!blob.size || !(await blob.slice(0,5).text()).startsWith('%PDF-'))throw new Error('O servidor não retornou um PDF válido. Use Baixar parecer aprovado PDF para tentar novamente.');
   const href=URL.createObjectURL(blob),link=document.createElement('a');
   link.href=href;link.download=`parecer_cliente_${cid}.pdf`;document.body.append(link);link.click();link.remove();
   setTimeout(()=>URL.revokeObjectURL(href),60000);
   info('analysisMsg','Parecer aprovado e PDF gerado. Se o navegador não tiver iniciado o download, clique em Baixar parecer aprovado PDF.');
   await selectCandidate();
 }catch(err){info('analysisMsg','Não foi possível concluir: '+err.message+' Nenhum texto digitado foi descartado.',true)}
 finally{button.disabled=false}
};
$('downloadJson').onclick=()=>{if(state.selectedCandidate)location.href=`/api/admin/candidates/${state.selectedCandidate}/report.json`};

function atualizarLogoPreview(){
  const logo=$('logoPreview');
  if(!logo)return;
  logo.onload=()=>logo.style.display='block';
  logo.onerror=()=>logo.style.display='none';
  logo.src='/api/brand/logo?preview='+Date.now();
}
atualizarLogoPreview();
$('saveLogo').onclick=async()=>{
 const file=$('logoUpload').files[0];if(!file)return $('logoMessage').textContent='Selecione uma imagem PNG ou JPG.';
 try{const data=new FormData();data.append('file',file);await call('/api/admin/brand/logo',{method:'POST',body:data});$('logoMessage').textContent='Logotipo salvo para os pareceres em PDF. Não aparece nas entrevistas.';atualizarLogoPreview()}
 catch(e){$('logoMessage').textContent=e.message}
};
$('removeLogo').onclick=async()=>{
 try{await call('/api/admin/brand/logo',{method:'DELETE'});$('logoMessage').textContent='Logotipo removido. Os pareceres terão cabeçalho neutro.';atualizarLogoPreview()}
 catch(e){$('logoMessage').textContent=e.message}
};
$('backup').onclick=()=>{location.href='/api/admin/backup.zip'};
$('restoreForm').onsubmit=async e=>{
 e.preventDefault();
 if(!activeUser || activeUser.role!=='administrador')return info('restoreMsg','Somente administradores podem restaurar backups.',true);
 const f=$('restoreFile').files[0];const confirmation=$('restoreConfirmation').value;
 if(!f || !f.name.toLowerCase().endsWith('.zip'))return info('restoreMsg','Selecione um backup em formato ZIP.',true);
 if(confirmation!=='RESTAURAR BACKUP')return info('restoreMsg','Digite exatamente RESTAURAR BACKUP.',true);
 if(!confirm('ATENÇÃO: a restauração substituirá usuários, vagas, candidatos, entrevistas, áudios e pareceres atuais. Fez um backup do estado atual?'))return;
 const button=$('restoreButton');button.disabled=true;
 info('restoreMsg','Enviando e verificando backup. Não atualize a página durante a restauração.');
 try{
  const form=new FormData();form.append('file',f);form.append('confirmation',confirmation);
  const result=await call('/api/admin/backup/restore',{method:'POST',body:form});
  info('restoreMsg',result.message||'Backup restaurado. Faça login novamente.');
  alert('Backup restaurado. Todas as sessões foram encerradas. Entre novamente com uma conta existente no backup ou com a senha principal do Render.');
  location.reload();
 }catch(err){info('restoreMsg','Restauração não concluída: '+err.message,true)}
 finally{button.disabled=false}
};


$('draftClientReport').onclick=async()=>{if(!state.selectedCandidate)return;
 const campos=[$('clientTech'),$('clientBehavior'),$('clientRecommendation')];
 if(campos.some(el=>el?.value.trim()) && !confirm('Gerar nova proposta de redação? Isso substituirá o texto atualmente nos campos, mas não altera o parecer salvo ou aprovado até você salvar novamente.'))return;
 try{info('analysisMsg','Preparando proposta de redação fundamentada para revisão editorial.');
 const d=await call(`/api/admin/candidates/${state.selectedCandidate}/client-draft`,{method:'POST'});
 $('clientTech').value=(d.tecnicas||[]).join('\n\n');
 $('clientBehavior').value=(d.comportamentais||[]).join('\n\n');
 $('clientRecommendation').value=d.recomendacao||$('clientRecommendation').value;
 info('analysisMsg',`Minuta preenchida (${d.modo||'redação documental'}). Revise as evidências e a recomendação, salve e aprove. ${d.aviso||''}`);
 }catch(e){info('analysisMsg',e.message,true)}
};

$('regenerateQuestions').onclick=async()=>{
 if(!state.selectedVacancy)return info('qMsg','Selecione a vaga para regenerar as perguntas.',true);
 if(!confirm('Isso substituirá o questionário atual desta vaga pelo roteiro derivado da descrição. Quer continuar?'))return;
 try{
  info('qMsg','Gerando roteiro específico com base na descrição da vaga.');
  const data=await call(`/api/admin/vacancies/${state.selectedVacancy}/regenerate-questions`,{method:'POST'});
  state.editing=data.questions;drawQuestions();
  info('qMsg',`${data.generated} perguntas preparadas. Confira responsabilidades, hard skills e soft skills. ${data.warnings.join(' ')}`);
 }catch(e){info('qMsg',e.message,true)}
};

// Gestão de usuários: acessível apenas ao administrador.
async function refreshStaffUsers(){
 if(!activeUser||activeUser.role!=='administrador')return;
 const people=await call('/api/admin/users');const list=$('staffList');list.innerHTML='';
 if(!people.length){list.innerHTML='<p class="hint">Nenhum usuário adicional cadastrado.</p>';return;}
 for(const u of people){
  const card=document.createElement('article');card.className='card';
  card.innerHTML=`<h3>${escapeHTML(u.name)}</h3><p>${escapeHTML(u.email)}</p><p>${u.role==='administrador'?'Administrador':'Recrutador'} · ${u.active?'Ativo':'Inativo'} ${u.must_change_password?'· Troca de senha pendente':''}</p><div class="buttonrow"><button type="button" class="btn outline small" data-status="${escapeHTML(u.id)}">${u.active?'Desativar':'Ativar'}</button><button type="button" class="btn outline small" data-reset="${escapeHTML(u.id)}">Redefinir senha</button></div>`;
  list.append(card);
  card.querySelector('[data-status]').onclick=async()=>{if(!confirm(`${u.active?'Desativar':'Ativar'} o acesso de ${u.name}?`))return;try{await call(`/api/admin/users/${u.id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({active:!u.active})});await refreshStaffUsers();}catch(e){info('usersMsg',e.message,true)}};
  card.querySelector('[data-reset]').onclick=()=>{$('resetLabel').textContent='Usuário: '+u.name+' ('+u.email+')';window.resetUserId=u.id;$('resetPanel').classList.remove('hidden');$('resetPasswordValue').value='';$('resetPasswordConfirm').value='';$('resetPanel').scrollIntoView({behavior:'smooth',block:'nearest'});};
 }
}
$('createUserForm').onsubmit=async e=>{e.preventDefault();try{if($('staffPassword').value!==$('staffPasswordConfirm').value)throw new Error('As senhas não coincidem.');const data={name:$('staffName').value.trim(),email:$('staffEmail').value.trim(),role:$('staffRole').value,password:$('staffPassword').value};await call('/api/admin/users',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(data)});$('createUserForm').reset();info('usersMsg','Conta criada. Compartilhe o e-mail e a senha provisória em canal seguro; a pessoa deverá alterá-la ao entrar.');await refreshStaffUsers();}catch(err){info('usersMsg',err.message,true)}};

$('cancelReset').onclick=()=>{$('resetPanel').classList.add('hidden');window.resetUserId=null};
$('resetPasswordForm').onsubmit=async e=>{e.preventDefault();if(!window.resetUserId)return;try{
  if($('resetPasswordValue').value!==$('resetPasswordConfirm').value)throw new Error('As senhas não coincidem.');
  await call(`/api/admin/users/${window.resetUserId}/reset-password`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({new_password:$('resetPasswordValue').value})});
  $('resetPanel').classList.add('hidden');window.resetUserId=null;info('usersMsg','Senha provisória redefinida. Compartilhe-a com o usuário por canal seguro.');await refreshStaffUsers();
}catch(e){info('usersMsg',e.message,true)}};

})();
