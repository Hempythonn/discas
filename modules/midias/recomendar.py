import asyncio

import discord

from modules.midias.providers.tmdb import (
    pesquisar_tmdb,
)

from modules.midias.providers.anilist import (
    pesquisar_anilist,
)

from modules.midias.providers.igdb import (
    pesquisar_igdb,
)

from modules.midias.providers.theaudiodb import (
    pesquisar_theaudiodb,
)

from modules.midias.database import (
    MidiasDatabase,
    formatar_data_finalizacao,
)

from modules.midias.lista import (
    atualizar_lista_publica,
)


# ============================================================
# CONFIGURAÇÃO
# ============================================================

DB_PATH = "data/bot.db"

db_midias = MidiasDatabase(
    DB_PATH
)


# ============================================================
# UTILIDADES
# ============================================================

def nome_tipo(tipo):
    return {
        "game": "Jogo",
        "movie": "Filme",
        "tv": "Série",
        "anime": "Anime",
        "manga": "Mangá",
        "music": "Música",
        "album": "Álbum",
        "artist": "Artista",
    }.get(
        tipo,
        "Mídia",
    )


def nome_status(
    status,
    tipo,
):
    if status == "quero_ver":
        return {
            "game": "Quero jogar",
            "movie": "Quero assistir",
            "tv": "Quero assistir",
            "anime": "Quero assistir",
            "manga": "Quero ler",
            "music": "Quero ouvir",
            "album": "Quero ouvir",
            "artist": "Quero ouvir",
        }.get(
            tipo,
            "Quero ver",
        )

    if status == "em_andamento":
        return {
            "game": "Jogando",
            "movie": "Assistindo",
            "tv": "Assistindo",
            "anime": "Assistindo",
            "manga": "Lendo",
            "music": "Ouvindo",
            "album": "Ouvindo",
            "artist": "Ouvindo",
        }.get(
            tipo,
            "Em andamento",
        )

    if status == "finalizado":
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

    return status


def limitar_texto(
    texto,
    limite=900,
):
    if not texto:
        return (
            "Descrição não disponível."
        )

    if len(texto) <= limite:
        return texto

    return (
        texto[
            : limite - 3
        ].rstrip()
        + "..."
    )


def ano_midia(
    resultado,
):
    return str(
        resultado.get("ano")
        or "Ano desconhecido"
    )


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
# EMBED PRIVADO DE PRÉVIA
# ============================================================

def criar_embed_previa(
    resultado,
    *,
    recomendado_por=None,
):
    embed = discord.Embed(
        title=resultado["titulo"],
        description=limitar_texto(
            resultado.get(
                "sinopse"
            )
        ),
    )

    embed.add_field(
        name="Tipo",
        value=nome_tipo(
            resultado["tipo"]
        ),
        inline=True,
    )

    embed.add_field(
        name="Ano",
        value=ano_midia(
            resultado
        ),
        inline=True,
    )

    if recomendado_por:
        embed.set_footer(
            text=(
                "Recomendado por "
                f"{recomendado_por}"
            )
        )

    if resultado.get("capa"):
        embed.set_thumbnail(
            url=resultado["capa"]
        )

    return embed


# ============================================================
# CONTAINER DO CARD PÚBLICO
# ============================================================

