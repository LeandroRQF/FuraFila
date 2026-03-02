# requests biblioteca para realizar requisições HTTP
# requests.auth classe utilizada para autenticação Basic Auth na API
# config importa as credenciais e configurações da aplicação definidas no arquivo config.py
# notifier importa a função send_teams_message, responsável por enviar mensagens para o Microsoft Teams
# datetime biblioteca para manipulação de datas e horários
# zoneinfo biblioteca para conversão de fuso horário (Python 3.9+)
import requests
from requests.auth import HTTPBasicAuth
from config import ZENDESK_SUBDOMAIN, ZENDESK_EMAIL, ZENDESK_API_TOKEN
from notifier import send_teams_message
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import unicodedata

print("Aplicação iniciada")

# ==========================================================
# FUNÇÃO: buscar_por_palavra
# Objetivo:
# Consultar a API do Zendesk e retornar tickets novos e abertos criados nas últimas 5 horas que contenham a palavra-chave definida
# ==========================================================
def buscar_por_palavra(palavra):
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/search.json"

    query = f"type:ticket status:new status:open created>1hours {palavra}"

    print(f"Buscando por: {palavra}")
    print("QUERY:", query)

    response = requests.get(
        url,
        params={"query": query},
        auth=HTTPBasicAuth(f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN),
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Encontrados {data.get('count')} para '{palavra}'")
        return data.get("results", [])
    else:
        print(f"Erro ao buscar '{palavra}':", response.text)
        return []
    

# ==========================================================
# FUNÇÃO: buscar_tickets_multiplas_palavras
# Objetivo:
# Consultar a API do Zendesk e retornar tickets que contenham qualquer uma das palavras-chave pré-definidas
# utiliza a função buscar_por_palavra para cada termo e consolida resultados evitando duplicação
# ==========================================================    
def buscar_tickets_multiplas_palavras(palavras):
    todos_tickets = {}

    for palavra in palavras:
        resultados = buscar_por_palavra(palavra)

        for ticket in resultados:
            # Usa ID como chave para evitar duplicação
            todos_tickets[ticket["id"]] = ticket

    print(f"Total consolidado (sem duplicados): {len(todos_tickets)}")

    return list(todos_tickets.values())
    

# ==========================================================
# FUNÇÃO: carregar_tickets_notificados
# Objetivo:
# Ler arquivo local que armazena IDs de tickets já notificados, evita envio duplicado ao Teams.
# ==========================================================
def carregar_tickets_notificados():
    try:
        tickets = set()

        with open("notified_tickets.txt", "r") as f:
            for linha in f:
                partes = linha.strip().split("|")
                ticket_id = partes[0]
                tickets.add(ticket_id)

        return tickets

    except FileNotFoundError:
        return set()


# ==========================================================
# FUNÇÃO: limpar_tickets_antigos
# Objetivo:
# Remover do arquivo tickets notificados há mais de X dias
# ==========================================================
def limpar_tickets_antigos(dias=3):

    try:
        linhas_validas = []
        agora = datetime.now(timezone.utc)
        limite = agora - timedelta(days=dias)

        with open("notified_tickets.txt", "r") as f:
            for linha in f:
                partes = linha.strip().split("|")

                if len(partes) != 2:
                    continue  # ignora linha mal formatada

                ticket_id, data_str = partes

                try:
                    data_ticket = datetime.fromisoformat(data_str)

                    if data_ticket >= limite:
                        linhas_validas.append(linha.strip())

                except Exception:
                    continue  # ignora erro de conversão

        # Reescreve arquivo apenas com tickets recentes
        with open("notified_tickets.txt", "w") as f:
            for linha in linhas_validas:
                f.write(linha + "\n")

        print(f"Limpeza concluída. {len(linhas_validas)} tickets mantidos.")

    except FileNotFoundError:
        pass


# ==========================================================
# FUNÇÃO: salvar_ticket_notificado
# Objetivo:
# Registrar no arquivo local o ID de um ticket já enviado
# ==========================================================
def salvar_ticket_notificado(ticket_id):
    data_envio = datetime.now(timezone.utc).isoformat()

    with open("notified_tickets.txt", "a") as f:
        f.write(f"{ticket_id}|{data_envio}\n")


# ==========================================================
# FUNÇÃO: remover_acentos
# Objetivo:
# Normalizar texto removendo acentuação para melhorar robustez da busca
# ==========================================================
def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


# ==========================================================
# FUNÇÃO PRINCIPAL
# Objetivo:
# Orquestrar fluxo completo:
# - Limpeza de histórico
# - Busca de tickets
# - Filtro de duplicidade
# - Conversão de data
# - Envio de alertas
# ==========================================================
def main():

    # LIMPA tickets antigos antes de tudo
    limpar_tickets_antigos(dias=7)

    # Lista estratégica de palavras-chave para detecção de risco operacional, urgência e possível insatisfação do cliente.
    palavras_originais = ["urgente", "urgência",  "imediatamente", "o quanto antes", "hoje ainda", "até amanhã", 
                          "até hoje", "para hoje", "pra hoje", "para amanhã", "pra amanhã", "faturamento", 
                          "insatisfação", "insatisfeito", "insatisfeita", "péssimo", "péssima", "ruim",
                          "horrível", "decepcionado", "decepcionada", "frustrado", "indignada", "indignado", 
                          "descaso", "falta de retorno", "ninguém responde"]

    # Normaliza palavras incluindo versões com e sem acento para evitar falhas na busca da API do Zendesk.
    palavras = []

    for palavra in palavras_originais:
        palavras.append(palavra)
        palavras.append(remover_acentos(palavra))

    palavras = list(set(palavras))
    tickets = buscar_tickets_multiplas_palavras(palavras)

    # Carrega tickets já notificados anteriormente
    tickets_notificados = carregar_tickets_notificados()
    
    if not tickets:
        print("Nenhum ticket encontrado.")
        return

    novos_enviados = 0 

    # Percorre todos os tickets encontrados
    for ticket in tickets:

        # Verifica se o ticket ainda não foi notificado
        if str(ticket["id"]) not in tickets_notificados:

            # Recupera prioridade (se não existir, define padrão)
            prioridade = ticket.get("priority") or "Não definida"

            # ==================================================
            # Conversão de Data (UTC → America/Sao_Paulo)
            # ==================================================

            # Data original vem em UTC no formato ISO 8601
            data_original = ticket['created_at']

            # Converte string para objeto datetime UTC
            data_utc = datetime.strptime(
                data_original,
                "%Y-%m-%dT%H:%M:%SZ"
            ).replace(tzinfo=ZoneInfo("UTC"))

            # Converte para fuso horário do Brasil
            data_local = data_utc.astimezone(
                ZoneInfo("America/Sao_Paulo")
            )

            # Formata para padrão brasileiro
            data_formatada = data_local.strftime(
                "%d/%m/%Y - hora: %H:%M"
            )

            # ==================================================
            # Montagem da mensagem
            # ==================================================

            mensagem = f"""
            🚨 TICKET URGENTE 🚨
            ID: {ticket['id']}
            Data: {data_formatada}
            Assunto: {ticket.get('subject', 'Sem assunto')}
            Prioridade: {prioridade}
            Link: https://{ZENDESK_SUBDOMAIN}.zendesk.com/agent/tickets/{ticket['id']}
            """

            print("Enviando mensagem para Teams...")
            
            # Envia mensagem para o Teams
            enviado = send_teams_message(mensagem)

            if enviado:
                # Salva ID para evitar reenvio futuro
                salvar_ticket_notificado(ticket["id"])
                novos_enviados += 1
            else:
                print(f"Falha ao notificar ticket {ticket['id']}.")
    
    # ==================================================
    # Logs finais
    # ==================================================
    if novos_enviados == 0:
        print(f"{len(tickets)} tickets encontrados, mas todos já foram notificados.")
    else:
        print(f"{novos_enviados} novo(s) ticket(s) enviado(s) com sucesso.")


# Executa a função principal apenas se o arquivo for executado diretamente
if __name__ == "__main__":
    main()