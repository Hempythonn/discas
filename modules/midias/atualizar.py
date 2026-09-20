import asyncio

import discord

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

db = MidiasDatabase(
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


def nome_plural(tipo):
    return {
        "game": "jogos",
        "movie": "filmes",
        "tv": "séries",
        "anime": "animes",
        "manga": "mangás",
        "music": "músicas",
        "album": "álbuns",
        "artist": "artistas",
    }.get(
        tipo,
        "mídias",
    )


def artigo_tipo(tipo):
    if tipo in (
        "movie",
        "tv",
        "music",
    ):
        return "uma"

    return "um"


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
# EMBED DA MÍDIA
# ============================================================

def criar_embed_midia(
    midia,
):
    embed = discord.Embed(
        title=midia["titulo"],
        description=(
            f"**{nome_tipo(midia['tipo'])}**"
        ),
    )

    if midia.get("capa"):
        embed.set_thumbnail(
            url=midia["capa"]
        )

    status = nome_status(
        midia["status"],
        midia["tipo"],
    )

    if (
        midia["status"]
        == "finalizado"
        and midia.get(
            "finalizado_em"
        )
    ):
        data = (
            formatar_data_finalizacao(
                midia[
                    "finalizado_em"
                ]
            )
        )

        if data:
            status += (
                f" • {data}"
            )

    embed.add_field(
        name="Status",
        value=status,
        inline=False,
    )

    embed.add_field(
        name="Favorito",
        value=(
            "Sim"
            if bool(
                midia["favorito"]
            )
            else "Não"
        ),
        inline=False,
    )

    if midia.get("opiniao"):
        embed.add_field(
            name="Opinião",
            value="Registrada",
            inline=False,
        )

        if (
            midia.get("nota")
            is not None
        ):
            embed.add_field(
                name="Nota",
                value=(
                    f"{midia['nota']:g}/10"
                ),
                inline=False,
            )

    return embed


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
# SELEÇÃO DE MÍDIA
# ============================================================

class MidiaSelect(
    discord.ui.Select
):
    def __init__(
        self,
        midias,
        tipo,
    ):
        self.midias = midias
        self.tipo = tipo

        opcoes = []

        for midia in midias[:25]:
            descricao = nome_status(
                midia["status"],
                midia["tipo"],
            )

            if bool(
                midia["favorito"]
            ):
                descricao += (
                    " • Favorito"
                )

            opcoes.append(
                discord.SelectOption(
                    label=(
                        midia[
                            "titulo"
                        ][:100]
                    ),
                    description=(
                        descricao[:100]
                    ),
                    value=str(
                        midia["id"]
                    ),
                )
            )

        super().__init__(
            placeholder=(
                "Escolha uma mídia..."
            ),
            min_values=1,
            max_values=1,
            options=opcoes,
        )

    async def callback(
        self,
        interaction,
    ):
        midia_id = int(
            self.values[0]
        )

        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                midia_id,
            )
        )

        if not midia:
            await interaction.response.edit_message(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=view_voltar_tipo(
                    self.tipo
                ),
            )

            return

        await interaction.response.edit_message(
            content=None,
            embed=criar_embed_midia(
                midia
            ),
            view=MidiaView(
                midia
            ),
        )