def criar_container_midia(
    resultado,
    *,
    recomendado_por=None,
):
    tipo = nome_tipo(
        resultado["tipo"]
    )

    descricao = limitar_texto(
        resultado.get(
            "sinopse"
        )
    )

    cabecalho = (
        discord.ui.TextDisplay(
            f"## {resultado['titulo']}\n"
            f"`{ano_midia(resultado)}` "
            f"• **{tipo}**"
        )
    )

    itens = []

    if resultado.get("capa"):
        itens.append(
            discord.ui.Section(
                cabecalho,
                accessory=(
                    discord.ui.Thumbnail(
                        resultado["capa"],
                        description=(
                            "Capa de "
                            f"{resultado['titulo']}"
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

    itens.append(
        discord.ui.TextDisplay(
            descricao
        )
    )

    if recomendado_por:
        itens.append(
            discord.ui.Separator()
        )

        itens.append(
            discord.ui.TextDisplay(
                "-# Recomendado por "
                f"**{recomendado_por}**"
            )
        )

    return discord.ui.Container(
        *itens
    )


# ============================================================
# STATUS DO USUÁRIO
# ============================================================

async def definir_status_usuario(
    interaction,
    resultado,
    novo_status,
):
    guild_id = (
        interaction.guild.id
    )

    user_id = (
        interaction.user.id
    )

    # --------------------------------------------------------
    # FINALIZADO
    #
    # Usa finalizar() porque ele preserva a data caso a mídia
    # já esteja finalizada.
    # --------------------------------------------------------

    if novo_status == "finalizado":
        resultado_db = (
            db_midias.finalizar(
                guild_id,
                user_id,
                resultado,
            )
        )

        midia_id = (
            resultado_db[
                "midia_id"
            ]
        )

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        estado = (
            db_midias.obter_estado(
                guild_id,
                user_id,
                midia_id,
            )
        )

        return {
            "midia_id": midia_id,
            "status": "finalizado",
            "finalizado_em": (
                resultado_db.get(
                    "finalizado_em"
                )
            ),
            "favorito": bool(
                estado
                and estado.get(
                    "favorito"
                )
            ),
        }

    # --------------------------------------------------------
    # QUERO / EM ANDAMENTO
    # --------------------------------------------------------

    registro = (
        db_midias.adicionar_quero_ver(
            guild_id,
            user_id,
            resultado,
        )
    )

    midia_id = (
        registro[
            "midia_id"
        ]
    )

    db_midias.alterar_status(
        guild_id,
        user_id,
        midia_id,
        novo_status,
    )

    await atualizar_lista_publica(
        interaction.guild,
        interaction.user,
    )

    estado = (
        db_midias.obter_estado(
            guild_id,
            user_id,
            midia_id,
        )
    )

    return {
        "midia_id": midia_id,
        "status": novo_status,
        "finalizado_em": (
            estado.get(
                "finalizado_em"
            )
            if estado
            else None
        ),
        "favorito": bool(
            estado
            and estado.get(
                "favorito"
            )
        ),
    }


# ============================================================
# OPINIÃO DEPOIS DE CONCLUIR
# ============================================================

class OpiniaoFinalModal(
    discord.ui.Modal
):
    def __init__(
        self,
        resultado,
        midia_id,
        *,
        favoritado=False,
    ):
        super().__init__(
            title="Escrever opinião"
        )

        self.resultado = resultado
        self.midia_id = midia_id
        self.favoritado = (
            favoritado
        )

        self.nota = (
            discord.ui.TextInput(
                label="Nota (opcional)",
                placeholder=(
                    "De 0 a 10. "
                    "Ex.: 8 ou 9.5"
                ),
                required=False,
                max_length=4,
            )
        )

        self.opiniao = (
            discord.ui.TextInput(
                label="Opinião",
                placeholder=(
                    "Escreva o que "
                    "você achou..."
                ),
                required=True,
                max_length=1500,
                style=(
                    discord.TextStyle.paragraph
                ),
            )
        )

        self.add_item(
            self.nota
        )

        self.add_item(
            self.opiniao
        )

    async def on_submit(
        self,
        interaction,
    ):
        nota_texto = (
            str(
                self.nota.value
            )
            .strip()
            .replace(",", ".")
        )

        nota = None

        if nota_texto:
            try:
                nota = float(
                    nota_texto
                )

            except ValueError:
                await interaction.response.send_message(
                    (
                        "A nota precisa ser "
                        "um número entre "
                        "**0 e 10**."
                    ),
                    ephemeral=True,
                    delete_after=4,
                )

                return

            if not 0 <= nota <= 10:
                await interaction.response.send_message(
                    (
                        "A nota precisa ficar "
                        "entre **0 e 10**."
                    ),
                    ephemeral=True,
                    delete_after=4,
                )

                return

        await interaction.response.defer()

        db_midias.salvar_opiniao(
            interaction.guild.id,
            interaction.user.id,
            self.midia_id,
            str(
                self.opiniao.value
            ).strip(),
            nota,
        )

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        # ----------------------------------------------------
        # JÁ FAVORITOU
        #
        # As duas decisões foram concluídas.
        # Mostra confirmação e fecha.
        # ----------------------------------------------------

        if self.favoritado:
            await interaction.edit_original_response(
                content=(
                    "✓ Opinião salva e "
                    "**favorito mantido**."
                ),
                view=None,
            )

            fechar_depois(
                interaction
            )

            return

        # ----------------------------------------------------
        # AINDA NÃO FAVORITOU
        #
        # A mesma caixa segue para a próxima decisão.
        # ----------------------------------------------------

        await interaction.edit_original_response(
            content=(
                "✓ **Opinião salva.**"
                "\n\n"
                "Deseja favoritar também?"
            ),
            view=DepoisOpiniaoView(
                self.resultado,
                self.midia_id,
            ),
        )


# ============================================================
# DEPOIS DE ESCREVER OPINIÃO
# ============================================================

class DepoisOpiniaoView(
    discord.ui.View
):
    def __init__(
        self,
        resultado,
        midia_id,
    ):
        super().__init__(
            timeout=300
        )

        self.resultado = resultado
        self.midia_id = midia_id

    @discord.ui.button(
        label="Favoritar",
        style=discord.ButtonStyle.secondary,
    )
    async def favoritar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        resultado = (
            db_midias.alterar_favorito(
                interaction.guild.id,
                interaction.user.id,
                self.midia_id,
            )
        )

        if not resultado[
            "sucesso"
        ]:
            if (
                resultado.get(
                    "motivo"
                )
                == "limite"
            ):
                await interaction.edit_original_response(
                    content=(
                        "Você já possui "
                        "**5 favoritos desse "
                        "tipo de mídia**."
                        "\n\n"
                        "Remova um favorito "
                        "antes de tentar novamente."
                    ),
                    view=self,
                )

                return

            await interaction.edit_original_response(
                content=(
                    "Não encontrei essa "
                    "mídia na sua lista."
                ),
                view=FecharView(),
            )

            return

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        if resultado[
            "favorito"
        ]:
            await interaction.edit_original_response(
                content=(
                    "✓ Opinião salva e "
                    "**adicionado aos favoritos**."
                ),
                view=None,
            )

            fechar_depois(
                interaction
            )

            return

        await interaction.edit_original_response(
            content=(
                "✓ Opinião salva."
                "\n\n"
                "A mídia não está mais "
                "nos favoritos."
            ),
            view=FecharView(),
        )

    @discord.ui.button(
        label="Agora não",
        style=discord.ButtonStyle.secondary,
    )
    async def agora_nao(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# DEPOIS DE FINALIZAR
# ============================================================

class DepoisFinalizarView(
    discord.ui.View
):
    def __init__(
        self,
        resultado,
        midia_id,
        *,
        favoritado=False,
    ):
        super().__init__(
            timeout=300
        )

        self.resultado = resultado
        self.midia_id = midia_id
        self.favoritado = (
            favoritado
        )

        if favoritado:
            self.favoritar.label = (
                "Favoritado"
            )

            self.favoritar.disabled = (
                True
            )

    @discord.ui.button(
        label="Escrever opinião",
        style=discord.ButtonStyle.secondary,
    )
    async def escrever_opiniao(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            OpiniaoFinalModal(
                self.resultado,
                self.midia_id,
                favoritado=(
                    self.favoritado
                ),
            )
        )

    @discord.ui.button(
        label="Favoritar",
        style=discord.ButtonStyle.secondary,
    )
    async def favoritar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        resultado = (
            db_midias.alterar_favorito(
                interaction.guild.id,
                interaction.user.id,
                self.midia_id,
            )
        )

        if not resultado[
            "sucesso"
        ]:
            if (
                resultado.get(
                    "motivo"
                )
                == "limite"
            ):
                await interaction.edit_original_response(
                    content=(
                        "Você já possui "
                        "**5 favoritos desse "
                        "tipo de mídia**."
                        "\n\n"
                        "Deseja deixar uma opinião?"
                    ),
                    view=self,
                )

                return

            await interaction.edit_original_response(
                content=(
                    "Não encontrei essa "
                    "mídia na sua lista."
                ),
                view=FecharView(),
            )

            return

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        self.favoritado = bool(
            resultado["favorito"]
        )

        if self.favoritado:
            button.label = (
                "Favoritado"
            )

            button.disabled = (
                True
            )

            await interaction.edit_original_response(
                content=(
                    f"✓ **{self.resultado['titulo']}** "
                    "foi adicionado aos favoritos."
                    "\n\n"
                    "Deseja deixar uma opinião?"
                ),
                view=self,
            )

            return

        button.label = (
            "Favoritar"
        )

        button.disabled = (
            False
        )

        await interaction.edit_original_response(
            content=(
                f"**{self.resultado['titulo']}** "
                "foi removido dos favoritos."
                "\n\n"
                "Deseja deixar uma opinião?"
            ),
            view=self,
        )

    @discord.ui.button(
        label="Agora não",
        style=discord.ButtonStyle.secondary,
    )
    async def agora_nao(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# FECHAR
# ============================================================

class FecharView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# CARD PÚBLICO
# ============================================================

class RecomendacaoPublicaLayout(
    discord.ui.LayoutView
):
    def __init__(
        self,
        resultado,
        recomendado_por,
    ):
        super().__init__(
            timeout=None
        )

        self.resultado = resultado

        container = (
            criar_container_midia(
                resultado,
                recomendado_por=(
                    recomendado_por
                ),
            )
        )

        botoes = (
            discord.ui.ActionRow()
        )

        for status in (
            "quero_ver",
            "em_andamento",
            "finalizado",
        ):
            botao = (
                discord.ui.Button(
                    label=nome_status(
                        status,
                        resultado["tipo"],
                    ),
                    style=(
                        discord.ButtonStyle.secondary
                    ),
                    custom_id=(
                        "midia:status:"
                        f"{resultado['provider']}:"
                        f"{resultado['tipo']}:"
                        f"{status}:"
                        f"{resultado['id']}"
                    ),
                )
            )

            if status == "quero_ver":
                botao.callback = (
                    self.quero
                )

            elif (
                status
                == "em_andamento"
            ):
                botao.callback = (
                    self.andamento
                )

            else:
                botao.callback = (
                    self.finalizado
                )

            botoes.add_item(
                botao
            )

        container.add_item(
            discord.ui.Separator(
                visible=False
            )
        )

        container.add_item(
            botoes
        )

        self.add_item(
            container
        )

    async def alterar(
        self,
        interaction,
        status,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                (
                    "Essa função precisa ser "
                    "usada dentro de um servidor."
                ),
                ephemeral=True,
                delete_after=4,
            )

            return

        await interaction.response.defer(
            ephemeral=True,
            thinking=True,
        )

        try:
            estado = (
                await definir_status_usuario(
                    interaction,
                    self.resultado,
                    status,
                )
            )

        except Exception as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui atualizar "
                    "essa mídia."
                    "\n"
                    f"`{erro}`"
                ),
                view=FecharView(),
            )

            return

        status_nome = (
            nome_status(
                status,
                self.resultado["tipo"],
            )
        )

        # ----------------------------------------------------
        # AÇÃO SIMPLES
        #
        # Confirma e desaparece sozinha.
        # ----------------------------------------------------

        if status != "finalizado":
            await interaction.edit_original_response(
                content=(
                    "✓ "
                    f"**{self.resultado['titulo']}** "
                    "agora está como "
                    f"**{status_nome}**."
                ),
                view=None,
            )

            fechar_depois(
                interaction
            )

            return

        # ----------------------------------------------------
        # FINALIZAÇÃO
        #
        # Há uma nova decisão, então permanece.
        # ----------------------------------------------------

        data = (
            formatar_data_finalizacao(
                estado.get(
                    "finalizado_em"
                )
            )
        )

        if data:
            linha_status = (
                f"**{status_nome}** "
                f"em **{data}**."
            )

        else:
            linha_status = (
                f"**{status_nome}**."
            )

        await interaction.edit_original_response(
            content=(
                f"**{self.resultado['titulo']}**"
                "\n\n"
                f"{linha_status}"
                "\n\n"
                "Deseja deixar uma opinião?"
            ),
            view=DepoisFinalizarView(
                self.resultado,
                estado["midia_id"],
                favoritado=(
                    estado[
                        "favorito"
                    ]
                ),
            ),
        )

    async def quero(
        self,
        interaction,
    ):
        await self.alterar(
            interaction,
            "quero_ver",
        )

    async def andamento(
        self,
        interaction,
    ):
        await self.alterar(
            interaction,
            "em_andamento",
        )

    async def finalizado(
        self,
        interaction,
    ):
        await self.alterar(
            interaction,
            "finalizado",
        )


# ============================================================
# RESULTADOS
# ============================================================

class ResultadoMidiaSelect(
    discord.ui.Select
):
    def __init__(
        self,
        resultados,
        view_voltar,
    ):
        self.resultados = (
            resultados
        )

        self.view_voltar = (
            view_voltar
        )

        opcoes = []

        for indice, resultado in enumerate(
            resultados[:25]
        ):
            opcoes.append(
                discord.SelectOption(
                    label=(
                        resultado[
                            "titulo"
                        ][:100]
                    ),
                    description=(
                        f"{nome_tipo(
                            resultado['tipo']
                        )} • "
                        f"{ano_midia(
                            resultado
                        )}"
                    )[:100],
                    value=str(
                        indice
                    ),
                )
            )

        super().__init__(
            placeholder=(
                "Escolha o resultado "
                "correto..."
            ),
            min_values=1,
            max_values=1,
            options=opcoes,
        )

    async def callback(
        self,
        interaction,
    ):
        indice = int(
            self.values[0]
        )

        resultado = (
            self.resultados[
                indice
            ]
        )

        await interaction.response.edit_message(
            content=None,
            embed=criar_embed_previa(
                resultado
            ),
            view=PreviaMidiaView(
                resultado,
                self.resultados,
                self.view_voltar,
            ),
        )


class ResultadoMidiaView(
    discord.ui.View
):
    def __init__(
        self,
        resultados,
        view_voltar,
    ):
        super().__init__(
            timeout=300
        )

        self.resultados = (
            resultados
        )

        self.view_voltar = (
            view_voltar
        )

        self.add_item(
            ResultadoMidiaSelect(
                resultados,
                view_voltar,
            )
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
        await interaction.response.edit_message(
            content=(
                "**O que você procura?**"
            ),
            embed=None,
            view=self.view_voltar,
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# PRÉVIA
# ============================================================

class PreviaMidiaView(
    discord.ui.View
):
    def __init__(
        self,
        resultado,
        resultados,
        view_voltar,
    ):
        super().__init__(
            timeout=300
        )

        self.resultado = (
            resultado
        )

        self.resultados = (
            resultados
        )

        self.view_voltar = (
            view_voltar
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
        await interaction.response.edit_message(
            content=(
                "**Resultados encontrados**"
                "\n"
                "Escolha qual deles "
                "você queria:"
            ),
            embed=None,
            view=ResultadoMidiaView(
                self.resultados,
                self.view_voltar,
            ),
        )

    @discord.ui.button(
        label="Selecionar",
        style=discord.ButtonStyle.secondary,
    )
    async def selecionar(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                "**Publicar esta "
                "recomendação?**"
            ),
            embed=criar_embed_previa(
                self.resultado,
                recomendado_por=(
                    interaction.user.display_name
                ),
            ),
            view=ConfirmarPublicacaoView(
                self.resultado,
                self.resultados,
                self.view_voltar,
                interaction.user.display_name,
            ),
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# CONFIRMAR PUBLICAÇÃO
# ============================================================

class ConfirmarPublicacaoView(
    discord.ui.View
):
    def __init__(
        self,
        resultado,
        resultados,
        view_voltar,
        recomendado_por,
    ):
        super().__init__(
            timeout=300
        )

        self.resultado = (
            resultado
        )

        self.resultados = (
            resultados
        )

        self.view_voltar = (
            view_voltar
        )

        self.recomendado_por = (
            recomendado_por
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
        await interaction.response.edit_message(
            content=None,
            embed=criar_embed_previa(
                self.resultado
            ),
            view=PreviaMidiaView(
                self.resultado,
                self.resultados,
                self.view_voltar,
            ),
        )

    @discord.ui.button(
        label="Publicar",
        style=discord.ButtonStyle.secondary,
    )
    async def publicar(
        self,
        interaction,
        button,
    ):
        if interaction.channel is None:
            await interaction.response.edit_message(
                content=(
                    "Não consegui identificar "
                    "o canal."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        await interaction.response.defer()

        try:
            await interaction.channel.send(
                view=RecomendacaoPublicaLayout(
                    self.resultado,
                    self.recomendado_por,
                )
            )

        except Exception as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui publicar "
                    "a recomendação."
                    "\n"
                    f"`{erro}`"
                    "\n\n"
                    "Você pode tentar "
                    "novamente ou voltar."
                ),
                embed=criar_embed_previa(
                    self.resultado
                ),
                view=self,
            )

            return

        await interaction.edit_original_response(
            content=(
                "✓ **Recomendação publicada.**"
                "\n\n"
                "Deseja recomendar "
                "outra mídia?"
            ),
            embed=None,
            view=RecomendarOutraView(),
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# RECOMENDAR OUTRA
# ============================================================

class RecomendarOutraView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Sim",
        style=discord.ButtonStyle.secondary,
    )
    async def sim(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                "𐙚 **O que deseja "
                "recomendar?**"
            ),
            embed=None,
            view=TipoMidiaView(),
        )

    @discord.ui.button(
        label="Não",
        style=discord.ButtonStyle.secondary,
    )
    async def nao(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# MOSTRAR RESULTADOS
# ============================================================

async def mostrar_resultados(
    interaction,
    resultados,
    view_voltar,
):
    if not resultados:
        await interaction.edit_original_response(
            content=(
                "Não encontrei nenhum "
                "resultado com esses dados."
                "\n\n"
                "Você pode tentar novamente "
                "ou voltar."
            ),
            embed=None,
            view=view_voltar,
        )

        return

    await interaction.edit_original_response(
        content=(
            "**Resultados encontrados**"
            "\n"
            "Escolha qual deles "
            "você queria:"
        ),
        embed=None,
        view=ResultadoMidiaView(
            resultados,
            view_voltar,
        ),
    )


# ============================================================
# PESQUISA TMDB
# ============================================================

class PesquisaTMDBModal(
    discord.ui.Modal
):
    def __init__(
        self,
        tipo,
    ):
        self.tipo = tipo

        super().__init__(
            title=(
                "Pesquisar filme"
                if tipo == "movie"
                else "Pesquisar série"
            )
        )

        self.nome = (
            discord.ui.TextInput(
                label="Nome",
                placeholder=(
                    "Digite o nome que "
                    "deseja procurar..."
                ),
                required=True,
                max_length=100,
            )
        )

        self.add_item(
            self.nome
        )

    async def on_submit(
        self,
        interaction,
    ):
        await interaction.response.defer()

        try:
            resultados = (
                await pesquisar_tmdb(
                    str(
                        self.nome.value
                    ).strip(),
                    self.tipo,
                )
            )

        except Exception as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui consultar "
                    "o TMDB."
                    "\n"
                    f"`{erro}`"
                    "\n\n"
                    "Você pode tentar novamente."
                ),
                embed=None,
                view=TipoTMDBView(),
            )

            return

        await mostrar_resultados(
            interaction,
            resultados,
            TipoTMDBView(),
        )


# ============================================================
# PESQUISA ANILIST
# ============================================================

class PesquisaAniListModal(
    discord.ui.Modal
):
    def __init__(
        self,
        tipo,
    ):
        self.tipo = tipo

        super().__init__(
            title=(
                "Pesquisar anime"
                if tipo == "anime"
                else "Pesquisar mangá"
            )
        )

        self.nome = (
            discord.ui.TextInput(
                label="Nome",
                placeholder=(
                    "Digite o nome que "
                    "deseja procurar..."
                ),
                required=True,
                max_length=100,
            )
        )

        self.add_item(
            self.nome
        )

    async def on_submit(
        self,
        interaction,
    ):
        await interaction.response.defer()

        try:
            resultados = (
                await pesquisar_anilist(
                    str(
                        self.nome.value
                    ).strip(),
                    self.tipo,
                )
            )

        except Exception as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui consultar "
                    "o AniList."
                    "\n"
                    f"`{erro}`"
                    "\n\n"
                    "Você pode tentar novamente."
                ),
                embed=None,
                view=TipoAniListView(),
            )

            return

        await mostrar_resultados(
            interaction,
            resultados,
            TipoAniListView(),
        )


# ============================================================
# PESQUISA IGDB
# ============================================================

class PesquisaIGDBModal(
    discord.ui.Modal
):
    def __init__(self):
        super().__init__(
            title="Pesquisar jogo"
        )

        self.nome = (
            discord.ui.TextInput(
                label="Nome",
                placeholder=(
                    "Digite o nome que "
                    "deseja procurar..."
                ),
                required=True,
                max_length=100,
            )
        )

        self.add_item(
            self.nome
        )

    async def on_submit(
        self,
        interaction,
    ):
        await interaction.response.defer()

        try:
            resultados = (
                await pesquisar_igdb(
                    str(
                        self.nome.value
                    ).strip()
                )
            )

        except Exception as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui consultar "
                    "o IGDB."
                    "\n"
                    f"`{erro}`"
                    "\n\n"
                    "Você pode tentar novamente."
                ),
                embed=None,
                view=TipoMidiaView(),
            )

            return

        await mostrar_resultados(
            interaction,
            resultados,
            TipoMidiaView(),
        )


