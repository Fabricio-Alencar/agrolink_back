import time
import traceback
from uuid import uuid4

from sqlalchemy import select
from database import SessionLocal
from models.produto import Produto
from models.usuario import Usuario

from services.azure_storage_service import (
    upload_arquivo,
    deletar_arquivo,
    CONTAINER_PRODUTOS
)

from services.cache_service import redis_client


# ==========================================================
# LISTAR PRODUTOS
# ==========================================================
def listar_produtos_produtor(user_id):

    inicio = time.perf_counter()

    print("\n========================================")
    print("🔵 LISTAR PRODUTOS DO PRODUTOR")
    print("👤 User ID:", user_id)
    print("========================================")

    db = SessionLocal()

    try:

        inicio_consulta = time.perf_counter()

        print("📡 Executando consulta no banco...")

        resultado = db.execute(
            select(Produto).where(
                Produto.produtor_id == user_id
            )
        )

        produtos = resultado.scalars().all()

        fim_consulta = time.perf_counter()

        print(
            f"⏱️ Tempo da consulta ao banco: "
            f"{(fim_consulta - inicio_consulta) * 1000:.2f} ms"
        )

        print("📦 Produtos encontrados:", len(produtos))

        return produtos

    except Exception as e:

        print("\n❌ ERRO AO LISTAR PRODUTOS")
        print("Tipo:", type(e).__name__)
        print("Mensagem:", str(e))
        print("TRACEBACK:")
        traceback.print_exc()

        raise

    finally:

        db.close()

        fim = time.perf_counter()

        print(
            f"⏱️ Tempo total do listar_produtos_produtor: "
            f"{(fim - inicio) * 1000:.2f} ms"
        )


