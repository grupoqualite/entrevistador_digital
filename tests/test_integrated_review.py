"""Casos fictícios de regressão, sem dados reais de candidatos."""
import os,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from technical_engine import prepare_report,update_review
from evidence_draft import draft_from_sources

class IntegratedReviewTest(unittest.TestCase):
    def setUp(self):
        self.questions=[
            {'id':'Q01','category':'responsabilidade','criterion':'Atendimento aos clientes por WhatsApp e presencialmente','origin':'Atendimento comercial','weight':3},
            {'id':'Q02','category':'hard','criterion':'Conferência de medicamentos e pedidos','origin':'Conferência de medicamentos e pedidos','weight':3},
            {'id':'Q03','category':'soft','criterion':'Organização, comunicação e atenção aos detalhes','origin':'Organização e atenção aos detalhes','weight':2},
        ]
        self.answers={
            'Q01':{'mode':'texto','text':'Atendi clientes na loja, ouvi suas necessidades e registrei os pedidos no sistema.'},
            'Q02':{'mode':'texto','text':'Nunca conferi medicamentos antes da entrega, apenas produtos de higiene.'},
            'Q03':{'mode':'texto','text':'Organizei os pedidos, expliquei atrasos aos clientes e verifiquei os registros para evitar divergências.'}
        }
        self.cv='Trabalhou em loja com atendimento de balcão, CRM e organização de pedidos. Elaborou relatórios semanais de acompanhamento.'
        self.disc='DISC: Estabilidade elevada, Conformidade alta e Dominância baixa. Descrito com cautela e preferência por procedimentos.'
        self.report=prepare_report(self.questions,self.answers,self.cv,self.disc,'','','Auxiliar de Farmácia','Pessoa Fictícia','Descrição de vaga fictícia')

    def test_unreviewed_conservative(self):
        d=draft_from_sources(self.report,self.cv,'',self.disc)
        self.assertEqual(d['auditoria_cruzamento']['criterios_revisados'],0)
        self.assertEqual(len(d['evidencias_tecnicas_internas']),0)

    def test_reviewed_scores_cross_both_categories(self):
        update_review(self.report,{
          'Q01':{'action':'retificar','score':3,'justification':'A experiência direta de atendimento foi descrita.'},
          'Q02':{'action':'retificar','score':0,'justification':'O candidato informou que não fez conferência de medicamentos.'},
          'Q03':{'action':'retificar','score':3,'justification':'O relato evidencia organização, comunicação e conferência de registros.'}
        })
        d=draft_from_sources(self.report,self.cv,'',self.disc)
        audit=d['auditoria_cruzamento']
        self.assertEqual(audit['tecnicos'],2)
        self.assertEqual(audit['comportamentais'],1)
        self.assertTrue(audit['disc_disponivel'])
        self.assertTrue(d['evidencias_tecnicas_internas'])
        self.assertTrue(d['evidencias_comportamentais_internas'])
        self.assertIn('ausência de experiência', ' '.join(d['tecnicas']).lower())
        self.assertIn('organização', ' '.join(d['comportamentais']).lower())
        self.assertIn('DISC', ' '.join(d['comportamentais']))
        client=' '.join(d['tecnicas']+d['comportamentais']+[d['recomendacao']]).lower()
        for forbidden in ('na resposta q01','na resposta q02','perfil profissional exportado', 'nota sugerida', 'peso 3','ia local','método de cálculo'):
            self.assertNotIn(forbidden,client)

    def test_human_rating_overrides_auto(self):
        c=self.report['criteria'][0]
        c['auto_score']=4
        update_review(self.report,{'Q01':{'action':'retificar','score':1,'justification':'A narrativa não comprova domínio suficiente.'}})
        self.assertEqual(self.report['criteria'][0]['score'],1)
        d=draft_from_sources(self.report,self.cv,'',self.disc)
        self.assertIn('faltam exemplos', ' '.join(d['tecnicas']).lower())

    def test_unrelated_response_does_not_support_high_technical_score(self):
        self.report['criteria'][1]['answer']='Trabalhei com organização de eventos e elaboração de campanhas digitais.'
        update_review(self.report,{'Q02':{'action':'retificar','score':4,'justification':'A experiência teria relevância, mas precisa de confirmação.'}})
        d=draft_from_sources(self.report,self.cv,'',self.disc)
        flagged=' '.join(d['auditoria_cruzamento']['alertas']).lower()
        self.assertIn('sem relato positivo',flagged)
        self.assertNotIn('na dimensão de conferência', ' '.join(d['tecnicas']).lower())

    def test_disc_not_enough_to_create_positive_review(self):
        for row in self.report['criteria']:
            row['answer']=''
        update_review(self.report,{'Q03':{'action':'retificar','score':4,'justification':'Perfil comportamental parece adequado, mas faltam episódios.'}})
        d=draft_from_sources(self.report,'Atuou anteriormente na produção industrial com atividades de embalagem e supervisão de máquinas.','',self.disc)
        # Nenhum traço do DISC autoriza tratar a competência como comprovada.
        self.assertTrue(d['auditoria_cruzamento']['alertas'])

if __name__=='__main__':unittest.main()
