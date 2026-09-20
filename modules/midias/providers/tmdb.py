import os
import aiohttp


TMDB_BASE_URL = "https://api.themoviedb.org/3"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"


def obter_token():
    token = os.getenv("TMDB_TOKEN")

    if not token:
        raise RuntimeError(
            "TMDB_TOKEN não foi encontrado no arquivo .env."
        )

    return token


def cabecalhos():
    return {
        "Authorization": f"Bearer {obter_token()}",
        "accept": "application/json",
    }


async def pesquisar_tmdb(nome: str, tipo: str):
    """
    tipo:
        movie -> Filme
        tv    -> Série
    """

    if tipo not in ("movie", "tv"):
        raise ValueError("Tipo de mídia inválido para o TMDB.")

    url = f"{TMDB_BASE_URL}/search/{tipo}"

    parametros = {
        "query": nome,
        "language": "pt-BR",
        "include_adult": "false",
        "page": 1,
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(
            url,
            headers=cabecalhos(),
            params=parametros,
        ) as resposta:

            if resposta.status != 200:
                texto = await resposta.text()

                raise RuntimeError(
                    f"Erro do TMDB ({resposta.status}): {texto}"
                )

            dados = await resposta.json()

    resultados = []

    for item in dados.get("results", [])[:10]:

        if tipo == "movie":
            titulo = item.get("title") or "Sem título"
            data = item.get("release_date") or ""
        else:
            titulo = item.get("name") or "Sem título"
            data = item.get("first_air_date") or ""

        ano = data[:4] if data else "????"

        poster_path = item.get("poster_path")

        if poster_path:
            capa = f"{TMDB_IMAGE_URL}{poster_path}"
        else:
            capa = None

        resultados.append(
            {
                "id": item["id"],
                "tipo": tipo,
                "titulo": titulo,
                "ano": ano,
                "sinopse": item.get("overview") or (
                    "Sinopse não disponível em português."
                ),
                "capa": capa,
            }
        )

    return resultados