# ==========================================================
# CRIAR PRODUTO
# ==========================================================
def criar_produto(data, arquivo_foto):

    print("\n========================================")
    print("🟢 CRIAR PRODUTO")
    print("========================================")

    print("📦 DATA RECEBIDA:")
    print(data)

    if arquivo_foto:
        print("📷 ARQUIVO:")
        print("   Nome:", arquivo_foto.filename)
        print("   Tipo:", arquivo_foto.content_type)
    else:
        print("📷 Nenhuma foto enviada")

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR USUÁRIO
        # ==========================================

        print("\n🔎 Buscando usuário...")
        print("👤 Produtor ID:", data['produtor_id'])

        usuario = db.get(
            Usuario,
            data['produtor_id']
        )

        if not usuario:
            print("❌ Usuário não encontrado")
            raise Exception("Usuário não encontrado")

        print("✅ Usuário encontrado")
        print("👤 Nome:", usuario.nome)
        print("👤 Tipo:", usuario.tipo)

        if usuario.tipo != 'produtor':
            print("❌ Usuário não é produtor")
            raise Exception(
                "Apenas produtores podem criar produtos"
            )

        # ==========================================
        # UPLOAD DA FOTO
        # ==========================================

        nome_blob = None

        if arquivo_foto:

            print("\n📷 Iniciando upload da foto...")

            extensao = ""

            if (
                arquivo_foto.filename
                and "." in arquivo_foto.filename
            ):
                extensao = "." + arquivo_foto.filename.rsplit(
                    ".",
                    1
                )[1].lower()

            nome_blob = f"{uuid4().hex}{extensao}"

            print("📁 Nome do Blob:", nome_blob)
            print("☁️ Container:", CONTAINER_PRODUTOS)

            try:

                upload_arquivo(
                    arquivo_foto.file,
                    nome_blob,
                    CONTAINER_PRODUTOS
                )

                print("✅ Upload da foto concluído")

            except Exception as e:

                print("\n❌ ERRO NO UPLOAD DA FOTO")
                print("Tipo:", type(e).__name__)
                print("Mensagem:", str(e))
                traceback.print_exc()

                raise

        else:

            print("📷 Nenhuma foto para fazer upload")

        # ==========================================
        # FOTO SALVA NO BANCO
        # ==========================================

        caminho_foto_banco = (
            nome_blob
            if nome_blob
            else "foto_generica.png"
        )

        print("📸 Foto que será salva no banco:")
        print(caminho_foto_banco)

        # ==========================================
        # CRIAR OBJETO PRODUTO
        # ==========================================

        try:

            print("\n📝 Criando objeto Produto...")

            produto = Produto(
                nome=data.get('nome'),
                preco=data.get('preco'),
                produtor_id=data.get('produtor_id'),
                quantidade=data.get('quantidade'),
                status=data.get('status'),
                categoria=data.get('categoria'),
                unidade=data.get('unidade'),
                descricao=data.get('descricao'),
                foto=caminho_foto_banco
            )

            print("✅ Objeto Produto criado")
            print("📦 Produto:", produto)

            db.add(produto)

            print("✅ Produto adicionado à sessão do banco")

            # ==========================================
            # COMMIT
            # ==========================================

            print("\n💾 Executando db.commit()...")

            inicio_commit = time.perf_counter()

            db.commit()

            fim_commit = time.perf_counter()

            print(
                f"✅ COMMIT REALIZADO COM SUCESSO "
                f"({(fim_commit - inicio_commit) * 1000:.2f} ms)"
            )

            # ==========================================
            # REFRESH
            # ==========================================

            print("🔄 Executando db.refresh()...")

            db.refresh(produto)

            print("✅ Refresh realizado")
            print("🆔 ID gerado:", produto.id)

            # ==========================================
            # REDIS
            # ==========================================

            print("\n🧹 Limpando cache Redis...")
            print("🔑 Chave: marketplace")

            try:

                resultado_redis = redis_client.delete(
                    "marketplace"
                )

                print(
                    "✅ Redis executado com sucesso"
                )

                print(
                    "📦 Resultado Redis:",
                    resultado_redis
                )

            except Exception as e:

                print("\n❌ ERRO NO REDIS")
                print("Tipo:", type(e).__name__)
                print("Mensagem:", str(e))
                traceback.print_exc()

                # NÃO interrompe o cadastro
                # porque o banco já foi atualizado

            print("\n========================================")
            print(
                f"✅ SUCESSO: Produto {produto.id} cadastrado."
            )
            print("========================================")

            return produto

        except Exception as e:

            db.rollback()

            print("\n========================================")
            print("❌ ERRO NO BANCO DE DADOS")
            print("========================================")

            print("Tipo:", type(e).__name__)
            print("Mensagem:", str(e))

            print("\n📋 TRACEBACK COMPLETO:")
            traceback.print_exc()

            # ==========================================
            # REMOVER BLOB SE O BANCO FALHOU
            # ==========================================

            if nome_blob:

                print("\n🧹 Tentando remover Blob após erro...")

                try:

                    deletar_arquivo(
                        nome_blob,
                        CONTAINER_PRODUTOS
                    )

                    print("✅ Blob removido")

                except Exception as erro_blob:

                    print(
                        "❌ Não foi possível remover o Blob:"
                    )

                    print(
                        str(erro_blob)
                    )

            raise Exception(
                f"Erro ao salvar no banco: {str(e)}"
            )

    except Exception as e:

        print("\n========================================")
        print("❌ ERRO GERAL AO CRIAR PRODUTO")
        print("========================================")

        print("Tipo:", type(e).__name__)
        print("Mensagem:", str(e))

        traceback.print_exc()

        raise

    finally:

        db.close()

        print("🔒 Conexão com banco fechada")