# ============================================================
# PESQUISA THEAUDIODB
# ============================================================

class PesquisaTheAudioDBModal(
    discord.ui.Modal
):
    def __init__(
        self,
        tipo,
    ):
        self.tipo = tipo

        titulos = {
            "music": "Pesquisar música",
            "album": "Pesquisar álbum",
            "artist": "Pesquisar artista",
        }

        super().__init__(
            title=titulos[tipo]
        )

        if tipo == "artist":
            self.nome = (
                discord.ui.TextInput(
                    label="Artista",
                    placeholder=(
                        "Digite o nome "
                        "do artista..."
                    ),
                    required=True,
                    max_length=100,
                )
            )

            self.artista = None

            self.add_item(
                self.nome
            )

            return

        self.artista = (
            discord.ui.TextInput(
                label="Artista",
                placeholder=(
                    "Digite o nome "
                    "do artista..."
                ),
                required=True,
                max_length=100,
            )
        )

        self.nome = (
            discord.ui.TextInput(
                label=(
                    "Música"
                    if tipo == "music"
                    else "Álbum"
                ),
                placeholder=(
                    "Digite o nome "
                    "da música..."
                    if tipo == "music"
                    else
                    "Digite o nome "
                    "do álbum..."
                ),
                required=True,
                max_length=100,
            )
        )

        self.add_item(
            self.artista
        )

        self.add_item(
            self.nome
        )

    async def on_submit(
        self,
        interaction,
    ):
        await interaction.response.defer()

        try:
            if self.tipo == "artist":
                resultados = (
                    await pesquisar_theaudiodb(
                        "artist",
                        nome=str(
                            self.nome.value
                        ).strip(),
                    )
                )

            else:
                resultados = (
                    await pesquisar_theaudiodb(
                        self.tipo,
                        nome=str(
                            self.nome.value
                        ).strip(),
                        artista=str(
                            self.artista.value
                        ).strip(),
                    )
                )

        except Exception as erro:
            await interaction.edit_original_response(
                content=(
                    "Não consegui consultar "
                    "o TheAudioDB."
                    "\n"
                    f"`{erro}`"
                    "\n\n"
                    "Você pode tentar novamente."
                ),
                embed=None,
                view=TipoTheAudioDBView(),
            )

            return

        await mostrar_resultados(
            interaction,
            resultados,
            TipoTheAudioDBView(),
        )


