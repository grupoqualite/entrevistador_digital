// V9.6.5: entrevistas novas exclusivamente por texto.
const $ = id => document.getElementById(id);
const token=decodeURIComponent(location.pathname.split('/').pop());
let data=null,idx=0;
const showErr=message=>{ $('interviewMsg').textContent=message||''; };
window.addEventListener('DOMContentLoaded',()=>{
  const logo=$('candidateLogo');
  logo.onload=()=>{logo.style.display='block';$('fallbackBrand').style.display='none'};
  logo.onerror=()=>{logo.style.display='none'};
});
async function send(url,options={}){
  const r=await fetch(url,options);let body;
  try{body=await r.json()}catch{body={detail:'Falha de comunicação.'}}
  if(!r.ok)throw new Error(body.detail||`Erro ${r.status}`);
  return body;
}
function done(){
  $('interviewBody').classList.add('hidden');
  $('finished').classList.remove('hidden');
  $('greeting').textContent='Entrevista finalizada';
  $('vacancyName').textContent='';
}
function showQuestion(){
  if(!data||idx>=data.questions.length)return;
  const q=data.questions[idx];
  $('questionBox').textContent=q.question;
  $('stepText').textContent=`Pergunta ${idx+1} de ${data.questions.length} · ${q.category_label}`;
  const progress=Math.round(idx/data.questions.length*100);
  $('stepPercent').textContent=`${progress}%`;
  $('progressFill').style.width=`${progress}%`;
  $('next').textContent=idx===data.questions.length-1?'Concluir entrevista':'Salvar e continuar';
  $('prev').disabled=idx===0;
  $('answerText').value='';
  showErr(data.answered[q.id]?'Esta pergunta já foi respondida. Você pode continuar sem substituir a resposta ou digitar outra resposta.':'');
}
async function init(){
  try{
    data=await send(`/api/invites/${token}`);
    $('greeting').textContent=`Olá, ${data.candidate}!`;
    $('vacancyName').textContent=`Entrevista para a vaga de ${data.vacancy}`;
    if(data.status==='concluido'){done();return}
    showQuestion();
  }catch(error){
    $('questionBox').textContent='Convite indisponível: '+error.message;
    $('next').disabled=true;
  }
}
$('prev').onclick=()=>{if(idx>0){idx--;showQuestion()}};
$('next').onclick=async()=>{
  if(!data||!data.questions[idx])return;
  const q=data.questions[idx];
  const answer=$('answerText').value.trim();
  const previouslyAnswered=Boolean(data.answered[q.id]);
  if(!answer&&!previouslyAnswered)return showErr('Digite sua resposta antes de continuar.');
  if(answer.length>0&&answer.length<3)return showErr('Digite uma resposta com pelo menos 3 caracteres.');
  $('next').disabled=true;showErr('Salvando resposta...');
  try{
    if(answer){
      const fd=new FormData();
      fd.append('question_id',q.id);
      fd.append('text',answer);
      await send(`/api/invites/${token}/answer`,{method:'POST',body:fd});
      data.answered[q.id]=true;
    }
    if(idx===data.questions.length-1){
      await send(`/api/invites/${token}/complete`,{method:'POST'});done();
    }else{idx++;showQuestion()}
  }catch(error){showErr(error.message)}
  finally{$('next').disabled=false}
};
const textArea=$('answerText');
textArea.addEventListener('paste',e=>{e.preventDefault();showErr('A função colar está desabilitada. Digite sua resposta.')});
textArea.addEventListener('drop',e=>{e.preventDefault();showErr('Não é permitido arrastar texto para este campo.')});
textArea.addEventListener('beforeinput',e=>{if(['insertFromPaste','insertFromDrop'].includes(e.inputType)){e.preventDefault();showErr('A colagem está desabilitada.')}});
textArea.addEventListener('keydown',e=>{if((e.ctrlKey||e.metaKey)&&e.key.toLowerCase()==='v'){e.preventDefault();showErr('A função colar está desabilitada.')}});
textArea.addEventListener('contextmenu',e=>e.preventDefault());
init();
