import os
import time

import aiohttp

from dotenv import load_dotenv


# ============================================================
# CONFIGURAÇÃO
# ============================================================

load_dotenv()

CLIENT_ID = os.getenv(
    "IGDB_CLIENT_ID"
)

CLIENT_SECRET = os.getenv(
    "IGDB_CLIENT_SECRET"
)

TWITCH_TOKEN_URL = (
    "https://id.twitch.tv/oauth2/token"
)

IGDB_GAMES_URL = (
    "https://api.igdb.com/v4/games"
)


# ============================================================
# CACHE DO TOKEN
# ============================================================

_token = None
_token_expira_em = 0


# ============================================================
# TOKEN DA TWITCH
# ============================================================

async def obter_token():
    global _token
    global _token_expira_em

    agora = time.time()

    # Reutiliza o token enquanto ele ainda for válido.
    if (
        _token is not None
        and agora < _token_expira_em
    ):
        return _token

    if not CLIENT_ID:
        raise RuntimeError(
            "IGDB_CLIENT_ID não foi encontrado no .env."
        )

    if not CLIENT_SECRET:
        raise RuntimeError(
            "IGDB_CLIENT_SECRET não foi encontrado no .env."
        )

    parametros = {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "client_credentials",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            TWITCH_TOKEN_URL,
            params=parametros,
        ) as resposta:

            if resposta.status != 200:
                texto = await resposta.text()

                raise RuntimeError(
                    "Não foi possível gerar o token "
                    f"da Twitch ({resposta.status}): "
                    f"{texto}"
                )

            dados = await resposta.json()

    _token = dados[
        "access_token"
    ]

    duracao = int(
        dados.get(
            "expires_in",
            3600,
        )
    )

    # Renova um minuto antes de expirar.
    _token_expira_em = (
        agora
        + duracao
        - 60
    )

    return _token


# ============================================================
# PESQUISA
# ============================================================

async def pesquisar_igdb(
    nome: str,
):
    token = await obter_token()

    nome = nome.strip()

    if not nome:
        return []

    # Escapa caracteres que poderiam quebrar
    # a string da consulta do IGDB.
    nome_seguro = (
        nome
        .replace("\\", "\\\\")
        .replace('"', '\\"')
    )

    consulta = f'''
        search "{nome_seguro}";
        fields
            id,
            name,
            summary,
            first_release_date,
            cover.image_id;
        limit 10;
    '''

    headers = {
        "Client-ID": CLIENT_ID,
        "Authorization": (
            f"Bearer {token}"
        ),
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            IGDB_GAMES_URL,
            headers=headers,
            data=consulta,
        ) as resposta:

            if resposta.status == 401:
                # Caso a Twitch invalide o token antes
                # do esperado, limpa o cache.
                global _token
                global _token_expira_em

                _token = None
                _token_expira_em = 0

            if resposta.status != 200:
                texto = await resposta.text()

                raise RuntimeError(
                    f"Erro do IGDB "
                    f"({resposta.status}): "
                    f"{texto}"
                )

            dados = await resposta.json()

    resultados = []

    for item in dados:
        timestamp = item.get(
            "first_release_date"
        )

        if timestamp:
            ano = time.strftime(
                "%Y",
                time.gmtime(timestamp),
            )

        else:
            ano = "????"

        capa = None

        cover = item.get(
            "cover"
        ) or {}

        image_id = cover.get(
            "image_id"
        )

        if image_id:
            capa = (
                "https://images.igdb.com/"
                "igdb/image/upload/"
                f"t_cover_big/{image_id}.jpg"
            )

        resultados.append(
            {
                "id": item["id"],
                "provider": "igdb",
                "tipo": "game",
                "titulo": item.get(
                    "name",
                    "Sem título",
                ),
                "ano": ano,
                "sinopse": (
                    item.get("summary")
                    or "Sinopse não disponível."
                ),
                "capa": capa,
            }
        )

    return resultados