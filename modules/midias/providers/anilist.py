import re

import aiohttp


ANILIST_URL = "https://graphql.anilist.co"


QUERY_PESQUISA = """
query (
    $search: String!,
    $type: MediaType!
) {
    Page(
        page: 1,
        perPage: 10
    ) {
        media(
            search: $search,
            type: $type,
            isAdult: false
        ) {
            id

            title {
                romaji
                english
                native
            }

            description(
                asHtml: false
            )

            startDate {
                year
            }

            coverImage {
                extraLarge
                large
            }

            format
        }
    }
}
"""


def limpar_descricao(
    descricao,
):
    if not descricao:
        return (
            "Sinopse não disponível."
        )

    # AniList pode devolver algumas tags
    # simples mesmo com asHtml desativado.
    descricao = re.sub(
        r"<br\\s*/?>",
        "\n",
        descricao,
        flags=re.IGNORECASE,
    )

    descricao = re.sub(
        r"<[^>]+>",
        "",
        descricao,
    )

    return descricao.strip()


def escolher_titulo(
    titulos,
):
    # Prioridade:
    # inglês -> romaji -> original.
    return (
        titulos.get("english")
        or titulos.get("romaji")
        or titulos.get("native")
        or "Sem título"
    )


async def pesquisar_anilist(
    nome: str,
    tipo: str,
):
    if tipo not in (
        "anime",
        "manga",
    ):
        raise ValueError(
            "Tipo inválido para o AniList."
        )

    tipo_api = (
        "ANIME"
        if tipo == "anime"
        else "MANGA"
    )

    payload = {
        "query": QUERY_PESQUISA,
        "variables": {
            "search": nome,
            "type": tipo_api,
        },
    }

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            ANILIST_URL,
            json=payload,
            headers=headers,
        ) as resposta:

            if resposta.status == 429:
                espera = resposta.headers.get(
                    "Retry-After",
                    "alguns segundos",
                )

                raise RuntimeError(
                    "O AniList atingiu temporariamente "
                    "o limite de requisições. "
                    f"Tente novamente em {espera}."
                )

            if resposta.status != 200:
                texto = await resposta.text()

                raise RuntimeError(
                    f"Erro do AniList "
                    f"({resposta.status}): "
                    f"{texto}"
                )

            dados = await resposta.json()

    if dados.get("errors"):
        mensagem = dados[
            "errors"
        ][0].get(
            "message",
            "Erro desconhecido.",
        )

        raise RuntimeError(
            f"Erro do AniList: {mensagem}"
        )

    pagina = (
        dados
        .get("data", {})
        .get("Page", {})
    )

    resultados_api = pagina.get(
        "media",
        []
    )

    resultados = []

    for item in resultados_api:
        titulo = escolher_titulo(
            item.get(
                "title",
                {},
            )
        )

        data = item.get(
            "startDate"
        ) or {}

        ano = (
            str(data["year"])
            if data.get("year")
            else "????"
        )

        capa_dados = (
            item.get("coverImage")
            or {}
        )

        capa = (
            capa_dados.get("extraLarge")
            or capa_dados.get("large")
        )

        resultados.append(
            {
                "id": item["id"],
                "provider": "anilist",
                "tipo": tipo,
                "titulo": titulo,
                "ano": ano,
                "sinopse": limpar_descricao(
                    item.get(
                        "description"
                    )
                ),
                "capa": capa,
                "formato": item.get(
                    "format"
                ),
            }
        )

    return resultados