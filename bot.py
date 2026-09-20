import os

import discord

from discord.ext import commands
from dotenv import load_dotenv

from modules.midias.recomendar import registrar_recomendacoes
from modules.midias.lista import registrar_lista
from modules.midias.atualizar import registrar_atualizar


load_dotenv()

TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise RuntimeError(
        "DISCORD_TOKEN não foi encontrado no arquivo .env."
    )


intents = discord.Intents.default()

bot = commands.Bot(
    command_prefix="!",
    intents=intents,
)


registrar_recomendacoes(bot)
registrar_lista(bot)
registrar_atualizar(bot)


async def setup_hook():
    await bot.tree.sync()


bot.setup_hook = setup_hook


@bot.event
async def on_ready():
    print(f"✓ Bot conectado como {bot.user}")
    print("✓ Recomendações carregadas")
    print("✓ Listas de mídias carregadas")
    print("✓ Atualização de mídias carregada")


bot.run(TOKEN)