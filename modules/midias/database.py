import sqlite3
from datetime import datetime


class MidiasDatabase:
    def __init__(self, caminho_db):
        self.caminho_db = caminho_db
        self.criar_tabelas()

    def conectar(self):
        conexao = sqlite3.connect(
            self.caminho_db
        )

        conexao.row_factory = sqlite3.Row

        return conexao

    # ========================================================
    # TABELAS
    # ========================================================

    def criar_tabelas(self):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS midias (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    provider TEXT NOT NULL,
                    external_id TEXT NOT NULL,
                    tipo TEXT NOT NULL,

                    titulo TEXT NOT NULL,
                    ano TEXT,
                    sinopse TEXT,
                    capa TEXT,

                    UNIQUE(
                        provider,
                        external_id,
                        tipo
                    )
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS midias_usuarios (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,

                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,
                    midia_id INTEGER NOT NULL,

                    status TEXT NOT NULL,
                    favorito INTEGER NOT NULL DEFAULT 0,

                    nota REAL,
                    opiniao TEXT,
                    finalizado_em TEXT,
                    opiniao_atualizada_em TEXT,

                    FOREIGN KEY (midia_id)
                        REFERENCES midias(id),

                    UNIQUE(
                        guild_id,
                        user_id,
                        midia_id
                    )
                )
                """
            )

            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS midias_listas (
                    guild_id INTEGER NOT NULL,
                    user_id INTEGER NOT NULL,

                    channel_id INTEGER NOT NULL,
                    message_id INTEGER NOT NULL,

                    categoria TEXT NOT NULL
                        DEFAULT 'filmes_series',

                    PRIMARY KEY (
                        guild_id,
                        user_id
                    )
                )
                """
            )

            conexao.commit()

    # ========================================================
    # MÍDIA
    # ========================================================

    def obter_ou_criar_midia(
        self,
        resultado,
    ):
        provider = resultado.get(
            "provider",
            "tmdb",
        )

        external_id = str(
            resultado["id"]
        )

        tipo = resultado["tipo"]

        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT id
                FROM midias
                WHERE provider = ?
                  AND external_id = ?
                  AND tipo = ?
                """,
                (
                    provider,
                    external_id,
                    tipo,
                ),
            )

            registro = cursor.fetchone()

            if registro:
                return registro["id"]

            cursor.execute(
                """
                INSERT INTO midias (
                    provider,
                    external_id,
                    tipo,
                    titulo,
                    ano,
                    sinopse,
                    capa
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    provider,
                    external_id,
                    tipo,
                    resultado["titulo"],
                    resultado["ano"],
                    resultado["sinopse"],
                    resultado["capa"],
                ),
            )

            conexao.commit()

            return cursor.lastrowid

    def obter_midia_usuario(
        self,
        guild_id,
        user_id,
        midia_id,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    m.id,
                    m.provider,
                    m.external_id,
                    m.tipo,
                    m.titulo,
                    m.ano,
                    m.sinopse,
                    m.capa,

                    mu.status,
                    mu.favorito,
                    mu.nota,
                    mu.opiniao,
                    mu.finalizado_em,
                    mu.opiniao_atualizada_em

                FROM midias_usuarios AS mu

                INNER JOIN midias AS m
                    ON m.id = mu.midia_id

                WHERE mu.guild_id = ?
                  AND mu.user_id = ?
                  AND mu.midia_id = ?
                """,
                (
                    guild_id,
                    user_id,
                    midia_id,
                ),
            )

            registro = cursor.fetchone()

        if not registro:
            return None

        return dict(registro)

    # ========================================================
    # ESTADO PESSOAL
    # ========================================================

    def obter_estado(
        self,
        guild_id,
        user_id,
        midia_id,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    status,
                    favorito,
                    nota,
                    opiniao,
                    finalizado_em
                FROM midias_usuarios
                WHERE guild_id = ?
                  AND user_id = ?
                  AND midia_id = ?
                """,
                (
                    guild_id,
                    user_id,
                    midia_id,
                ),
            )

            registro = cursor.fetchone()

        if not registro:
            return None

        return {
            "status": registro["status"],
            "favorito": bool(
                registro["favorito"]
            ),
            "nota": registro["nota"],
            "opiniao": registro["opiniao"],
            "finalizado_em": registro[
                "finalizado_em"
            ],
        }

    # ========================================================
    # ADICIONAR À LISTA
    # ========================================================

    def adicionar_quero_ver(
        self,
        guild_id,
        user_id,
        resultado,
    ):
        midia_id = self.obter_ou_criar_midia(
            resultado
        )

        estado = self.obter_estado(
            guild_id,
            user_id,
            midia_id,
        )

        if estado is not None:
            return {
                "criado": False,
                "midia_id": midia_id,
                "estado": estado,
            }

        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO midias_usuarios (
                    guild_id,
                    user_id,
                    midia_id,
                    status
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    guild_id,
                    user_id,
                    midia_id,
                    "quero_ver",
                ),
            )

            conexao.commit()

        return {
            "criado": True,
            "midia_id": midia_id,
            "estado": {
                "status": "quero_ver",
                "favorito": False,
                "nota": None,
                "opiniao": None,
                "finalizado_em": None,
            },
        }

    # ========================================================
    # FINALIZAR
    # ========================================================

    def finalizar(
        self,
        guild_id,
        user_id,
        resultado,
    ):
        midia_id = self.obter_ou_criar_midia(
            resultado
        )

        estado = self.obter_estado(
            guild_id,
            user_id,
            midia_id,
        )

        if (
            estado is not None
            and estado["status"] == "finalizado"
        ):
            return {
                "alterado": False,
                "midia_id": midia_id,
                "finalizado_em": estado[
                    "finalizado_em"
                ],
            }

        agora = datetime.now()

        finalizado_em = agora.isoformat(
            timespec="seconds"
        )

        with self.conectar() as conexao:
            cursor = conexao.cursor()

            if estado is None:
                cursor.execute(
                    """
                    INSERT INTO midias_usuarios (
                        guild_id,
                        user_id,
                        midia_id,
                        status,
                        finalizado_em
                    )
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        guild_id,
                        user_id,
                        midia_id,
                        "finalizado",
                        finalizado_em,
                    ),
                )

            else:
                cursor.execute(
                    """
                    UPDATE midias_usuarios
                    SET
                        status = ?,
                        finalizado_em = ?
                    WHERE guild_id = ?
                      AND user_id = ?
                      AND midia_id = ?
                    """,
                    (
                        "finalizado",
                        finalizado_em,
                        guild_id,
                        user_id,
                        midia_id,
                    ),
                )

            conexao.commit()

        return {
            "alterado": True,
            "midia_id": midia_id,
            "finalizado_em": finalizado_em,
        }

    # ========================================================
    # ALTERAR STATUS
    # ========================================================

    def alterar_status(
        self,
        guild_id,
        user_id,
        midia_id,
        novo_status,
    ):
        if novo_status not in (
            "quero_ver",
            "em_andamento",
            "finalizado",
        ):
            raise ValueError(
                "Status inválido."
            )

        midia = self.obter_midia_usuario(
            guild_id,
            user_id,
            midia_id,
        )

        if not midia:
            return None

        if novo_status in (
            "quero_ver",
            "em_andamento",
        ):
            with self.conectar() as conexao:
                cursor = conexao.cursor()

                cursor.execute(
                    """
                    UPDATE midias_usuarios
                    SET
                        status = ?,
                        finalizado_em = NULL
                    WHERE guild_id = ?
                      AND user_id = ?
                      AND midia_id = ?
                    """,
                    (
                        novo_status,
                        guild_id,
                        user_id,
                        midia_id,
                    ),
                )

                conexao.commit()

            return {
                "status": novo_status,
                "finalizado_em": None,
            }

        finalizado_em = datetime.now().isoformat(
            timespec="seconds"
        )

        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                UPDATE midias_usuarios
                SET
                    status = ?,
                    finalizado_em = ?
                WHERE guild_id = ?
                  AND user_id = ?
                  AND midia_id = ?
                """,
                (
                    "finalizado",
                    finalizado_em,
                    guild_id,
                    user_id,
                    midia_id,
                ),
            )

            conexao.commit()

        return {
            "status": "finalizado",
            "finalizado_em": finalizado_em,
        }

    # ========================================================
    # FAVORITOS
    # ========================================================

    def contar_favoritos(
        self,
        guild_id,
        user_id,
        tipo,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT COUNT(*) AS quantidade

                FROM midias_usuarios AS mu

                INNER JOIN midias AS m
                    ON m.id = mu.midia_id

                WHERE mu.guild_id = ?
                  AND mu.user_id = ?
                  AND m.tipo = ?
                  AND mu.favorito = 1
                """,
                (
                    guild_id,
                    user_id,
                    tipo,
                ),
            )

            registro = cursor.fetchone()

        return registro["quantidade"]

    def alterar_favorito(
        self,
        guild_id,
        user_id,
        midia_id,
    ):
        midia = self.obter_midia_usuario(
            guild_id,
            user_id,
            midia_id,
        )

        if not midia:
            return {
                "sucesso": False,
                "motivo": "nao_encontrado",
            }

        if bool(midia["favorito"]):
            with self.conectar() as conexao:
                cursor = conexao.cursor()

                cursor.execute(
                    """
                    UPDATE midias_usuarios
                    SET favorito = 0
                    WHERE guild_id = ?
                      AND user_id = ?
                      AND midia_id = ?
                    """,
                    (
                        guild_id,
                        user_id,
                        midia_id,
                    ),
                )

                conexao.commit()

            return {
                "sucesso": True,
                "favorito": False,
            }

        quantidade = self.contar_favoritos(
            guild_id,
            user_id,
            midia["tipo"],
        )

        if quantidade >= 5:
            return {
                "sucesso": False,
                "motivo": "limite",
                "limite": 5,
            }

        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                UPDATE midias_usuarios
                SET favorito = 1
                WHERE guild_id = ?
                  AND user_id = ?
                  AND midia_id = ?
                """,
                (
                    guild_id,
                    user_id,
                    midia_id,
                ),
            )

            conexao.commit()

        return {
            "sucesso": True,
            "favorito": True,
        }

    # ========================================================
    # OPINIÃO
    # ========================================================

    def salvar_opiniao(
        self,
        guild_id,
        user_id,
        midia_id,
        opiniao,
        nota=None,
    ):
        agora = datetime.now().isoformat(
            timespec="seconds"
        )

        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                UPDATE midias_usuarios
                SET
                    nota = ?,
                    opiniao = ?,
                    opiniao_atualizada_em = ?
                WHERE guild_id = ?
                  AND user_id = ?
                  AND midia_id = ?
                """,
                (
                    nota,
                    opiniao,
                    agora,
                    guild_id,
                    user_id,
                    midia_id,
                ),
            )

            conexao.commit()

    # ========================================================
    # REMOVER DA LISTA
    # ========================================================

    def remover_da_lista(
        self,
        guild_id,
        user_id,
        midia_id,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                DELETE FROM midias_usuarios
                WHERE guild_id = ?
                  AND user_id = ?
                  AND midia_id = ?
                """,
                (
                    guild_id,
                    user_id,
                    midia_id,
                ),
            )

            alterados = cursor.rowcount

            conexao.commit()

        return alterados > 0

    # ========================================================
    # LISTAR MÍDIAS DO USUÁRIO
    # ========================================================

    def listar_midias_usuario(
        self,
        guild_id,
        user_id,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    m.id,
                    m.provider,
                    m.external_id,
                    m.tipo,
                    m.titulo,
                    m.ano,
                    m.sinopse,
                    m.capa,

                    mu.status,
                    mu.favorito,
                    mu.nota,
                    mu.opiniao,
                    mu.finalizado_em

                FROM midias_usuarios AS mu

                INNER JOIN midias AS m
                    ON m.id = mu.midia_id

                WHERE mu.guild_id = ?
                  AND mu.user_id = ?

                ORDER BY
                    m.titulo COLLATE NOCASE
                """,
                (
                    guild_id,
                    user_id,
                ),
            )

            registros = cursor.fetchall()

        return [
            dict(registro)
            for registro in registros
        ]

    # ========================================================
    # OPINIÕES
    # ========================================================

    def listar_opinioes(
        self,
        guild_id,
        user_id,
        tipo,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    m.id,
                    m.tipo,
                    m.titulo,
                    m.ano,
                    m.capa,

                    mu.nota,
                    mu.opiniao,
                    mu.finalizado_em

                FROM midias_usuarios AS mu

                INNER JOIN midias AS m
                    ON m.id = mu.midia_id

                WHERE mu.guild_id = ?
                  AND mu.user_id = ?
                  AND m.tipo = ?
                  AND mu.opiniao IS NOT NULL
                  AND TRIM(mu.opiniao) != ''

                ORDER BY
                    m.titulo COLLATE NOCASE
                """,
                (
                    guild_id,
                    user_id,
                    tipo,
                ),
            )

            registros = cursor.fetchall()

        return [
            dict(registro)
            for registro in registros
        ]

    # ========================================================
    # LISTA PÚBLICA
    # ========================================================

    def obter_lista_publica(
        self,
        guild_id,
        user_id,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                SELECT
                    channel_id,
                    message_id,
                    categoria
                FROM midias_listas
                WHERE guild_id = ?
                  AND user_id = ?
                """,
                (
                    guild_id,
                    user_id,
                ),
            )

            registro = cursor.fetchone()

        if not registro:
            return None

        return dict(registro)

    def salvar_lista_publica(
        self,
        guild_id,
        user_id,
        channel_id,
        message_id,
        categoria="filmes_series",
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                INSERT INTO midias_listas (
                    guild_id,
                    user_id,
                    channel_id,
                    message_id,
                    categoria
                )
                VALUES (?, ?, ?, ?, ?)

                ON CONFLICT(
                    guild_id,
                    user_id
                )
                DO UPDATE SET
                    channel_id = excluded.channel_id,
                    message_id = excluded.message_id,
                    categoria = excluded.categoria
                """,
                (
                    guild_id,
                    user_id,
                    channel_id,
                    message_id,
                    categoria,
                ),
            )

            conexao.commit()

    def atualizar_categoria_lista(
        self,
        guild_id,
        user_id,
        categoria,
    ):
        with self.conectar() as conexao:
            cursor = conexao.cursor()

            cursor.execute(
                """
                UPDATE midias_listas
                SET categoria = ?
                WHERE guild_id = ?
                  AND user_id = ?
                """,
                (
                    categoria,
                    guild_id,
                    user_id,
                ),
            )

            conexao.commit()


# ============================================================
# DATA
# ============================================================

def formatar_data_finalizacao(
    data_iso,
):
    if not data_iso:
        return None

    data = datetime.fromisoformat(
        data_iso
    )

    return data.strftime(
        "%d/%m/%Y"
    )