# ==========================================================
# EXCLUIR PRODUTO
# ==========================================================
def deletar_produto(produto_id, user_id):

    print("\n========================================")
    print("🔴 EXCLUIR PRODUTO")
    print("========================================")

    print("🆔 Produto ID:", produto_id)
    print("👤 User ID:", user_id)

    db = SessionLocal()

    try:

        print("\n🔎 Buscando produto...")

        produto = db.get(
            Produto,
            produto_id
        )

        if produto:

            print("✅ Produto encontrado")
            print("📦 Nome:", produto.nome)
            print("👤 Dono:", produto.produtor_id)
            print("📷 Foto:", produto.foto)

        else:

            print("❌ Produto NÃO encontrado")

            raise Exception(
                "Produto não encontrado"
            )

        # ==========================================
        # VERIFICAR DONO
        # ==========================================

        print("\n🔐 Verificando proprietário...")

        if produto.produtor_id != user_id:

            print("❌ Usuário não é dono do produto")

            raise Exception(
                "Você não tem permissão para excluir este produto"
            )

        print("✅ Usuário é o proprietário")

        # ==========================================
        # REMOVER FOTO
        # ==========================================

        foto_produto = produto.foto

        if (
            foto_produto
            and foto_produto != "foto_generica.png"
            and not foto_produto.startswith(
                ("http://", "https://")
            )
        ):

            print("\n☁️ Removendo foto do Azure...")
            print("📷 Arquivo:", foto_produto)

            try:

                deletar_arquivo(
                    foto_produto,
                    CONTAINER_PRODUTOS
                )

                print("✅ Foto removida do Azure")

            except Exception as e:

                print(
                    "⚠️ Não foi possível excluir "
                    "a foto do produto:"
                )

                print(str(e))

                traceback.print_exc()

        # ==========================================
        # EXCLUIR DO BANCO
        # ==========================================

        try:

            print("\n🗑️ Excluindo produto do banco...")

            db.delete(produto)

            print("✅ Produto marcado para exclusão")

            db.commit()

            print("✅ COMMIT realizado")

            # ==========================================
            # REDIS
            # ==========================================

            print("\n🧹 Limpando cache Redis...")

            try:

                resultado_redis = redis_client.delete(
                    "marketplace"
                )

                print(
                    "✅ Redis executado:",
                    resultado_redis
                )

            except Exception as e:

                print("⚠️ Erro no Redis:")
                print(str(e))
                traceback.print_exc()

            print(
                f"✅ SUCESSO: Produto {produto_id} deletado."
            )

            return True

        except Exception as e:

            db.rollback()

            print("\n❌ ERRO AO DELETAR NO BANCO")
            print("Tipo:", type(e).__name__)
            print("Mensagem:", str(e))

            traceback.print_exc()

            raise Exception(
                "Erro ao excluir no banco de dados"
            )

    finally:

        db.close()

        print("🔒 Conexão com banco fechada")


