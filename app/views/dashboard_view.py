from __future__ import annotations

from typing import List, Tuple

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QGroupBox, QGridLayout

from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from app.utils.firebase_repository import FirebaseRepository
from app.views.components.dialog_theme import apply_app_font
from app.config import settings as app_settings


class DashboardView(QWidget):
    def __init__(self, repository: FirebaseRepository):
        super().__init__()
        self._repo = repository

        layout = QVBoxLayout(self)

        # Ações de topo
        actions = QHBoxLayout()
        self._range = QComboBox()
        self._range.addItems(["Últimos 7 dias", "Últimos 30 dias", "Últimos 90 dias", "Tudo"])
        btn_refresh = QPushButton("Atualizar")
        btn_export = QPushButton("Exportar Relatório")
        btn_refresh.clicked.connect(self.reload)
        btn_export.clicked.connect(self._export_report)
        actions.addWidget(QLabel("Dashboard — Receitas e Serviços"))
        actions.addWidget(self._range)
        actions.addStretch(1)
        actions.addWidget(btn_refresh)
        actions.addWidget(btn_export)
        layout.addLayout(actions)

        # Cards resumidos
        gb = QGroupBox("Resumo")
        grid = QGridLayout(gb)
        self._lbl_orders = QLabel("Pedidos: 0")
        self._lbl_total = QLabel("Total: R$ 0,00")
        self._lbl_avg = QLabel("Ticket médio: R$ 0,00")
        grid.addWidget(self._lbl_orders, 0, 0)
        grid.addWidget(self._lbl_total, 0, 1)
        grid.addWidget(self._lbl_avg, 0, 2)
        layout.addWidget(gb)

        # Gráfico Top serviços
        self._fig_top = Figure(figsize=(7.2, 3.2))
        self._canvas_top = FigureCanvas(self._fig_top)
        layout.addWidget(QLabel("Serviços mais rentáveis"))
        layout.addWidget(self._canvas_top)

        # Gráfico Bottom serviços
        self._fig_bottom = Figure(figsize=(7.2, 3.2))
        self._canvas_bottom = FigureCanvas(self._fig_bottom)
        layout.addWidget(QLabel("Serviços menos rentáveis"))
        layout.addWidget(self._canvas_bottom)

        # Gráfico série temporal
        self._fig_days = Figure(figsize=(7.2, 3.2))
        self._canvas_days = FigureCanvas(self._fig_days)
        layout.addWidget(QLabel("Receita por dia (últimos 30)"))
        layout.addWidget(self._canvas_days)

        apply_app_font(self)
        self.reload()

    def reload(self) -> None:
        self._update_summary()
        self._draw_top()
        self._draw_bottom()
        self._draw_days()

    def _selected_days(self) -> int | None:
        idx = self._range.currentIndex()
        return {0: 7, 1: 30, 2: 90}.get(idx, None)

    def _update_summary(self) -> None:
        days = self._selected_days() or 30
        count, total, avg = self._repo.summary_since(days)
        self._lbl_orders.setText(f"Pedidos: {count}")
        self._lbl_total.setText(f"Total: R$ {total/100:.2f}")
        self._lbl_avg.setText(f"Ticket médio: R$ {avg/100:.2f}")

    def _draw_top(self) -> None:
        data = self._repo.top_services_by_revenue(8, self._selected_days())
        labels = [f"{n} ({t}/{s or '-'})" for n, t, s, _ in data]
        values = [c / 100.0 for _, _, _, c in data]
        self._fig_top.clear()
        ax = self._fig_top.add_subplot(111)
        ax.barh(labels, values, color="#2e7d32")
        ax.set_xlabel("R$")
        # Evita sobreposição de rótulos
        fs = int(app_settings.get_settings().get("UI_FONT_SIZE_PT", 12))
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=max(8, fs - 1))
        self._fig_top.subplots_adjust(left=0.38, right=0.98, top=0.95, bottom=0.15)
        self._canvas_top.draw()

    def _draw_bottom(self) -> None:
        data = self._repo.bottom_services_by_revenue(8, self._selected_days())
        labels = [f"{n} ({t}/{s or '-'})" for n, t, s, _ in data]
        values = [c / 100.0 for _, _, _, c in data]
        self._fig_bottom.clear()
        ax = self._fig_bottom.add_subplot(111)
        ax.barh(labels, values, color="#c62828")
        ax.set_xlabel("R$")
        fs = int(app_settings.get_settings().get("UI_FONT_SIZE_PT", 12))
        ax.set_yticks(range(len(labels)))
        ax.set_yticklabels(labels, fontsize=max(8, fs - 1))
        self._fig_bottom.subplots_adjust(left=0.38, right=0.98, top=0.95, bottom=0.15)
        self._canvas_bottom.draw()

    def _draw_days(self) -> None:
        days = self._selected_days() or 30
        data = list(reversed(self._repo.revenue_by_day(days)))
        labels = [d for d, _ in data]
        values = [c / 100.0 for _, c in data]
        self._fig_days.clear()
        ax = self._fig_days.add_subplot(111)
        ax.plot(labels, values, marker="o", color="#007065")
        ax.set_xticks(range(0, len(labels), max(1, len(labels)//10)))
        ax.set_ylabel("R$")
        ax.grid(True, alpha=0.3)
        ax.tick_params(axis='x', labelrotation=45)
        self._fig_days.subplots_adjust(bottom=0.28, left=0.1, right=0.98, top=0.95)
        self._canvas_days.draw()

    def _export_report(self) -> None:
        # Exporta CSV simples com top/bottom e série por dia
        import csv
        from datetime import datetime
        fname = f"relatorio_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        with open(fname, "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["Top serviços por receita"])
            w.writerow(["service_name", "service_type", "service_subtype", "total_cents"])
            for row in self._repo.top_services_by_revenue(20):
                w.writerow(row)
            w.writerow([])
            w.writerow(["Bottom serviços por receita"])
            w.writerow(["service_name", "service_type", "service_subtype", "total_cents"])
            for row in self._repo.bottom_services_by_revenue(20):
                w.writerow(row)
            w.writerow([])
            w.writerow(["Receita por dia (últimos 90)"])
            w.writerow(["day", "total_cents"])
            for row in self._repo.revenue_by_day(90):
                w.writerow(row)
        # Simples feedback no título
        self.window().setWindowTitle(self.window().windowTitle() + f" — Exportado {fname}")

    


