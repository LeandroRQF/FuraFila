# Importa o módulo 'os', que permite acessar variáveis de ambiente e outras funcionalidades relacionadas ao sistema operacional.
# Importa a função 'load_dotenv' da biblioteca python-dotenv. Essa função permite carregar variáveis de ambiente a partir de um arquivo .env.
import os
import sys
from dotenv import load_dotenv


# ==========================================================
# Carrega o arquivo .env corretamente tanto no .py quanto no .exe
# ==========================================================

if getattr(sys, 'frozen', False):
    # Se estiver rodando como executável (.exe)
    base_path = os.path.dirname(sys.executable)
else:
    # Se estiver rodando como script Python (.py)
    base_path = os.path.dirname(__file__)

env_path = os.path.join(base_path, ".env")
load_dotenv(env_path)


# ==========================================================
# CONFIGURAÇÃO DE AMBIENTE
# ==========================================================
load_dotenv()

# Variáveis de autenticação Zendesk
ZENDESK_SUBDOMAIN = os.getenv("ZENDESK_SUBDOMAIN")
ZENDESK_EMAIL = os.getenv("ZENDESK_EMAIL")
ZENDESK_API_TOKEN = os.getenv("ZENDESK_API_TOKEN")

# Recupera a URL do webhook do Microsoft Teams. Essa URL é utilizada para enviar mensagens automáticas para um canal específico do Teams.
TEAMS_WEBHOOK_URL = os.getenv("TEAMS_WEBHOOK_URL")


# ==============================
# Validação de segurança
# ==============================

# Verifica se todas as variáveis necessárias foram carregadas corretamente. 
# A função all() retorna True apenas se todos os valores da lista existirem.
# Caso alguma variável esteja vazia ou não definida, a aplicação será interrompida com um erro explícito.
if not all([ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN, TEAMS_WEBHOOK_URL]):
    raise ValueError("Variáveis de ambiente não configuradas corretamente.")