class ListaMidiasView(
    discord.ui.View
):
    def __init__(
        self,
        midias,
        tipo,
    ):
        super().__init__(
            timeout=300
        )

        self.tipo = tipo

        self.add_item(
            MidiaSelect(
                midias,
                tipo,
            )
        )

        voltar = discord.ui.Button(
            label="Voltar",
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        fechar = discord.ui.Button(
            label="Fechar",
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        voltar.callback = (
            self.voltar
        )

        fechar.callback = (
            self.fechar
        )

        self.add_item(
            voltar
        )

        self.add_item(
            fechar
        )

    async def voltar(
        self,
        interaction,
    ):
        await interaction.response.edit_message(
            content=(
                "O que deseja atualizar?"
            ),
            embed=None,
            view=view_voltar_tipo(
                self.tipo
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
# OPINIÃO NORMAL
# ============================================================

class OpiniaoModal(
    discord.ui.Modal
):
    def __init__(
        self,
        midia,
    ):
        super().__init__(
            title="Editar opinião"
        )

        self.midia = midia

        nota_atual = ""

        if (
            midia.get("nota")
            is not None
        ):
            nota_atual = (
                f"{midia['nota']:g}"
            )

        opiniao_atual = (
            midia.get("opiniao")
            or ""
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
                default=nota_atual,
            )
        )

        self.opiniao = (
            discord.ui.TextInput(
                label="Opinião",
                placeholder=(
                    "Escreva o que "
                    "você achou..."
                ),
                style=(
                    discord.TextStyle.paragraph
                ),
                required=True,
                max_length=1500,
                default=opiniao_atual,
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
        texto_nota = (
            str(
                self.nota.value
            )
            .strip()
            .replace(",", ".")
        )

        nota = None

        if texto_nota:
            try:
                nota = float(
                    texto_nota
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

        opiniao = str(
            self.opiniao.value
        ).strip()

        if not opiniao:
            await interaction.response.send_message(
                (
                    "A opinião não pode "
                    "ficar vazia."
                ),
                ephemeral=True,
                delete_after=4,
            )

            return

        db.salvar_opiniao(
            interaction.guild.id,
            interaction.user.id,
            self.midia["id"],
            opiniao,
            nota,
        )

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        await interaction.response.edit_message(
            content=(
                "✓ **Opinião salva.**"
            ),
            embed=criar_embed_midia(
                midia
            ),
            view=MidiaView(
                midia
            ),
        )


# ============================================================
# OPINIÃO APÓS CONCLUSÃO
# ============================================================

class OpiniaoFinalModal(
    discord.ui.Modal
):
    def __init__(
        self,
        midia_id,
        *,
        favoritado=False,
    ):
        super().__init__(
            title="Escrever opinião"
        )

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
        texto_nota = (
            str(
                self.nota.value
            )
            .strip()
            .replace(",", ".")
        )

        nota = None

        if texto_nota:
            try:
                nota = float(
                    texto_nota
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

        db.salvar_opiniao(
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

        if self.favoritado:
            await interaction.response.edit_message(
                content=(
                    "✓ Opinião salva e "
                    "**favorito mantido**."
                ),
                embed=None,
                view=None,
            )

            fechar_depois(
                interaction
            )

            return

        await interaction.response.edit_message(
            content=(
                "✓ **Opinião salva.**"
                "\n\n"
                "Deseja favoritar também?"
            ),
            embed=None,
            view=DepoisOpiniaoView(
                self.midia_id
            ),
        )


# ============================================================
# DEPOIS DA OPINIÃO
# ============================================================

class DepoisOpiniaoView(
    discord.ui.View
):
    def __init__(
        self,
        midia_id,
    ):
        super().__init__(
            timeout=300
        )

        self.midia_id = (
            midia_id
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
            db.alterar_favorito(
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
            ),
            view=None,
        )

        fechar_depois(
            interaction
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
        midia_id,
        *,
        favoritado=False,
    ):
        super().__init__(
            timeout=300
        )

        self.midia_id = (
            midia_id
        )

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
    async def escrever(
        self,
        interaction,
        button,
    ):
        await interaction.response.send_modal(
            OpiniaoFinalModal(
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
            db.alterar_favorito(
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
                    "✓ Adicionado aos favoritos."
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
                "Removido dos favoritos."
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
# ALTERAR STATUS
# ============================================================

class EscolherStatusView(
    discord.ui.View
):
    def __init__(
        self,
        midia,
    ):
        super().__init__(
            timeout=300
        )

        self.midia = midia

        quero = discord.ui.Button(
            label=nome_status(
                "quero_ver",
                midia["tipo"],
            ),
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        andamento = discord.ui.Button(
            label=nome_status(
                "em_andamento",
                midia["tipo"],
            ),
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        finalizado = discord.ui.Button(
            label=nome_status(
                "finalizado",
                midia["tipo"],
            ),
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        voltar = discord.ui.Button(
            label="Voltar",
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        fechar = discord.ui.Button(
            label="Fechar",
            style=(
                discord.ButtonStyle.secondary
            ),
        )

        quero.callback = (
            self.quero
        )

        andamento.callback = (
            self.andamento
        )

        finalizado.callback = (
            self.finalizado
        )

        voltar.callback = (
            self.voltar
        )

        fechar.callback = (
            self.fechar
        )

        self.add_item(
            quero
        )

        self.add_item(
            andamento
        )

        self.add_item(
            finalizado
        )

        self.add_item(
            voltar
        )

        self.add_item(
            fechar
        )

    async def aplicar(
        self,
        interaction,
        novo_status,
    ):
        await interaction.response.defer()

        resultado = (
            db.alterar_status(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
                novo_status,
            )
        )

        if resultado is None:
            await interaction.edit_original_response(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        if not midia:
            await interaction.edit_original_response(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        if novo_status == "finalizado":
            data = (
                formatar_data_finalizacao(
                    resultado.get(
                        "finalizado_em"
                    )
                )
            )

            status_nome = (
                nome_status(
                    "finalizado",
                    midia["tipo"],
                )
            )

            if data:
                linha = (
                    f"**{status_nome}** "
                    f"em **{data}**."
                )

            else:
                linha = (
                    f"**{status_nome}**."
                )

            await interaction.edit_original_response(
                content=(
                    f"**{midia['titulo']}**"
                    "\n\n"
                    f"{linha}"
                    "\n\n"
                    "Deseja deixar uma opinião?"
                ),
                embed=None,
                view=DepoisFinalizarView(
                    midia["id"],
                    favoritado=bool(
                        midia["favorito"]
                    ),
                ),
            )

            return

        await interaction.edit_original_response(
            content=(
                "✓ "
                f"**{midia['titulo']}** "
                "agora está como "
                f"**{nome_status(
                    novo_status,
                    midia['tipo'],
                )}**."
            ),
            embed=criar_embed_midia(
                midia
            ),
            view=MidiaView(
                midia
            ),
        )

    async def quero(
        self,
        interaction,
    ):
        await self.aplicar(
            interaction,
            "quero_ver",
        )

    async def andamento(
        self,
        interaction,
    ):
        await self.aplicar(
            interaction,
            "em_andamento",
        )

    async def finalizado(
        self,
        interaction,
    ):
        await self.aplicar(
            interaction,
            "finalizado",
        )

    async def voltar(
        self,
        interaction,
    ):
        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        if not midia:
            await interaction.response.edit_message(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        await interaction.response.edit_message(
            content=None,
            embed=criar_embed_midia(
                midia
            ),
            view=MidiaView(
                midia
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
# REMOVER
# ============================================================

class ConfirmarRemocaoView(
    discord.ui.View
):
    def __init__(
        self,
        midia,
    ):
        super().__init__(
            timeout=300
        )

        self.midia = midia

    @discord.ui.button(
        label="Confirmar",
        style=discord.ButtonStyle.secondary,
    )
    async def confirmar(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        removido = (
            db.remover_da_lista(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        if not removido:
            await interaction.edit_original_response(
                content=(
                    "Essa mídia já não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        await interaction.edit_original_response(
            content=(
                "✓ "
                f"**{self.midia['titulo']}** "
                "foi removido da sua lista."
            ),
            embed=None,
            view=DepoisRemoverView(
                self.midia["tipo"]
            ),
        )

    @discord.ui.button(
        label="Cancelar",
        style=discord.ButtonStyle.secondary,
    )
    async def cancelar(
        self,
        interaction,
        button,
    ):
        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        if not midia:
            await interaction.response.edit_message(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        await interaction.response.edit_message(
            content=None,
            embed=criar_embed_midia(
                midia
            ),
            view=MidiaView(
                midia
            ),
        )


class DepoisRemoverView(
    discord.ui.View
):
    def __init__(
        self,
        tipo,
    ):
        super().__init__(
            timeout=300
        )

        self.tipo = tipo

    @discord.ui.button(
        label="Voltar",
        style=discord.ButtonStyle.secondary,
    )
    async def voltar(
        self,
        interaction,
        button,
    ):
        await abrir_lista(
            interaction,
            self.tipo,
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
# TELA DA MÍDIA
# ============================================================

class MidiaView(
    discord.ui.View
):
    def __init__(
        self,
        midia,
    ):
        super().__init__(
            timeout=300
        )

        self.midia = midia

        if bool(
            midia["favorito"]
        ):
            self.favorito.label = (
                "Desfavoritar"
            )

        else:
            self.favorito.label = (
                "Favoritar"
            )

        if midia.get("opiniao"):
            self.editar_opiniao.label = (
                "Editar opinião"
            )

        else:
            self.editar_opiniao.label = (
                "Escrever opinião"
            )

    @discord.ui.button(
        label="Alterar status",
        style=discord.ButtonStyle.secondary,
    )
    async def alterar_status(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                f"Qual deve ser o status de "
                f"**{self.midia['titulo']}**?"
            ),
            embed=None,
            view=EscolherStatusView(
                self.midia
            ),
        )

    @discord.ui.button(
        label="Favoritar",
        style=discord.ButtonStyle.secondary,
    )
    async def favorito(
        self,
        interaction,
        button,
    ):
        await interaction.response.defer()

        resultado = (
            db.alterar_favorito(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
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
                await interaction.followup.send(
                    (
                        "Você já possui "
                        "**5 favoritos desse "
                        "tipo de mídia**."
                    ),
                    ephemeral=True,
                    delete_after=4,
                )

                return

            await interaction.followup.send(
                (
                    "Não encontrei essa "
                    "mídia na sua lista."
                ),
                ephemeral=True,
                delete_after=4,
            )

            return

        await atualizar_lista_publica(
            interaction.guild,
            interaction.user,
        )

        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        if not midia:
            await interaction.edit_original_response(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        if resultado[
            "favorito"
        ]:
            mensagem = (
                "✓ Adicionado aos favoritos."
            )

        else:
            mensagem = (
                "✓ Removido dos favoritos."
            )

        await interaction.edit_original_response(
            content=mensagem,
            embed=criar_embed_midia(
                midia
            ),
            view=MidiaView(
                midia
            ),
        )

    @discord.ui.button(
        label="Escrever opinião",
        style=discord.ButtonStyle.secondary,
    )
    async def editar_opiniao(
        self,
        interaction,
        button,
    ):
        midia = (
            db.obter_midia_usuario(
                interaction.guild.id,
                interaction.user.id,
                self.midia["id"],
            )
        )

        if not midia:
            await interaction.response.edit_message(
                content=(
                    "Essa mídia não está "
                    "mais na sua lista."
                ),
                embed=None,
                view=FecharView(),
            )

            return

        await interaction.response.send_modal(
            OpiniaoModal(
                midia
            )
        )

    @discord.ui.button(
        label="Remover da lista",
        style=discord.ButtonStyle.secondary,
    )
    async def remover(
        self,
        interaction,
        button,
    ):
        await interaction.response.edit_message(
            content=(
                f"Remover "
                f"**{self.midia['titulo']}** "
                "da sua lista?"
            ),
            embed=None,
            view=ConfirmarRemocaoView(
                self.midia
            ),
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
        await abrir_lista(
            interaction,
            self.midia["tipo"],
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
# ABRIR LISTA
# ============================================================

async def abrir_lista(
    interaction,
    tipo,
):
    midias = [
        midia
        for midia
        in db.listar_midias_usuario(
            interaction.guild.id,
            interaction.user.id,
        )
        if midia["tipo"] == tipo
    ]

    if not midias:
        await interaction.response.edit_message(
            content=(
                f"Você não possui "
                f"**{nome_plural(tipo)}** "
                "na sua lista."
            ),
            embed=None,
            view=view_voltar_tipo(
                tipo
            ),
        )

        return

    await interaction.response.edit_message(
        content=(
            f"Escolha "
            f"{artigo_tipo(tipo)} "
            f"**{nome_tipo(tipo).lower()}** "
            "da sua lista:"
        ),
        embed=None,
        view=ListaMidiasView(
            midias,
            tipo,
        ),
    )


# ============================================================
# FILME / SÉRIE
# ============================================================

class TipoFilmeSerieView(
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
        await abrir_lista(
            interaction,
            "movie",
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
        await abrir_lista(
            interaction,
            "tv",
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
                "𐙚 O que deseja atualizar?"
            ),
            embed=None,
            view=CategoriaAtualizarView(),
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

class TipoAnimeMangaView(
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
        await abrir_lista(
            interaction,
            "anime",
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
        await abrir_lista(
            interaction,
            "manga",
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
                "𐙚 O que deseja atualizar?"
            ),
            embed=None,
            view=CategoriaAtualizarView(),
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

class TipoMusicaView(
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
        await abrir_lista(
            interaction,
            "music",
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
        await abrir_lista(
            interaction,
            "album",
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
        await abrir_lista(
            interaction,
            "artist",
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
                "𐙚 O que deseja atualizar?"
            ),
            embed=None,
            view=CategoriaAtualizarView(),
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
# VOLTAR PARA O SUBMENU CERTO
# ============================================================

def view_voltar_tipo(
    tipo,
):
    if tipo in (
        "movie",
        "tv",
    ):
        return (
            TipoFilmeSerieView()
        )

    if tipo in (
        "anime",
        "manga",
    ):
        return (
            TipoAnimeMangaView()
        )

    if tipo in (
        "music",
        "album",
        "artist",
    ):
        return (
            TipoMusicaView()
        )

    return (
        CategoriaAtualizarView()
    )


# ============================================================
# MENU PRINCIPAL
# ============================================================

class CategoriaAtualizarView(
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
        await abrir_lista(
            interaction,
            "game",
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
                "O que deseja atualizar?"
            ),
            embed=None,
            view=TipoFilmeSerieView(),
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
                "O que deseja atualizar?"
            ),
            embed=None,
            view=TipoAnimeMangaView(),
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
                "O que deseja atualizar?"
            ),
            embed=None,
            view=TipoMusicaView(),
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
# /ATUALIZAR
# ============================================================

def registrar_atualizar(
    bot,
):
    @bot.tree.command(
        name="atualizar",
        description=(
            "Atualize sua coleção "
            "de mídias."
        ),
    )
    async def atualizar(
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
            "𐙚 O que deseja atualizar?",
            view=CategoriaAtualizarView(),
            ephemeral=True,
        )