# ==========================================================
# ATUALIZAR PRODUTO
# ==========================================================
def atualizar_produto(
    produto_id,
    user_id,
    data,
    arquivo_foto
):

    print("\n========================================")
    print("🟡 ATUALIZAR PRODUTO")
    print("========================================")

    print("🆔 Produto ID:", produto_id)
    print("👤 User ID:", user_id)
    print("📦 Data:", data)

    db = SessionLocal()

    try:

        # ==========================================
        # BUSCAR PRODUTO
        # ==========================================

        print("\n🔎 Buscando produto...")

        produto = db.get(
            Produto,
            produto_id
        )

        if not produto:

            print("❌ Produto não encontrado")

            raise Exception(
                "Produto não encontrado"
            )

        print("✅ Produto encontrado")
        print("📦 Nome atual:", produto.nome)
        print("📷 Foto atual:", produto.foto)
        print("👤 Dono:", produto.produtor_id)

        # ==========================================
        # VERIFICAR DONO
        # ==========================================

        print("\n🔐 Verificando proprietário...")

        if produto.produtor_id != user_id:

            print("❌ Usuário não é proprietário")

            raise Exception(
                "Você não tem permissão para editar este produto"
            )

        print("✅ Usuário é proprietário")

        # ==========================================
        # ATUALIZAR CAMPOS
        # ==========================================

        foto_antiga = produto.foto

        print("\n📝 Atualizando campos...")

        produto.nome = data.get(
            'nome',
            produto.nome
        )

        produto.preco = data.get(
            'preco',
            produto.preco
        )

        produto.quantidade = data.get(
            'quantidade',
            produto.quantidade
        )

        produto.unidade = data.get(
            'unidade',
            produto.unidade
        )

        produto.categoria = data.get(
            'categoria',
            produto.categoria
        )

        produto.descricao = data.get(
            'descricao',
            produto.descricao
        )

        produto.status = data.get(
            'status',
            produto.status
        )

        print("✅ Campos atualizados em memória")

        print("📦 Novo nome:", produto.nome)
        print("💰 Novo preço:", produto.preco)
        print("📦 Nova quantidade:", produto.quantidade)
        print("📏 Nova unidade:", produto.unidade)
        print("🏷️ Nova categoria:", produto.categoria)
        print("📝 Nova descrição:", produto.descricao)
        print("📌 Novo status:", produto.status)

        # ==========================================
        # NOVA FOTO
        # ==========================================

        novo_nome_blob = None

        if arquivo_foto:

            print("\n📷 Nova foto recebida")

            extensao = ""

            if (
                arquivo_foto.filename
                and "." in arquivo_foto.filename
            ):

                extensao = "." + arquivo_foto.filename.rsplit(
                    ".",
                    1
                )[1].lower()

            novo_nome_blob = (
                f"{uuid4().hex}{extensao}"
            )

            print(
                "📁 Novo nome Blob:",
                novo_nome_blob
            )

            print(
                "☁️ Container:",
                CONTAINER_PRODUTOS
            )

            # ==========================================
            # UPLOAD
            # ==========================================

            try:

                print("☁️ Fazendo upload da nova foto...")

                upload_arquivo(
                    arquivo_foto.file,
                    novo_nome_blob,
                    CONTAINER_PRODUTOS
                )

                print("✅ Upload concluído")

                produto.foto = novo_nome_blob

                print(
                    "📷 Nova foto definida:",
                    produto.foto
                )

            except Exception as e:

                print("\n❌ ERRO NO UPLOAD DA NOVA FOTO")
                print("Tipo:", type(e).__name__)
                print("Mensagem:", str(e))

                traceback.print_exc()

                raise

            # ==========================================
            # REMOVER FOTO ANTIGA
            # ==========================================

            if (
                foto_antiga
                and foto_antiga != "foto_generica.png"
                and not foto_antiga.startswith(
                    ("http://", "https://")
                )
            ):

                print(
                    "\n🧹 Removendo foto antiga..."
                )

                try:

                    deletar_arquivo(
                        foto_antiga,
                        CONTAINER_PRODUTOS
                    )

                    print(
                        "✅ Foto antiga removida"
                    )

                except Exception as e:

                    print(
                        "⚠️ Não foi possível excluir "
                        "a foto antiga:"
                    )

                    print(str(e))

                    traceback.print_exc()

        else:

            print(
                "\n📷 Nenhuma nova foto enviada"
            )

        # ==========================================
        # COMMIT
        # ==========================================

        try:

            print("\n💾 Executando db.commit()...")

            inicio_commit = time.perf_counter()

            db.commit()

            fim_commit = time.perf_counter()

            print(
                f"✅ COMMIT realizado com sucesso "
                f"({(fim_commit - inicio_commit) * 1000:.2f} ms)"
            )

            # ==========================================
            # REFRESH
            # ==========================================

            print("🔄 Executando db.refresh()...")

            db.refresh(produto)

            print("✅ Refresh realizado")

            print("📦 Produto após atualização:")
            print("ID:", produto.id)
            print("Nome:", produto.nome)
            print("Preço:", produto.preco)
            print("Quantidade:", produto.quantidade)
            print("Unidade:", produto.unidade)
            print("Categoria:", produto.categoria)
            print("Status:", produto.status)
            print("Foto:", produto.foto)

            # ==========================================
            # REDIS
            # ==========================================

            print("\n🧹 Limpando cache Redis...")

            try:

                resultado_redis = redis_client.delete(
                    "marketplace"
                )

                print(
                    "✅ Redis executado com sucesso"
                )

                print(
                    "📦 Resultado Redis:",
                    resultado_redis
                )

            except Exception as e:

                print("\n⚠️ ERRO NO REDIS")
                print("Tipo:", type(e).__name__)
                print("Mensagem:", str(e))

                traceback.print_exc()

                # O banco já foi atualizado.
                # O erro do Redis não deve desfazer a alteração.

            print("\n========================================")
            print(
                f"✅ SUCESSO: Produto {produto_id} atualizado."
            )
            print("========================================")

            return produto

        except Exception as e:

            db.rollback()

            print("\n========================================")
            print("❌ ERRO AO ATUALIZAR BANCO")
            print("========================================")

            print("Tipo:", type(e).__name__)
            print("Mensagem:", str(e))

            print("\n📋 TRACEBACK COMPLETO:")
            traceback.print_exc()

            # ==========================================
            # REMOVER NOVO BLOB
            # ==========================================

            if (
                arquivo_foto
                and novo_nome_blob
            ):

                print(
                    "\n🧹 Tentando remover "
                    "novo Blob após erro..."
                )

                try:

                    deletar_arquivo(
                        novo_nome_blob,
                        CONTAINER_PRODUTOS
                    )

                    print(
                        "✅ Novo Blob removido"
                    )

                except Exception as erro_blob:

                    print(
                        "❌ Não foi possível remover "
                        "o novo Blob:"
                    )

                    print(
                        str(erro_blob)
                    )

            raise Exception(
                f"Erro ao atualizar banco: {str(e)}"
            )

    except Exception as e:

        print("\n========================================")
        print("❌ ERRO GERAL AO ATUALIZAR PRODUTO")
        print("========================================")

        print("Tipo:", type(e).__name__)
        print("Mensagem:", str(e))

        traceback.print_exc()

        raise

    finally:

        db.close()

        print("🔒 Conexão com banco fechada")