# ============================================================
# FILME / SÉRIE
# ============================================================

class TipoTMDBView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Filme",
        style=discord.ButtonStyle.secondary,
    )
    async def filme(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaTMDBModal(
                "movie"
            )
        )

    @discord.ui.button(
        label="Série",
        style=discord.ButtonStyle.secondary,
    )
    async def serie(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaTMDBModal(
                "tv"
            )
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
        await interaction.response.edit_message(
            content=(
                "𐙚 **O que deseja "
                "recomendar?**"
            ),
            embed=None,
            view=TipoMidiaView(),
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# ANIME / MANGÁ
# ============================================================

class TipoAniListView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Anime",
        style=discord.ButtonStyle.secondary,
    )
    async def anime(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaAniListModal(
                "anime"
            )
        )

    @discord.ui.button(
        label="Mangá",
        style=discord.ButtonStyle.secondary,
    )
    async def manga(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaAniListModal(
                "manga"
            )
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
        await interaction.response.edit_message(
            content=(
                "𐙚 **O que deseja "
                "recomendar?**"
            ),
            embed=None,
            view=TipoMidiaView(),
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# MÚSICA / ÁLBUM / ARTISTA
# ============================================================

class TipoTheAudioDBView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Música",
        style=discord.ButtonStyle.secondary,
    )
    async def musica(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaTheAudioDBModal(
                "music"
            )
        )

    @discord.ui.button(
        label="Álbum",
        style=discord.ButtonStyle.secondary,
    )
    async def album(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaTheAudioDBModal(
                "album"
            )
        )

    @discord.ui.button(
        label="Artista",
        style=discord.ButtonStyle.secondary,
    )
    async def artista(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaTheAudioDBModal(
                "artist"
            )
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
        await interaction.response.edit_message(
            content=(
                "𐙚 **O que deseja "
                "recomendar?**"
            ),
            embed=None,
            view=TipoMidiaView(),
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# TIPO PRINCIPAL
# ============================================================

class TipoMidiaView(
    discord.ui.View
):
    def __init__(self):
        super().__init__(
            timeout=300
        )

    @discord.ui.button(
        label="Jogo",
        style=discord.ButtonStyle.secondary,
    )
    async def jogo(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            PesquisaIGDBModal()
        )

    @discord.ui.button(
        label="Filme/Série",
        style=discord.ButtonStyle.secondary,
    )
    async def filme_serie(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                "**O que você procura?**"
            ),
            embed=None,
            view=TipoTMDBView(),
        )

    @discord.ui.button(
        label="Anime/Mangá",
        style=discord.ButtonStyle.secondary,
    )
    async def anime_manga(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                "**O que você procura?**"
            ),
            embed=None,
            view=TipoAniListView(),
        )

    @discord.ui.button(
        label="Música",
        style=discord.ButtonStyle.secondary,
    )
    async def musica(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                "**O que você procura?**"
            ),
            embed=None,
            view=TipoTheAudioDBView(),
        )

    @discord.ui.button(
        label="Fechar",
        style=discord.ButtonStyle.secondary,
    )
    async def fechar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        try:
            await interaction.delete_original_response()

        except discord.NotFound:
            pass


# ============================================================
# /RECOMENDAR
# ============================================================

def registrar_recomendacoes(
    bot,
):
    @bot.tree.command(
        name="recomendar",
        description=(
            "Recomende uma mídia."
        ),
    )
    async def recomendar(
        interaction: discord.Interaction,
    ):
        if interaction.guild is None:
            await interaction.response.send_message(
                (
                    "Use esse comando "
                    "dentro de um servidor."
                ),
                ephemeral=True,
                delete_after=4,
            )

            return

        await interaction.response.send_message(
            (
                "𐙚 **O que deseja "
                "recomendar?**"
            ),
            view=TipoMidiaView(),
            ephemeral=True,
        )