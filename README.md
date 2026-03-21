🚀 Monitoramento Proativo: De dashboards à antecipação de crises com Python!

🎫 Zendesk → Microsoft Teams Notifier

Automação responsável por monitorar tickets novos no Zendesk e enviar notificações automáticas para um canal do Microsoft Teams.

📌 Sobre o Projeto

Este projeto consulta periodicamente a API do Zendesk em busca de tickets com status new, criados recentemente, e envia uma notificação formatada para um canal do Microsoft Teams via Incoming Webhook.

A aplicação também mantém controle dos tickets já notificados para evitar envios duplicados.

🏗 Arquitetura do Projeto
.
├── .env
├── .env.example
├── .gitignore
├── config.py
├── main.py
├── notifier.py
├── notified_tickets.txt
├── requirements.txt
└── README.md

📄 Descrição dos Arquivos
Arquivo	Descrição
config.py
Carrega e valida as variáveis de ambiente

main.py	
Contém a lógica principal da aplicação

notifier.py	
Responsável pelo envio das mensagens ao Microsoft Teams

notified_tickets.txt	
Armazena os IDs dos tickets já notificados

requirements.txt	
Lista de dependências do projeto

.env	
Variáveis sensíveis (não versionado)

.env.example	
Modelo para configuração do ambiente

🔐 Variáveis de Ambiente
O projeto utiliza um arquivo .env para armazenar credenciais sensíveis.

Exemplo:
ZENDESK_SUBDOMAIN=seu_subdominio
ZENDESK_EMAIL=seu_email
ZENDESK_API_TOKEN=seu_token
TEAMS_WEBHOOK_URL=sua_url_webhook

🔎 Onde obter:
Subdomínio e API Token → Painel administrativo do Zendesk
Webhook → Configuração de Webhook do Microsoft Teams

⚠️ Nunca compartilhe seu arquivo .env publicamente.

⚙️ Instalação
1️⃣ Criar ambiente virtual (recomendado)
python -m venv venv

Ativar:
Windows
venv\Scripts\activate

Linux / Mac
source venv/bin/activate

2️⃣ Instalar dependências
pip install -r requirements.txt

3️⃣ Configurar variáveis de ambiente

Copie o arquivo .env.example:
cp .env.example .env

Preencha com suas credenciais reais.

▶️ Execução
python main.py

🔄 Funcionamento

A aplicação:
1 - Consulta a API do Zendesk
2 - Filtra tickets com:
    type:ticket
    status:new
    created>1hours

3 - Verifica se o ticket já foi notificado
4 - Converte horário UTC → America/Sao_Paulo
5 - Envia mensagem formatada para o Microsoft Teams
6 - Salva o ID do ticket para evitar duplicidade

🌎 Integrações Utilizadas
Zendesk API (Search Endpoint)
Microsoft Teams Incoming Webhook

📦 Dependências
requests
python-dotenv

🔄 Execução Automática (Opcional)
A aplicação pode ser configurada para rodar automaticamente via:
Agendador de Tarefas (Windows)
Cron (Linux/Mac)
Docker
Geração de executável .exe com PyInstaller

🚀 Melhorias Futuras
 Implementar logging estruturado
 Migrar controle de tickets para SQLite
 Containerização com Docker
 Implementar testes automatizados
 Criar painel de monitoramento

🛡 Segurança
Credenciais armazenadas apenas em variáveis de ambiente
Validação obrigatória de configuração
Controle de duplicidade de notificações

👨‍💻 Autor
Projeto desenvolvido para automação corporativa de monitoramento de tickets Zendesk e notificação automática no Microsoft Teams.

📜 Licença
Uso interno / Corporativo.
