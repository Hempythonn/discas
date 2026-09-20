import asyncio

import discord

from modules.midias.database import (
    MidiasDatabase,
    formatar_data_finalizacao,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DB_PATH = "data/bot.db"

db_midias = MidiasDatabase(
    DB_PATH
)


# ============================================================
# CATEGORIAS
# ============================================================

CATEGORIAS = [
    "jogos",
    "filmes_series",
    "anime_manga",
    "musica",
]


def categoria_anterior(
    categoria,
):
    indice = CATEGORIAS.index(
        categoria
    )

    return CATEGORIAS[
        (indice - 1)
        % len(CATEGORIAS)
    ]


def categoria_proxima(
    categoria,
):
    indice = CATEGORIAS.index(
        categoria
    )

    return CATEGORIAS[
        (indice + 1)
        % len(CATEGORIAS)
    ]


# ============================================================
# FECHAMENTO AUTOMÁTICO
# ============================================================

async def apagar_resposta_depois(
    interaction,
    segundos=4,
):
    await asyncio.sleep(
        segundos
    )

    try:
        await interaction.delete_original_response()

    except (
        discord.NotFound,
        discord.HTTPException,
    ):
        pass


def fechar_depois(
    interaction,
    segundos=4,
):
    asyncio.create_task(
        apagar_resposta_depois(
            interaction,
            segundos,
        )
    )


# ============================================================
# NOMES
# ============================================================

def nome_status_final(
    tipo,
):
    return {
        "game": "Finalizado",
        "movie": "Assistido",
        "tv": "Assistida",
        "anime": "Assistido",
        "manga": "Lido",
        "music": "Ouvida",
        "album": "Ouvido",
        "artist": "Ouvido",
    }.get(
        tipo,
        "Finalizado",
    )


# ============================================================
# FILTROS
# ============================================================

def filtrar(
    midias,
    *,
    tipo=None,
    status=None,
    favorito=None,
):
    resultado = []

    for midia in midias:
        if (
            tipo is not None
            and midia["tipo"] != tipo
        ):
            continue

        if (
            status is not None
            and midia["status"] != status
        ):
            continue

        if (
            favorito is not None
            and bool(
                midia["favorito"]
            ) != favorito
        ):
            continue

        resultado.append(
            midia
        )

    return resultado


def nomes_midias(
    midias,
):
    if not midias:
        return "—"

    return "\n".join(
        midia["titulo"]
        for midia in midias
    )


# ============================================================
# BLOCO PADRÃO
# ============================================================

def adicionar_bloco(
    embed,
    titulo,
    favoritos,
    pendentes,
    andamento,
    finalizados,
    *,
    nome_pendentes,
    nome_andamento,
    nome_finalizados,
):
    embed.add_field(
        name=f"**{titulo}**",
        value="\u200b",
        inline=False,
    )

    embed.add_field(
        name="Favoritos",
        value=nomes_midias(
            favoritos
        ),
        inline=False,
    )

    embed.add_field(
        name=nome_pendentes,
        value=nomes_midias(
            pendentes
        ),
        inline=False,
    )

    embed.add_field(
        name=nome_andamento,
        value=nomes_midias(
            andamento
        ),
        inline=False,
    )

    embed.add_field(
        name=nome_finalizados,
        value=nomes_midias(
            finalizados
        ),
        inline=False,
    )


# ============================================================
# JOGOS
# ============================================================

def criar_embed_jogos(
    nome_usuario,
    midias,
):
    embed = discord.Embed(
        title=f"𐙚 {nome_usuario}"
    )

    adicionar_bloco(
        embed,
        "JOGOS",

        filtrar(
            midias,
            tipo="game",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="game",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="game",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="game",
            status="finalizado",
        ),

        nome_pendentes="Quero jogar",
        nome_andamento="Jogando",
        nome_finalizados="Finalizados",
    )

    return embed


# ============================================================
# FILMES / SÉRIES
# ============================================================

def criar_embed_filmes_series(
    nome_usuario,
    midias,
):
    embed = discord.Embed(
        title=f"𐙚 {nome_usuario}"
    )

    adicionar_bloco(
        embed,
        "FILMES",

        filtrar(
            midias,
            tipo="movie",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="movie",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="movie",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="movie",
            status="finalizado",
        ),

        nome_pendentes="Quero assistir",
        nome_andamento="Assistindo",
        nome_finalizados="Assistidos",
    )

    embed.add_field(
        name="\u200b",
        value="━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )

    adicionar_bloco(
        embed,
        "SÉRIES",

        filtrar(
            midias,
            tipo="tv",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="tv",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="tv",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="tv",
            status="finalizado",
        ),

        nome_pendentes="Quero assistir",
        nome_andamento="Assistindo",
        nome_finalizados="Assistidas",
    )

    return embed


# ============================================================
# ANIME / MANGÁ
# ============================================================

def criar_embed_anime_manga(
    nome_usuario,
    midias,
):
    embed = discord.Embed(
        title=f"𐙚 {nome_usuario}"
    )

    adicionar_bloco(
        embed,
        "ANIMES",

        filtrar(
            midias,
            tipo="anime",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="anime",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="anime",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="anime",
            status="finalizado",
        ),

        nome_pendentes="Quero assistir",
        nome_andamento="Assistindo",
        nome_finalizados="Assistidos",
    )

    embed.add_field(
        name="\u200b",
        value="━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )

    adicionar_bloco(
        embed,
        "MANGÁS",

        filtrar(
            midias,
            tipo="manga",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="manga",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="manga",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="manga",
            status="finalizado",
        ),

        nome_pendentes="Quero ler",
        nome_andamento="Lendo",
        nome_finalizados="Lidos",
    )

    return embed


# ============================================================
# MÚSICA / ÁLBUM / ARTISTA
# ============================================================

def criar_embed_musica(
    nome_usuario,
    midias,
):
    embed = discord.Embed(
        title=f"𐙚 {nome_usuario}"
    )

    adicionar_bloco(
        embed,
        "MÚSICAS",

        filtrar(
            midias,
            tipo="music",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="music",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="music",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="music",
            status="finalizado",
        ),

        nome_pendentes="Quero ouvir",
        nome_andamento="Ouvindo",
        nome_finalizados="Ouvidas",
    )

    embed.add_field(
        name="\u200b",
        value="━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )

    adicionar_bloco(
        embed,
        "ÁLBUNS",

        filtrar(
            midias,
            tipo="album",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="album",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="album",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="album",
            status="finalizado",
        ),

        nome_pendentes="Quero ouvir",
        nome_andamento="Ouvindo",
        nome_finalizados="Ouvidos",
    )

    embed.add_field(
        name="\u200b",
        value="━━━━━━━━━━━━━━━━━━━━━━",
        inline=False,
    )

    adicionar_bloco(
        embed,
        "ARTISTAS",

        filtrar(
            midias,
            tipo="artist",
            favorito=True,
        )[:5],

        filtrar(
            midias,
            tipo="artist",
            status="quero_ver",
        ),

        filtrar(
            midias,
            tipo="artist",
            status="em_andamento",
        ),

        filtrar(
            midias,
            tipo="artist",
            status="finalizado",
        ),

        nome_pendentes="Quero ouvir",
        nome_andamento="Ouvindo",
        nome_finalizados="Ouvidos",
    )

    return embed


# ============================================================
# OPINIÃO INDIVIDUAL
# ============================================================

class OpiniaoLayout(
    discord.ui.LayoutView
):
    def __init__(
        self,
        opinioes,
        indice=0,
        *,
        guild_id=None,
        dono_user_id=None,
        opcoes=None,
    ):
        super().__init__(
            timeout=300
        )

        self.opinioes = opinioes
        self.indice = indice

        self.guild_id = guild_id
        self.dono_user_id = (
            dono_user_id
        )

        self.opcoes = opcoes

        opiniao = opinioes[
            indice
        ]

        itens = []

        ano = (
            opiniao.get("ano")
            or "Ano desconhecido"
        )

        cabecalho = (
            discord.ui.TextDisplay(
                f"## {opiniao['titulo']}\n"
                f"`{ano}`"
            )
        )

        if opiniao.get("capa"):
            itens.append(
                discord.ui.Section(
                    cabecalho,
                    accessory=(
                        discord.ui.Thumbnail(
                            opiniao["capa"],
                            description=(
                                "Capa de "
                                f"{opiniao['titulo']}"
                            ),
                        )
                    ),
                )
            )

        else:
            itens.append(
                cabecalho
            )

        itens.append(
            discord.ui.Separator()
        )

        if (
            opiniao.get("nota")
            is not None
        ):
            itens.append(
                discord.ui.TextDisplay(
                    "**Nota**\n"
                    f"{opiniao['nota']:g}/10"
                )
            )

        itens.append(
            discord.ui.TextDisplay(
                "**Opinião**\n"
                f"{opiniao['opiniao']}"
            )
        )

        data = (
            formatar_data_finalizacao(
                opiniao.get(
                    "finalizado_em"
                )
            )
        )

        if data:
            itens.append(
                discord.ui.TextDisplay(
                    "-# "
                    f"{nome_status_final(
                        opiniao['tipo']
                    )} "
                    f"em {data}"
                )
            )

        botoes = (
            discord.ui.ActionRow()
        )

        anterior = discord.ui.Button(
            label="Anterior",
            style=(
                discord.ButtonStyle.secondary
            ),
            disabled=(
                len(opinioes) <= 1
            ),
        )

        anterior.callback = (
            self.anterior
        )

        botoes.add_item(
            anterior
        )

        if (
            self.opcoes is not None
            and self.guild_id is not None
            and self.dono_user_id
            is not None
        ):
            trocar_tipo = (
                discord.ui.Button(
                    label="Trocar tipo",
                    style=(
                        discord.ButtonStyle.secondary
                    ),
                )
            )

            trocar_tipo.callback = (
                self.trocar_tipo
            )

            botoes.add_item(
                trocar_tipo
            )

        fechar = discord.ui.Button(
            label="Fechar",
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        fechar.callback = (
            self.fechar
        )

        botoes.add_item(
            fechar
        )

        proxima = discord.ui.Button(
            label="Próxima",
            style=(
                discord.ButtonStyle.secondary
            ),
            disabled=(
                len(opinioes) <= 1
            ),
        )

        proxima.callback = (
            self.proxima
        )

        botoes.add_item(
            proxima
        )

        itens.append(
            discord.ui.Separator(
                visible=False
            )
        )

        itens.append(
            botoes
        )

        self.add_item(
            discord.ui.Container(
                *itens
            )
        )

    async def anterior(
        self,
        interaction,
    ):
        novo_indice = (
            self.indice - 1
        ) % len(
            self.opinioes
        )

        await interaction.response.edit_message(
            view=OpiniaoLayout(
                self.opinioes,
                novo_indice,
                guild_id=(
                    self.guild_id
                ),
                dono_user_id=(
                    self.dono_user_id
                ),
                opcoes=self.opcoes,
            )
        )

    async def proxima(
        self,
        interaction,
    ):
        novo_indice = (
            self.indice + 1
        ) % len(
            self.opinioes
        )

        await interaction.response.edit_message(
            view=OpiniaoLayout(
                self.opinioes,
                novo_indice,
                guild_id=(
                    self.guild_id
                ),
                dono_user_id=(
                    self.dono_user_id
                ),
                opcoes=self.opcoes,
            )
        )

    async def trocar_tipo(
        self,
        interaction,
    ):
        await interaction.response.edit_message(
            content=(
                "Quais opiniões "
                "deseja ver?"
            ),
            embed=None,
            attachments=[],
            view=EscolherOpiniaoView(
                self.guild_id,
                self.dono_user_id,
                self.opcoes,
            ),
        )

    async def fechar(
        self,
        interaction,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# ESCOLHER TIPO DE OPINIÃO
# ============================================================

class EscolherOpiniaoView(
    discord.ui.View
):
    def __init__(
        self,
        guild_id,
        dono_user_id,
        opcoes,
        *,
        ocultar_tipo=None,
        mostrar_voltar=False,
    ):
        super().__init__(
            timeout=300
        )

        self.guild_id = guild_id
        self.dono_user_id = (
            dono_user_id
        )

        self.opcoes = opcoes

        self.ocultar_tipo = (
            ocultar_tipo
        )

        self.mostrar_voltar = (
            mostrar_voltar
        )

        for tipo, nome in opcoes:
            if tipo == ocultar_tipo:
                continue

            botao = discord.ui.Button(
                label=nome,
                style=(
                    discord.ButtonStyle.secondary
                ),
            )

            async def callback(
                interaction,
                tipo=tipo,
                nome=nome,
            ):
                await self.abrir(
                    interaction,
                    tipo,
                    nome,
                )

            botao.callback = (
                callback
            )

            self.add_item(
                botao
            )

        if mostrar_voltar:
            voltar = discord.ui.Button(
                label="Voltar",
                style=(
                    discord.ButtonStyle.secondary
                ),
            )

            voltar.callback = (
                self.voltar
            )

            self.add_item(
                voltar
            )

        fechar = discord.ui.Button(
            label="Fechar",
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        fechar.callback = (
            self.fechar
        )

        self.add_item(
            fechar
        )

    async def abrir(
        self,
        interaction,
        tipo,
        nome,
    ):
        opinioes = (
            db_midias.listar_opinioes(
                self.guild_id,
                self.dono_user_id,
                tipo,
            )
        )

        # ----------------------------------------------------
        # SEM OPINIÕES
        #
        # Não mostramos novamente o tipo que acabou de ser
        # escolhido.
        # ----------------------------------------------------

        if not opinioes:
            await interaction.response.edit_message(
                content=(
                    f"Não há opiniões de "
                    f"**{nome.lower()}** "
                    "para mostrar."
                    "\n\n"
                    "Você pode escolher "
                    "outro tipo:"
                ),
                embed=None,
                attachments=[],
                view=EscolherOpiniaoView(
                    self.guild_id,
                    self.dono_user_id,
                    self.opcoes,
                    ocultar_tipo=tipo,
                    mostrar_voltar=True,
                ),
            )

            return

        # ----------------------------------------------------
        # COM OPINIÕES
        # ----------------------------------------------------

        await interaction.response.edit_message(
            content=None,
            embed=None,
            attachments=[],
            view=OpiniaoLayout(
                opinioes,
                guild_id=(
                    self.guild_id
                ),
                dono_user_id=(
                    self.dono_user_id
                ),
                opcoes=self.opcoes,
            ),
        )

    async def voltar(
        self,
        interaction,
    ):
        await interaction.response.edit_message(
            content=(
                "Quais opiniões "
                "deseja ver?"
            ),
            embed=None,
            attachments=[],
            view=EscolherOpiniaoView(
                self.guild_id,
                self.dono_user_id,
                self.opcoes,
            ),
        )

    async def fechar(
        self,
        interaction,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# LISTA PÚBLICA
# ============================================================

class ListaPublicaView(
    discord.ui.View
):
    def __init__(
        self,
        guild_id,
        dono_user_id,
        nome_usuario,
        categoria="jogos",
    ):
        super().__init__(
            timeout=None
        )

        self.guild_id = guild_id
        self.dono_user_id = (
            dono_user_id
        )

        self.nome_usuario = (
            nome_usuario
        )

        if categoria not in CATEGORIAS:
            categoria = "jogos"

        self.categoria = categoria

        self.voltar.custom_id = (
            "lista:voltar:"
            f"{guild_id}:"
            f"{dono_user_id}"
        )

        self.opinioes.custom_id = (
            "lista:opinioes:"
            f"{guild_id}:"
            f"{dono_user_id}"
        )

        self.proxima.custom_id = (
            "lista:proxima:"
            f"{guild_id}:"
            f"{dono_user_id}"
        )

    def embed(
        self,
    ):
        midias = (
            db_midias.listar_midias_usuario(
                self.guild_id,
                self.dono_user_id,
            )
        )

        if self.categoria == "jogos":
            return criar_embed_jogos(
                self.nome_usuario,
                midias,
            )

        if (
            self.categoria
            == "filmes_series"
        ):
            return (
                criar_embed_filmes_series(
                    self.nome_usuario,
                    midias,
                )
            )

        if (
            self.categoria
            == "anime_manga"
        ):
            return (
                criar_embed_anime_manga(
                    self.nome_usuario,
                    midias,
                )
            )

        if (
            self.categoria
            == "musica"
        ):
            return criar_embed_musica(
                self.nome_usuario,
                midias,
            )

        return criar_embed_jogos(
            self.nome_usuario,
            midias,
        )

    async def mudar_categoria(
        self,
        interaction,
        nova_categoria,
    ):
        self.categoria = (
            nova_categoria
        )

        db_midias.atualizar_categoria_lista(
            self.guild_id,
            self.dono_user_id,
            nova_categoria,
        )

        nova_view = (
            ListaPublicaView(
                self.guild_id,
                self.dono_user_id,
                self.nome_usuario,
                nova_categoria,
            )
        )

        await interaction.response.edit_message(
            content=None,
            embed=nova_view.embed(),
            view=nova_view,
        )

    @discord.ui.button(
        label="Voltar",
        style=discord.ButtonStyle.secondary,
    )
    async def voltar(
        self,
        interaction,
        button,
    ):
        await self.mudar_categoria(
            interaction,
            categoria_anterior(
                self.categoria
            ),
        )

    @discord.ui.button(
        label="Opiniões",
        style=discord.ButtonStyle.secondary,
    )
    async def opinioes(
        self,
        interaction,
        button,
    ):
        # ----------------------------------------------------
        # JOGOS
        # ----------------------------------------------------

        if self.categoria == "jogos":
            opinioes = (
                db_midias.listar_opinioes(
                    self.guild_id,
                    self.dono_user_id,
                    "game",
                )
            )

            if not opinioes:
                await interaction.response.send_message(
                    (
                        "Não há opiniões de "
                        "**jogos** para mostrar."
                    ),
                    ephemeral=True,
                    delete_after=4,
                )

                return

            await interaction.response.send_message(
                view=OpiniaoLayout(
                    opinioes
                ),
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # FILMES / SÉRIES
        # ----------------------------------------------------

        if (
            self.categoria
            == "filmes_series"
        ):
            opcoes = [
                (
                    "movie",
                    "Filmes",
                ),
                (
                    "tv",
                    "Séries",
                ),
            ]

            await interaction.response.send_message(
                (
                    "Quais opiniões "
                    "deseja ver?"
                ),
                view=EscolherOpiniaoView(
                    self.guild_id,
                    self.dono_user_id,
                    opcoes,
                ),
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # ANIME / MANGÁ
        # ----------------------------------------------------

        if (
            self.categoria
            == "anime_manga"
        ):
            opcoes = [
                (
                    "anime",
                    "Animes",
                ),
                (
                    "manga",
                    "Mangás",
                ),
            ]

            await interaction.response.send_message(
                (
                    "Quais opiniões "
                    "deseja ver?"
                ),
                view=EscolherOpiniaoView(
                    self.guild_id,
                    self.dono_user_id,
                    opcoes,
                ),
                ephemeral=True,
            )

            return

        # ----------------------------------------------------
        # MÚSICA / ÁLBUM / ARTISTA
        # ----------------------------------------------------

        if self.categoria == "musica":
            opcoes = [
                (
                    "music",
                    "Músicas",
                ),
                (
                    "album",
                    "Álbuns",
                ),
                (
                    "artist",
                    "Artistas",
                ),
            ]

            await interaction.response.send_message(
                (
                    "Quais opiniões "
                    "deseja ver?"
                ),
                view=EscolherOpiniaoView(
                    self.guild_id,
                    self.dono_user_id,
                    opcoes,
                ),
                ephemeral=True,
            )

            return

    @discord.ui.button(
        label="Próxima",
        style=discord.ButtonStyle.secondary,
    )
    async def proxima(
        self,
        interaction,
        button,
    ):
        await self.mudar_categoria(
            interaction,
            categoria_proxima(
                self.categoria
            ),
        )


# ============================================================
# ATUALIZAR LISTA PÚBLICA
# ============================================================

async def atualizar_lista_publica(
    guild,
    user,
):
    if guild is None:
        return False

    registro = (
        db_midias.obter_lista_publica(
            guild.id,
            user.id,
        )
    )

    if not registro:
        return False

    canal = guild.get_channel(
        registro[
            "channel_id"
        ]
    )

    if canal is None:
        try:
            canal = (
                await guild.fetch_channel(
                    registro[
                        "channel_id"
                    ]
                )
            )

        except (
            discord.NotFound,
            discord.Forbidden,
            discord.HTTPException,
        ):
            return False

    try:
        mensagem = (
            await canal.fetch_message(
                registro[
                    "message_id"
                ]
            )
        )

    except (
        discord.NotFound,
        discord.Forbidden,
        discord.HTTPException,
    ):
        return False

    membro = guild.get_member(
        user.id
    )

    if membro is not None:
        nome_usuario = (
            membro.display_name
        )

    else:
        nome_usuario = (
            user.display_name
        )

    categoria = registro.get(
        "categoria",
        "jogos",
    )

    if categoria not in CATEGORIAS:
        categoria = "jogos"

        db_midias.atualizar_categoria_lista(
            guild.id,
            user.id,
            categoria,
        )

    view = ListaPublicaView(
        guild.id,
        user.id,
        nome_usuario,
        categoria,
    )

    try:
        await mensagem.edit(
            content=None,
            embed=view.embed(),
            view=view,
        )

    except discord.HTTPException:
        return False

    return True


# ============================================================
# /LISTA
# ============================================================

def registrar_lista(
    bot,
):
    @bot.tree.command(
        name="lista",
        description=(
            "Crie ou atualize "
            "sua lista de mídias."
        ),
    )
    async def lista(
        interaction: discord.Interaction,
    ):
        if (
            interaction.guild is None
            or interaction.channel is None
        ):
            await interaction.response.send_message(
                (
                    "Use esse comando "
                    "dentro de um servidor."
                ),
                ephemeral=True,
                delete_after=4,
            )

            return

        guild_id = (
            interaction.guild.id
        )

        user_id = (
            interaction.user.id
        )

        nome_usuario = (
            interaction.user.display_name
        )

        registro = (
            db_midias.obter_lista_publica(
                guild_id,
                user_id,
            )
        )

        # ====================================================
        # LISTA JÁ EXISTE
        # ====================================================

        if registro:
            canal = (
                interaction.guild.get_channel(
                    registro[
                        "channel_id"
                    ]
                )
            )

            if canal is None:
                try:
                    canal = (
                        await interaction.guild.fetch_channel(
                            registro[
                                "channel_id"
                            ]
                        )
                    )

                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException,
                ):
                    canal = None

            if canal is not None:
                try:
                    mensagem = (
                        await canal.fetch_message(
                            registro[
                                "message_id"
                            ]
                        )
                    )

                    categoria = (
                        registro.get(
                            "categoria",
                            "jogos",
                        )
                    )

                    if (
                        categoria
                        not in CATEGORIAS
                    ):
                        categoria = "jogos"

                    view = (
                        ListaPublicaView(
                            guild_id,
                            user_id,
                            nome_usuario,
                            categoria,
                        )
                    )

                    await mensagem.edit(
                        content=None,
                        embed=view.embed(),
                        view=view,
                    )

                    await interaction.response.send_message(
                        (
                            "✓ Sua lista "
                            "foi atualizada."
                        ),
                        ephemeral=True,
                        delete_after=4,
                    )

                    return

                except (
                    discord.NotFound,
                    discord.Forbidden,
                    discord.HTTPException,
                ):
                    pass

        # ====================================================
        # NOVA LISTA
        # ====================================================

        view = ListaPublicaView(
            guild_id,
            user_id,
            nome_usuario,
            "jogos",
        )

        await interaction.response.defer(
            ephemeral=True
        )

        try:
            mensagem = (
                await interaction.channel.send(
                    embed=view.embed(),
                    view=view,
                )
            )

        except discord.HTTPException as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui criar "
                    "sua lista."
                    "\n"
                    f"`{erro}`"
                )
            )

            fechar_depois(
                interaction,
                6,
            )

            return

        db_midias.salvar_lista_publica(
            guild_id,
            user_id,
            interaction.channel.id,
            mensagem.id,
            "jogos",
        )

        await interaction.edit_original_response(
            content=(
                "✓ Sua lista foi criada."
            )
        )

        fechar_depois(
            interaction
        )