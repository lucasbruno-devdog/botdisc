import os
import discord
from discord.ext import commands
import requests
from requests.auth import HTTPBasicAuth
import json
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()

# Pega as credenciais do ambiente
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
JIRA_URL = os.getenv('JIRA_URL')
JIRA_USER = os.getenv('JIRA_USER')
JIRA_API_TOKEN = os.getenv('JIRA_API_TOKEN')
# --- NOVO: Carrega a chave do projeto ---
JIRA_PROJECT_KEY = os.getenv('JIRA_PROJECT_KEY')


# Define as intenções (intents) do bot.
intents = discord.Intents.default()
intents.message_content = True

# Cria a instância do bot com um prefixo de comando
bot = commands.Bot(command_prefix='!', intents=intents)

# Evento que é acionado quando o bot está pronto e online
@bot.event
async def on_ready():
    print(f'Bot conectado como {bot.user}')
    print('------')

# Comando para buscar uma issue no Jira
@bot.command(name="jira")
async def get_jira_issue(ctx, issue_key: str):
    """Busca informações de uma issue específica do Jira. Uso: !jira PROJ-123"""
    api_url = f"{JIRA_URL}/rest/api/3/issue/{issue_key}"
    auth = HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN)
    headers = {"Accept": "application/json"}
    
    try:
        response = requests.get(api_url, headers=headers, auth=auth)
        response.raise_for_status()
        
        issue_data = response.json()
        fields = issue_data['fields']
        summary = fields['summary']
        status = fields['status']['name']
        reporter = fields['reporter']['displayName']
        assignee = fields['assignee']['displayName'] if fields.get('assignee') else "Não atribuído"
        issue_type = fields['issuetype']['name']
        
        embed = discord.Embed(
            title=f"Ticket {issue_key}: {summary}",
            url=f"{JIRA_URL}/browse/{issue_key}",
            color=discord.Color.blue()
        )
        embed.set_author(name=f"Tipo: {issue_type}")
        embed.add_field(name="Status", value=status, inline=True)
        embed.add_field(name="Responsável", value=assignee, inline=True)
        embed.add_field(name="Relator", value=reporter, inline=False)
        
        await ctx.send(embed=embed)

    except requests.exceptions.HTTPError as err:
        if err.response.status_code == 404:
            await ctx.send(f"Erro: A issue `{issue_key}` não foi encontrada.")
        else:
            await ctx.send(f"Erro ao contatar o Jira: {err.response.status_code}")
    except Exception as e:
        await ctx.send(f"Ocorreu um erro inesperado: {e}")

# --- NOVO COMANDO PARA CRIAR TICKETS ---
@bot.command(name="create")
async def create_jira_issue(ctx, *, summary: str):
    """Cria um novo ticket no Jira. Uso: !create Título do novo ticket"""
    
    # URL da API para criar issues
    api_url = f"{JIRA_URL}/rest/api/3/issue"
    
    # Autenticação e cabeçalhos
    auth = HTTPBasicAuth(JIRA_USER, JIRA_API_TOKEN)
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json"
    }
    
    # Payload (dados) da issue a ser criada.
    # A estrutura deve seguir o que a API do Jira espera.
    payload = json.dumps({
        "fields": {
            "summary": summary, # O título que o usuário digitou
            "issuetype": {
                "name": "Task" # IMPORTANTE: Use um tipo de issue válido no seu projeto (Task, Bug, Story, etc.)
            },
            "project": {
                "key": JIRA_PROJECT_KEY # A chave do projeto que definimos no .env
            }
        }
    })
    
    await ctx.send(f"Criando ticket no Jira com o título: \"{summary}\"...")

    try:
        # Faz a requisição POST para criar o ticket
        response = requests.post(api_url, data=payload, headers=headers, auth=auth)
        response.raise_for_status() # Lança erro se a requisição falhar (status code não for 2xx)

        # Se a criação foi bem-sucedida (status 201 Created), pega a resposta
        issue_data = response.json()
        new_issue_key = issue_data['key']
        
        # Cria uma mensagem bonita de confirmação
        embed = discord.Embed(
            title="✅ Ticket Criado com Sucesso!",
            description=f"O ticket **{new_issue_key}** foi criado no Jira.",
            url=f"{JIRA_URL}/browse/{new_issue_key}",
            color=discord.Color.green()
        )
        embed.add_field(name="Título", value=summary, inline=False)
        embed.add_field(name="Projeto", value=JIRA_PROJECT_KEY, inline=True)
        embed.add_field(name="Criado por", value=ctx.author.display_name, inline=True)
        
        await ctx.send(embed=embed)

    except requests.exceptions.HTTPError as err:
        # Se der erro, mostra uma mensagem mais detalhada
        error_message = f"Erro ao criar o ticket: {err.response.status_code}"
        try:
            # Tenta pegar a mensagem de erro específica do Jira
            jira_error = err.response.json()
            error_details = jira_error.get('errorMessages', [])
            if error_details:
                error_message += f"\nDetalhes: `{', '.join(error_details)}`"
        except json.JSONDecodeError:
            pass # Se a resposta de erro não for JSON, ignora
        await ctx.send(error_message)
    except Exception as e:
        await ctx.send(f"Ocorreu um erro inesperado: {e}")

# Inicia o bot
bot.run(DISCORD_TOKEN)