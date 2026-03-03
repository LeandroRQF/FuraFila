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
import time

print("Aplicação iniciada")

# ==========================================================
# FUNÇÃO: buscar_tickets_recentes
# Objetivo:
# Buscar tickets novos e abertos criados nos últimos 15 minutos
# ==========================================================
def buscar_tickets_recentes():
    url = f"https://{ZENDESK_SUBDOMAIN}.zendesk.com/api/v2/search.json"

    query = "type:ticket status:new status:open created>15minutes"

    print("Buscando tickets recentes...")
    print("QUERY:", query)

    response = requests.get(
        url,
        params={"query": query},
        auth=HTTPBasicAuth(f"{ZENDESK_EMAIL}/token", ZENDESK_API_TOKEN),
        timeout=10
    )

    if response.status_code == 200:
        data = response.json()
        print(f"Encontrados {data.get('count')} tickets recentes")
        return data.get("results", [])
    else:
        print("Erro na busca:", response.text)
        return []


# ==========================================================
# FUNÇÃO: carregar_tickets_notificados
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
# ==========================================================
def limpar_tickets_antigos(dias=7):
    try:
        linhas_validas = []
        agora = datetime.now(timezone.utc)
        limite = agora - timedelta(days=dias)

        with open("notified_tickets.txt", "r") as f:
            for linha in f:
                partes = linha.strip().split("|")

                if len(partes) != 2:
                    continue

                ticket_id, data_str = partes

                try:
                    data_ticket = datetime.fromisoformat(data_str)

                    if data_ticket >= limite:
                        linhas_validas.append(linha.strip())

                except Exception:
                    continue

        with open("notified_tickets.txt", "w") as f:
            for linha in linhas_validas:
                f.write(linha + "\n")

        print(f"Limpeza concluída. {len(linhas_validas)} tickets mantidos.")

    except FileNotFoundError:
        pass


# ==========================================================
# FUNÇÃO: salvar_ticket_notificado
# ==========================================================
def salvar_ticket_notificado(ticket_id):
    data_envio = datetime.now(timezone.utc).isoformat()

    with open("notified_tickets.txt", "a") as f:
        f.write(f"{ticket_id}|{data_envio}\n")


# ==========================================================
# FUNÇÃO: remover_acentos
# ==========================================================
def remover_acentos(texto):
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )


# ==========================================================
# FUNÇÃO PRINCIPAL
# ==========================================================
def main():

    limpar_tickets_antigos(dias=7)

    palavras_originais = [
        "urgente", "urgência", "imediatamente", "o quanto antes",
        "hoje ainda", "até amanhã", "até hoje", "para hoje",
        "pra hoje", "para amanhã", "pra amanhã", "faturamento",
        "insatisfação", "insatisfeito", "insatisfeita",
        "péssimo", "péssima", "ruim", "horrível",
        "decepcionado", "decepcionada", "frustrado",
        "indignada", "indignado", "descaso",
        "falta de retorno", "ninguém responde", "NFS"
    ]

    tickets = buscar_tickets_recentes()

    tickets_notificados = carregar_tickets_notificados()

    if not tickets:
        print("Nenhum ticket encontrado.")
        return

    novos_enviados = 0

    for ticket in tickets:

        # ==================================================
        # FILTRO LOCAL INTELIGENTE (IGNORA ACENTO)
        # ==================================================
        subject = ticket.get("subject") or ""
        description = ticket.get("description") or ""

        texto_completo = f"{subject} {description}"
        texto_normalizado = remover_acentos(texto_completo.lower())

        # ==================================================
        # IDENTIFICA QUAIS PALAVRAS FORAM ENCONTRADAS
        # ==================================================
        palavras_encontradas = []

        for p in palavras_originais:
            if not p.strip():
                continue

            p_normalizada = remover_acentos(p.lower())

            if p_normalizada in texto_normalizado:
                palavras_encontradas.append(p)

        if not palavras_encontradas:
            print(f"Ticket {ticket['id']} ignorado (sem palavra-chave).")
            continue

        # ==================================================
        # VERIFICA DUPLICIDADE
        # ==================================================
        if str(ticket["id"]) in tickets_notificados:
            continue

        prioridade = ticket.get("priority") or "Não definida"

        # ==================================================
        # CONVERSÃO DE DATA
        # ==================================================

        data_original = ticket['created_at']

        data_utc = datetime.strptime(
            data_original,
            "%Y-%m-%dT%H:%M:%SZ"
        ).replace(tzinfo=ZoneInfo("UTC"))

        data_local = data_utc.astimezone(
            ZoneInfo("America/Sao_Paulo")
        )

        data_formatada = data_local.strftime(
            "%d/%m/%Y - hora: %H:%M"
        )

        # ==================================================
        # MENSAGEM
        # ==================================================
        palavras_formatadas = ", ".join(palavras_encontradas)

        mensagem = f"""
        🚨 TICKET URGENTE 🚨
        ID: {ticket['id']}
        Data: {data_formatada}
        Assunto: {subject}
        Prioridade: {prioridade}
        Link: https://{ZENDESK_SUBDOMAIN}.zendesk.com/agent/tickets/{ticket['id']}

        🔎 Palavras detectadas:
        {palavras_formatadas}        
        """

        print("Enviando mensagem para Teams...")

        enviado = send_teams_message(mensagem)

        if enviado:
            salvar_ticket_notificado(ticket["id"])
            novos_enviados += 1
        else:
            print(f"Falha ao notificar ticket {ticket['id']}.")

    # ==================================================
    # LOG FINAL
    # ==================================================
    if novos_enviados == 0:
        print(f"{len(tickets)} tickets encontrados, mas nenhum novo para envio.")
    else:
        print(f"{novos_enviados} novo(s) ticket(s) enviado(s) com sucesso.")

if __name__ == "__main__":
    main()