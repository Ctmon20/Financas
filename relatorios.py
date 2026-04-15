"""
Módulo de Relatórios - Finanças Smart
Versão 2.0 - Corrigida e Otimizada
"""

import flet as ft
from datetime import datetime
from flet import PieChart, PieChartSection


class TelaRelatorios:
    """Gerencia a tela de relatórios com gráficos e análises."""

    def __init__(self, finance_manager, ao_voltar):
        self.fm = finance_manager
        self.ao_voltar = ao_voltar
        self.chart = PieChart(
            sections=[],
            center_space_radius=35,
            sections_space=2,
            height=200,
        )

    def obter_meses_anos(self):
        """Extrai e ordena os meses/anos disponíveis no histórico."""
        opcoes = set()
        for item in self.fm.dados.get('historico', []):
            try:
                data_part = item.get('data', '').split(' ')[0]
                partes = data_part.split('/')
                if len(partes) == 3:
                    opcoes.add(f"{partes[1]}/{partes[2]}")
            except (IndexError, AttributeError):
                continue
        
        lista = list(opcoes)
        try:
            lista.sort(key=lambda x: datetime.strptime(x, "%m/%Y"), reverse=True)
        except ValueError:
            lista.sort(reverse=True)
        
        return lista

    def build(self, page: ft.Page):
        """Constrói a interface da tela de relatórios."""
        page.clean()
        page.padding = ft.padding.only(top=5, left=10, right=10, bottom=10)

        opcoes_filtro = self.obter_meses_anos()

        CORES = [
            ft.colors.RED, ft.colors.BLUE, ft.colors.GREEN,
            ft.colors.ORANGE, ft.colors.PURPLE, ft.colors.CYAN,
            ft.colors.AMBER, ft.colors.PINK, ft.colors.LIME,
            ft.colors.TEAL, ft.colors.INDIGO, ft.colors.DEEP_ORANGE
        ]

        lbl_total = ft.Text(size=18, weight="bold", color="red")

        tabela_transacoes = ft.DataTable(
            columns=[
                ft.DataColumn(ft.Text("Descrição", weight="bold")),
                ft.DataColumn(ft.Text("Valor", weight="bold")),
                ft.DataColumn(ft.Text("Data", weight="bold")),
            ],
            rows=[],
            column_spacing=15,
            heading_row_height=40,
            horizontal_lines=ft.border.BorderSide(0.5, "grey800"),
        )

        def atualizar_dados():
            """Atualiza gráfico e tabela baseado no filtro selecionado."""
            filtro = drop_filtro.value
            if not filtro:
                return

            gastos_por_cat = {}
            transacoes_filtradas = []
            total_mes = 0

            for item in self.fm.dados.get('historico', []):
                try:
                    data_part = item.get('data', '').split(' ')[0]
                    partes = data_part.split('/')
                    
                    if len(partes) != 3:
                        continue
                    
                    # Filtra por mês/ano e apenas despesas (out)
                    if f"{partes[1]}/{partes[2]}" == filtro and item.get('tipo') == "out":
                        cat = item.get('categoria', 'Outros')
                        valor = float(item.get('valor', 0))

                        gastos_por_cat[cat] = gastos_por_cat.get(cat, 0) + valor
                        total_mes += valor
                        transacoes_filtradas.append(item)
                except (ValueError, IndexError, AttributeError, TypeError):
                    continue

            # --- ATUALIZA GRÁFICO ---
            novas_secoes = []
            for i, (cat, valor) in enumerate(gastos_por_cat.items()):
                porcentagem = (valor / total_mes * 100) if total_mes > 0 else 0
                novas_secoes.append(
                    PieChartSection(
                        valor,
                        title=f"{cat}\n{porcentagem:.0f}%",
                        color=CORES[i % len(CORES)],
                        radius=45,
                        title_style=ft.TextStyle(size=9, weight="bold", color="white"),
                    )
                )

            # --- ATUALIZA TABELA ---
            novas_linhas = []
            for trans in reversed(transacoes_filtradas):
                nome_exibicao = trans.get('desc') or trans.get('descricao') or "Gasto"
                valor_formatado = f"R$ {float(trans.get('valor', 0)):.2f}"
                data_exibicao = trans.get('data', '').split(' ')[0]

                novas_linhas.append(
                    ft.DataRow(
                        cells=[
                            ft.DataCell(ft.Text(nome_exibicao, size=12)),
                            ft.DataCell(ft.Text(valor_formatado, color="red", weight="bold", size=12)),
                            ft.DataCell(ft.Text(data_exibicao, size=11)),
                        ]
                    )
                )

            self.chart.sections = novas_secoes
            tabela_transacoes.rows = novas_linhas

            # Formata total
            valor_fmt = f"R$ {total_mes:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
            lbl_total.value = f"Total Gasto: {valor_fmt}"
            page.update()

        drop_filtro = ft.Dropdown(
            label="Mês/Ano",
            options=[ft.dropdown.Option(opt) for opt in opcoes_filtro],
            on_change=lambda e: atualizar_dados(),
            height=50,
            expand=True
        )

        if opcoes_filtro:
            drop_filtro.value = opcoes_filtro[0]

        page.add(
            ft.Column([
                ft.Row([
                    ft.IconButton(ft.icons.ARROW_BACK, on_click=lambda _: self.ao_voltar()),
                    ft.Text("Relatórios", size=24, weight="bold")
                ], spacing=0),

                ft.Row([drop_filtro]),
                lbl_total,

                ft.Container(
                    content=self.chart,
                    alignment=ft.alignment.center,
                    height=220,
                    margin=ft.margin.only(top=10)
                ),

                ft.Text("Histórico de Gastos", size=16, weight="bold"),
                ft.Divider(height=1),

                ft.Row(
                    [tabela_transacoes],
                    alignment=ft.MainAxisAlignment.CENTER,
                    scroll=ft.ScrollMode.AUTO
                ),

            ], scroll=ft.ScrollMode.AUTO, spacing=10, expand=True)
        )

        if opcoes_filtro:
            atualizar_dados()
        page.update()
