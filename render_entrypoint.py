"""Inicialização específica para Render. Não contém credenciais."""
import os
import uvicorn

# Render disponibiliza o endereço HTTPS como variável de ambiente.
if not os.environ.get('ENTREVISTADOR_PUBLIC_URL'):
    public_url = os.environ.get('RENDER_EXTERNAL_URL', '').strip().rstrip('/')
    if not public_url.startswith('https://'):
        raise SystemExit('RENDER_EXTERNAL_URL indisponível: configure ENTREVISTADOR_PUBLIC_URL com HTTPS.')
    os.environ['ENTREVISTADOR_PUBLIC_URL'] = public_url
os.environ.setdefault('ENTREVISTADOR_ENV', 'production')
os.environ.setdefault('ENTREVISTADOR_DATA', '/app/dados')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', '10000'))
    uvicorn.run('server:APP',host='0.0.0.0',port=port,workers=1,proxy_headers=True,forwarded_allow_ips='*')
