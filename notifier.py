# Importa a biblioteca requests, responsável por realizar requisições HTTP.
import requests

# Importa a exceção específica para tratar erros relacionados a requisições HTTP
# (como timeout, falha de conexão, erro 4xx ou 5xx).
from requests.exceptions import RequestException

# Importa a URL do Webhook do Microsoft Teams definida no arquivo de configuração.
# Essa URL é o endpoint que receberá a mensagem via POST.
from config import TEAMS_WEBHOOK_URL


# ==========================================================
# Função: send_teams_message
# Objetivo:
# Enviar uma mensagem para um canal do Microsoft Teams
# utilizando um Webhook previamente configurado.
#
# Parâmetro:
#   message (str) -> Texto que será enviado ao canal do Teams.
#
# Retorno:
#   True  -> Envio realizado com sucesso
#   False -> Falha no envio
# ==========================================================
def send_teams_message(message):
    try:
        # Monta o payload no formato esperado pelo Webhook do Teams.
        # O Teams exige um JSON contendo a chave "text" com o conteúdo da mensagem.
        payload = {
            "text": message
        }

        # Realiza uma requisição HTTP do tipo POST para o Webhook.
        # O parâmetro timeout=10 impede que a aplicação fique aguardando
        # indefinidamente em caso de falha de conexão.
        response = requests.post(
            TEAMS_WEBHOOK_URL,
            json=payload,
            timeout=10
        )

        # Lança automaticamente uma exceção caso o status HTTP seja 4xx ou 5xx.
        # Se não houver erro, a execução continua normalmente.
        response.raise_for_status()

        # Se chegou até aqui, o envio foi concluído com sucesso.
        return True

    except RequestException as e:
        # Captura apenas erros relacionados à requisição HTTP,
        # como problemas de conexão, timeout ou erro retornado pelo servidor.
        print(f"Erro ao enviar mensagem para o Teams: {e}")
        return False