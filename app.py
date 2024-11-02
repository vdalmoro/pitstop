import discord
import re
import gspread
import pytz
import os
from discord.ext import commands
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv('DISCORD_TOKEN')
LISTEN_ID = os.getenv('LISTENER') # Ouvindo BTL - Geral
POLICE_ID = os.getenv('COMMANDER') # Recebendo BTL - Police

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
GOOGLE = os.getenv('GOOGLE_CREDENTIALS_PATH')
creds = ServiceAccountCredentials.from_json_keyfile_name(GOOGLE, scope)
client = gspread.authorize(creds)
lspd = client.open("PITSTOP - LSPD").worksheet("LSPD")
workers = client.open("PITSTOP - LSPD").worksheet("WORKERS")


@bot.event
async def on_ready():
    print(f'{bot.user} está online e pronto para uso!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    await bot.process_commands(message)

    if message.channel.id == LISTEN_ID:

        funcionario_match = re.search(r"Funcionário\(a\): (.+)", message.content)
        tempo_trabalho_match = re.search(r"Tempo de trabalho: (.+)", message.content)

        if funcionario_match and tempo_trabalho_match:

            funcionario = funcionario_match.group(1).strip()
            tempo_trabalho = tempo_trabalho_match.group(1).strip()

            timestamp = message.created_at
            local_time = timestamp.astimezone(pytz.timezone('America/Sao_Paulo'))
            date_sent = local_time.strftime("%d-%m-%Y %H:%M:%S")

            row = [funcionario, date_sent, tempo_trabalho]
            workers.append_row(row)

@bot.command(name='police')
async def police(ctx, badge: int, service: str):
    if ctx.channel.id == POLICE_ID:
        timestamp = ctx.message.created_at
        date_sent = timestamp.strftime("%d-%m-%Y")
        author = ctx.message.author
    
        row = [author.name, date_sent, badge, service]
        lspd.append_row(row)
        last_row = len(lspd.get_all_values())
        formula = f'=SWITCH(D{last_row}; "A"; 200; "B"; 350; "C"; 550; "D"; 580; "E"; 1130; "Valor não encontrado")'
        lspd.update_cell(last_row, 5, formula)

        await ctx.send(f"Serviço: {service} para o Oficial: {badge}. Cadastrado com sucesso! Realizado por {author.name} em {date_sent}")
    else:
        await ctx.send("Este comando só pode ser usado no canal designado para comandos!")

bot.run(TOKEN)