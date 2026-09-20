import aiohttp


THEAUDIODB_API_KEY = "123"

BASE_URL = (
    "https://www.theaudiodb.com/api/v1/json/"
    f"{THEAUDIODB_API_KEY}"
)


# ============================================================
# UTILIDADES
# ============================================================

def limitar_resultados(
    resultados,
    limite=10,
):
    return resultados[:limite]


def limpar_texto(texto):
    if texto is None:
        return None

    texto = str(texto).strip()

    if not texto:
        return None

    return texto


def primeiro_texto(*valores):
    for valor in valores:
        valor = limpar_texto(valor)

        if valor:
            return valor

    return None


def montar_ano(valor):
    valor = limpar_texto(valor)

    if not valor:
        return "—"

    return valor[:4]


def montar_descricao(
    item,
    *campos,
):
    for campo in campos:
        texto = limpar_texto(
            item.get(campo)
        )

        if texto:
            return texto

    return "Descrição não disponível."


# ============================================================
# REQUISIÇÃO
# ============================================================

async def consultar(
    endpoint,
    parametros,
):
    url = (
        f"{BASE_URL}/"
        f"{endpoint}"
    )

    timeout = aiohttp.ClientTimeout(
        total=15
    )

    async with aiohttp.ClientSession(
        timeout=timeout
    ) as session:
        async with session.get(
            url,
            params=parametros,
        ) as response:
            if response.status != 200:
                texto = await response.text()

                raise RuntimeError(
                    "TheAudioDB respondeu com "
                    f"HTTP {response.status}: "
                    f"{texto[:300]}"
                )

            return await response.json()


# ============================================================
# ARTISTA
# ============================================================

async def pesquisar_artista(
    nome,
):
    dados = await consultar(
        "search.php",
        {
            "s": nome,
        },
    )

    artistas = (
        dados.get("artists")
        or []
    )

    resultados = []

    for artista in artistas:
        external_id = (
            artista.get("idArtist")
        )

        titulo = primeiro_texto(
            artista.get("strArtist"),
            nome,
        )

        if not external_id or not titulo:
            continue

        capa = primeiro_texto(
            artista.get(
                "strArtistThumb"
            ),
            artista.get(
                "strArtistFanart"
            ),
            artista.get(
                "strArtistFanart2"
            ),
        )

        genero = limpar_texto(
            artista.get("strGenre")
        )

        estilo = limpar_texto(
            artista.get("strStyle")
        )

        pais = primeiro_texto(
            artista.get("strCountry"),
            artista.get(
                "strCountryCode"
            ),
        )

        descricao = montar_descricao(
            artista,
            "strBiographyPT",
            "strBiographyEN",
        )

        extras = []

        if genero:
            extras.append(genero)

        if estilo and estilo != genero:
            extras.append(estilo)

        if pais:
            extras.append(pais)

        if extras:
            descricao = (
                " • ".join(extras)
                + "\n\n"
                + descricao
            )

        resultados.append(
            {
                "id": str(
                    external_id
                ),
                "provider": "theaudiodb",
                "tipo": "artist",
                "titulo": titulo,
                "ano": montar_ano(
                    artista.get(
                        "intBornYear"
                    )
                ),
                "sinopse": descricao,
                "capa": capa,
            }
        )

    return limitar_resultados(
        resultados
    )


# ============================================================
# ÁLBUM
# ============================================================

