"""
Finanças Smart - Aplicativo de Gestão Financeira com Flet
Versão 2.1 - Sistema de Login Dinâmico e Persistente
"""

import flet as ft
import asyncio
from datetime import datetime
import json
import os
from relatorios import TelaRelatorios

# Configuração de caminho de dados
if os.getenv("FLET_PLATFORM") == "android":
    ARQUIVO_DADOS = os.path.join(os.getcwd(), "financas_smart_dados.json")
else:
    ARQUIVO_DADOS = "financas_smart_dados.json"


class FinancasData:
    """Gerencia persistência e lógica de dados financeiros."""
    
    def __init__(self):
        self.dados = self.carregar()

    def carregar(self):
        """Carrega dados do arquivo JSON ou retorna estrutura padrão."""
        if os.path.exists(ARQUIVO_DADOS):
            try:
                with open(ARQUIVO_DADOS, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    if self._validar_estrutura(dados):
                        return dados
            except (json.JSONDecodeError, IOError) as e:
                print(f"Erro ao carregar dados: {e}")
        
        return self._estrutura_padrao()

    @staticmethod
    def _estrutura_padrao():
        """Retorna a estrutura padrão de dados."""
        return {
            "saldo": 0.0,
            "receitas": 0.0,
            "despesas": 0.0,
            "historico": [],
            "categorias": [
                "Alimentação", "Transporte", "Lazer", "Saúde",
                "Educação", "Salário", "Outros"
            ]
        }

    @staticmethod
    def _validar_estrutura(dados):
        """Valida se os dados possuem a estrutura esperada."""
        chaves_obrigatorias = {"saldo", "receitas", "despesas", "historico", "categorias"}
        return isinstance(dados, dict) and chaves_obrigatorias.issubset(dados.keys())

    def salvar(self):
        """Salva dados no arquivo JSON."""
        try:
            with open(ARQUIVO_DADOS, "w", encoding="utf-8") as f:
                json.dump(self.dados, f, ensure_ascii=False, indent=4)
        except IOError as e:
            print(f"Erro ao salvar dados: {e}")

    def adicionar_movimento(self, valor, descricao, categoria, tipo):
        """Adiciona uma transação (receita ou despesa)."""
        if valor <= 0:
            raise ValueError("Valor deve ser positivo")
        
        data_formatada = datetime.now().strftime("%d/%m/%Y %H:%M")
        novo_item = {
            "tipo": tipo,
            "valor": valor,
            "desc": descricao or "Sem descrição",
            "categoria": categoria,
            "data": data_formatada
        }

        if tipo == "in":
            self.dados['saldo'] += valor
            self.dados['receitas'] += valor
        elif tipo == "out":
            self.dados['saldo'] -= valor
            self.dados['despesas'] += valor
        
        self.dados['historico'].append(novo_item)
        self.salvar()

    def atualizar_movimento(self, indice, valor, descricao, categoria):
        """Atualiza uma transação existente."""
        item = self.dados['historico'][indice]
        
        # Reverte valores antigos
        if item['tipo'] == "in":
            self.dados['saldo'] -= item['valor']
            self.dados['receitas'] -= item['valor']
        else:
            self.dados['saldo'] += item['valor']
            self.dados['despesas'] -= item['valor']

        # Aplica novos valores
        item['valor'] = valor
        item['desc'] = descricao
        item['categoria'] = categoria

        if item['tipo'] == "in":
            self.dados['saldo'] += valor
            self.dados['receitas'] += valor
        else:
            self.dados['saldo'] -= valor
            self.dados['despesas'] += valor

        self.salvar()

    def excluir_movimento(self, indice):
        """Remove uma transação."""
        item = self.dados['historico'].pop(indice)
        if item['tipo'] == "in":
            self.dados['saldo'] -= item['valor']
            self.dados['receitas'] -= item['valor']
        else:
            self.dados['saldo'] += item['valor']
            self.dados['despesas'] -= item['valor']
        self.salvar()

    def adicionar_categoria(self, nome_categoria):
        """Adiciona uma nova categoria."""
        nome = nome_categoria.strip()
        if nome and nome not in self.dados["categorias"]:
            self.dados["categorias"].append(nome)
            self.salvar()
            return True
        return False


def formatar_moeda(valor):
    """Formata valor para padrão brasileiro (R$ 1.234,56)."""
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


async def main(page: ft.Page):
    """Função principal da aplicação."""
    page.title = "Gestor de Finanças"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 450
    page.window_height = 800
    page.bgcolor = "#0F172A"

    finance_manager = FinancasData()

    # Componentes Globais da Interface
    saldo_txt = ft.Text("", size=36, weight="bold")
    receitas_txt = ft.Text("", color="green", weight="w600")
    despesas_txt = ft.Text("", color="red", weight="w600")
    lista_historico = ft.ListView(expand=True, spacing=10, padding=10)

    # Campos de Edição (Diálogo)
    edit_val = ft.TextField(label="Valor (R$)", prefix=ft.Text("R$ "), keyboard_type="number")
    edit_desc = ft.TextField(label="Descrição")
    edit_cat = ft.Dropdown(label="Categoria")
    item_atual_index = [None]

    def mostrar_erro(mensagem):
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=ft.colors.RED)
        page.snack_bar.open = True
        page.update()

    def mostrar_sucesso(mensagem):
        page.snack_bar = ft.SnackBar(ft.Text(mensagem), bgcolor=ft.colors.GREEN)
        page.snack_bar.open = True
        page.update()

    def atualizar_ui():
        """Atualiza a interface com os dados atuais."""
        d = finance_manager.dados
        saldo_txt.value = formatar_moeda(d['saldo'])
        saldo_txt.color = "white" if d['saldo'] >= 0 else "red"
        receitas_txt.value = f"↑ {formatar_moeda(d['receitas'])}"
        despesas_txt.value = f"↓ {formatar_moeda(d['despesas'])}"

        lista_historico.controls.clear()
        for i, item in enumerate(reversed(d['historico'])):
            idx_real = len(d['historico']) - 1 - i
            cor = ft.colors.GREEN if item.get('tipo') == "in" else ft.colors.RED
            icone = ft.icons.ARROW_UPWARD if item.get('tipo') == "in" else ft.icons.ARROW_DOWNWARD
            
            lista_historico.controls.append(
                ft.Container(
                    content=ft.ListTile(
                        leading=ft.Icon(icone, color=cor),
                        title=ft.Text(f"{item.get('desc')} ({item.get('categoria')})", weight="bold"),
                        subtitle=ft.Text(item.get('data'), size=11),
                        trailing=ft.Text(formatar_moeda(item.get('valor')), color=cor, weight="bold"),
                        on_click=lambda _, idx=idx_real: abrir_edicao(idx),
                    ),
                    bgcolor="#1E293B", border_radius=12,
                )
            )
        page.update()

    def abrir_edicao(idx):
        item = finance_manager.dados['historico'][idx]
        item_atual_index[0] = idx
        edit_val.value = str(item['valor'])
        edit_desc.value = item['desc']
        edit_cat.options = [ft.dropdown.Option(c) for c in finance_manager.dados["categorias"]]
        edit_cat.value = item.get('categoria', 'Outros')
        dlg_editar.open = True
        page.update()

    def salvar_edicao(e):
        try:
            novo_v = float(edit_val.value.replace(",", "."))
            finance_manager.atualizar_movimento(item_atual_index[0], novo_v, edit_desc.value, edit_cat.value)
            dlg_editar.open = False
            atualizar_ui()
        except: mostrar_erro("Dados inválidos!")

    def excluir_item(e):
        finance_manager.excluir_movimento(item_atual_index[0])
        dlg_editar.open = False
        atualizar_ui()

    dlg_editar = ft.AlertDialog(
        title=ft.Text("Editar Transação"),
        content=ft.Column([edit_val, edit_desc, edit_cat], tight=True, width=300),
        actions=[
            ft.IconButton(ft.icons.DELETE_OUTLINE, icon_color="red", on_click=excluir_item),
            ft.TextButton("Cancelar", on_click=lambda _: setattr(dlg_editar, "open", False) or page.update()),
            ft.ElevatedButton("Salvar", on_click=salvar_edicao, bgcolor="blue", color="white"),
        ],
    )
    page.overlay.append(dlg_editar)

    def abrir_relatorios():
        rel = TelaRelatorios(finance_manager, ao_voltar=mostrar_dashboard)
        rel.build(page)

    def mostrar_dashboard():
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.START
        page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH

        val_in = ft.TextField(label="Valor (R$)", prefix=ft.Text("R$ "), border_radius=10, keyboard_type="number")
        desc_in = ft.TextField(label="Descrição", border_radius=10)
        cat_in = ft.Dropdown(
            label="Categoria", border_radius=10, expand=True,
            options=[ft.dropdown.Option(c) for c in finance_manager.dados["categorias"]],
            value="Outros"
        )

        def salvar_nova_categoria(e):
            if finance_manager.adicionar_categoria(nova_cat_field.value):
                cat_in.options.append(ft.dropdown.Option(nova_cat_field.value))
                cat_in.value = nova_cat_field.value
                dialog_nova_cat.open = False
                page.update()

        nova_cat_field = ft.TextField(label="Nome da Categoria")
        dialog_nova_cat = ft.AlertDialog(
            title=ft.Text("Nova Categoria"),
            content=nova_cat_field,
            actions=[ft.TextButton("Adicionar", on_click=salvar_nova_categoria)],
        )
        page.overlay.append(dialog_nova_cat)

        def on_add_click(tipo):
            try:
                v = float(val_in.value.replace(",", "."))
                finance_manager.adicionar_movimento(v, desc_in.value, cat_in.value, tipo)
                val_in.value = ""; desc_in.value = ""; atualizar_ui()
            except: mostrar_erro("Valor inválido!")

        header = ft.Row([
            ft.Text("Gestor de Finanças", size=24, weight="bold", color="blue"),
            ft.Row([
                ft.IconButton(ft.icons.BAR_CHART_ROUNDED, on_click=lambda _: abrir_relatorios()),
                ft.IconButton(ft.icons.LOGOUT_ROUNDED, on_click=lambda _: mostrar_login())
            ])
        ], alignment="spaceBetween")

        resumo_card = ft.Container(
            content=ft.Column([
                ft.Text("Saldo Total", size=14, color="blue200"),
                saldo_txt,
                ft.Divider(color="white24"),
                ft.Row([receitas_txt, despesas_txt], alignment="spaceBetween")
            ]),
            padding=25, bgcolor="#1E293B", border_radius=20
        )

        page.add(
            header, resumo_card,
            ft.Text("Nova Transação", size=16, weight="bold", color="white70"),
            val_in, desc_in, 
            ft.Row([cat_in, ft.IconButton(ft.icons.ADD, on_click=lambda _: setattr(dialog_nova_cat, "open", True) or page.update())]),
            ft.Row([
                ft.ElevatedButton("Ganho", icon=ft.icons.ADD, bgcolor="green", color="white", on_click=lambda _: on_add_click("in"), expand=True),
                ft.ElevatedButton("Gasto", icon=ft.icons.REMOVE, bgcolor="red", color="white", on_click=lambda _: on_add_click("out"), expand=True),
            ]),
            ft.Text("Histórico", size=16, weight="bold", color="white70"),
            lista_historico
        )
        atualizar_ui()

    # --- NOVO SISTEMA DE LOGIN E CADASTRO ---

    def mostrar_cadastro(e=None):
        """Tela para cadastrar novo usuário/senha ou redefinir."""
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        novo_user = ft.TextField(label="Definir Usuário", width=300, border_radius=10, prefix_icon=ft.icons.PERSON_ADD)
        nova_pass = ft.TextField(label="Definir Senha", width=300, password=True, can_reveal_password=True, border_radius=10, prefix_icon=ft.icons.PASSWORD)

        def salvar_cadastro(e):
            if novo_user.value and nova_pass.value:
                page.client_storage.set("app_user", novo_user.value)
                page.client_storage.set("app_pass", nova_pass.value)
                mostrar_sucesso("Acesso configurado com sucesso!")
                mostrar_login()
            else:
                mostrar_erro("Preencha todos os campos!")

        page.add(
            ft.Icon(ft.icons.SETTINGS_ACCESSIBILITY_ROUNDED, size=60, color="green"),
            ft.Text("Configurar Acesso", size=24, weight="bold"),
            novo_user, nova_pass,
            ft.ElevatedButton("SALVAR CONFIGURAÇÃO", on_click=salvar_cadastro, width=300, bgcolor="green", color="white", height=50),
            ft.TextButton("Cancelar e Voltar", on_click=lambda _: mostrar_login())
        )
        page.update()

    def mostrar_login():
        """Exibe a tela de login com mensagem de erro integrada."""
        page.clean()
        page.vertical_alignment = ft.MainAxisAlignment.CENTER
        page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
        
        # 1. Criamos o componente de texto para o erro (inicia vazio)
        erro_field = ft.Text("", color="red", size=12, weight="bold")

        user_in = ft.TextField(label="Usuário", width=300, border_radius=10, prefix_icon=ft.icons.PERSON)
        pass_in = ft.TextField(label="Senha", width=300, password=True, can_reveal_password=True, border_radius=10, prefix_icon=ft.icons.LOCK)

        def realizar_login(e):
            u_salvo = page.client_storage.get("app_user")
            p_salvo = page.client_storage.get("app_pass")

            # Resetamos a mensagem de erro a cada tentativa
            erro_field.value = ""
            
            if not user_in.value or not pass_in.value:
                erro_field.value = "Por favor, preencha todos os campos!"
                page.update()
                return

            # Validação
            sucesso = False
            if u_salvo is None:
                if user_in.value == "admin" and pass_in.value == "1234":
                    sucesso = True
                else:
                    erro_field.value = "Usuário ou senha padrão incorretos!"
            else:
                if user_in.value == u_salvo and pass_in.value == p_salvo:
                    sucesso = True
                else:
                    erro_field.value = "Usuário ou senha inválidos!"

            if sucesso:
                mostrar_dashboard()
            else:
                page.update()

        page.add(
            ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=80, color="blue"),
            ft.Text("Gestor de Finanças", size=28, weight="bold"),
            ft.Container(height=20),
            user_in, 
            pass_in,
            ft.ElevatedButton("ENTRAR", on_click=realizar_login, width=300, height=50, bgcolor="blue", color="white"),
            ft.Row([
                ft.TextButton("Criar Conta / Esqueci Senha", on_click=mostrar_cadastro),
            ], alignment=ft.MainAxisAlignment.CENTER),
            # 2. Adicionamos o campo de erro logo abaixo do link
            erro_field 
        )
        page.update()

    # --- INÍCIO DO APP (SPLASH) ---
    page.vertical_alignment = ft.MainAxisAlignment.CENTER
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.add(
        ft.Column([
            ft.Icon(ft.icons.ACCOUNT_BALANCE_WALLET_ROUNDED, size=100, color="blue"),
            ft.Text("Gestor de Finanças", size=32, weight="bold"),
            ft.ProgressRing(width=20, stroke_width=2),
        ], horizontal_alignment="center", alignment="center")
    )
    page.update()
    await asyncio.sleep(2)
    mostrar_login()

if __name__ == "__main__":
    ft.app(target=main)