async def pesquisar_album(
    artista,
    album,
):
    dados = await consultar(
        "searchalbum.php",
        {
            "s": artista,
            "a": album,
        },
    )

    albuns = (
        dados.get("album")
        or []
    )

    resultados = []

    for item in albuns:
        external_id = (
            item.get("idAlbum")
        )

        titulo_album = primeiro_texto(
            item.get("strAlbum"),
            album,
        )

        if (
            not external_id
            or not titulo_album
        ):
            continue

        nome_artista = primeiro_texto(
            item.get("strArtist"),
            artista,
        )

        capa = primeiro_texto(
            item.get(
                "strAlbumThumb"
            ),
            item.get(
                "strAlbumThumbHQ"
            ),
            item.get(
                "strAlbumCDart"
            ),
        )

        genero = limpar_texto(
            item.get("strGenre")
        )

        estilo = limpar_texto(
            item.get("strStyle")
        )

        descricao = montar_descricao(
            item,
            "strDescriptionPT",
            "strDescriptionEN",
        )

        cabecalho = []

        if nome_artista:
            cabecalho.append(
                f"Artista: {nome_artista}"
            )

        if genero:
            cabecalho.append(genero)

        if (
            estilo
            and estilo != genero
        ):
            cabecalho.append(estilo)

        if cabecalho:
            descricao = (
                " • ".join(cabecalho)
                + "\n\n"
                + descricao
            )

        resultados.append(
            {
                "id": str(
                    external_id
                ),
                "provider": "theaudiodb",
                "tipo": "album",
                "titulo": titulo_album,
                "ano": montar_ano(
                    item.get(
                        "intYearReleased"
                    )
                ),
                "sinopse": descricao,
                "capa": capa,
            }
        )

    return limitar_resultados(
        resultados
    )


# ============================================================
# MÚSICA / FAIXA
# ============================================================

async def pesquisar_musica(
    artista,
    musica,
):
    dados = await consultar(
        "searchtrack.php",
        {
            "s": artista,
            "t": musica,
        },
    )

    faixas = (
        dados.get("track")
        or []
    )

    resultados = []

    for faixa in faixas:
        external_id = (
            faixa.get("idTrack")
        )

        titulo = primeiro_texto(
            faixa.get("strTrack"),
            musica,
        )

        if not external_id or not titulo:
            continue

        nome_artista = primeiro_texto(
            faixa.get("strArtist"),
            artista,
        )

        nome_album = limpar_texto(
            faixa.get("strAlbum")
        )

        capa = primeiro_texto(
            faixa.get(
                "strTrackThumb"
            ),
            faixa.get(
                "strAlbumThumb"
            ),
        )

        genero = limpar_texto(
            faixa.get("strGenre")
        )

        descricao = montar_descricao(
            faixa,
            "strDescriptionPT",
            "strDescriptionEN",
        )

        detalhes = []

        if nome_artista:
            detalhes.append(
                f"Artista: {nome_artista}"
            )

        if nome_album:
            detalhes.append(
                f"Álbum: {nome_album}"
            )

        if genero:
            detalhes.append(genero)

        if detalhes:
            descricao = (
                " • ".join(detalhes)
                + "\n\n"
                + descricao
            )

        resultados.append(
            {
                "id": str(
                    external_id
                ),
                "provider": "theaudiodb",
                "tipo": "music",
                "titulo": titulo,
                "ano": montar_ano(
                    primeiro_texto(
                        faixa.get(
                            "intYearReleased"
                        ),
                        faixa.get(
                            "intYear"
                        ),
                    )
                ),
                "sinopse": descricao,
                "capa": capa,
            }
        )

    return limitar_resultados(
        resultados
    )


# ============================================================
# FUNÇÃO ÚNICA DO PROVIDER
# ============================================================

async def pesquisar_theaudiodb(
    tipo,
    *,
    nome=None,
    artista=None,
):
    if tipo == "artist":
        if not nome:
            raise ValueError(
                "Informe o nome do artista."
            )

        return await pesquisar_artista(
            nome
        )

    if tipo == "album":
        if not artista or not nome:
            raise ValueError(
                "Informe o artista e o álbum."
            )

        return await pesquisar_album(
            artista,
            nome,
        )

    if tipo == "music":
        if not artista or not nome:
            raise ValueError(
                "Informe o artista e a música."
            )

        return await pesquisar_musica(
            artista,
            nome,
        )

    raise ValueError(
        "Tipo de mídia musical inválido."
    )