from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QSortFilterProxyModel, Qt
from PySide6.QtGui import QAction, QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QTableView,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from app.core.analyzer import Analyzer
from app.core.models import AnalysisResult, LogEvent
from app.core.report_generator import ReportGenerator


CATEGORIES = [
    "All",
    "Database",
    "Network",
    "License",
    "Search / OpenSearch",
    "Cluster / Hazelcast",
    "NFS / Shared Home",
    "SMTP / TLS",
    "Plugin",
    "Memory / JVM",
    "Startup / Shutdown",
    "Authentication / SSO",
    "Unknown",
]


class EventFilterProxy(QSortFilterProxyModel):
    def __init__(self) -> None:
        super().__init__()
        self.level = "All"
        self.category = "All"
        self.keyword = ""

    def set_filters(self, level: str, category: str, keyword: str) -> None:
        self.level = level
        self.category = category
        self.keyword = keyword.lower().strip()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent) -> bool:  # noqa: ANN001
        model = self.sourceModel()
        if model is None:
            return True

        level = model.index(source_row, 1, source_parent).data()
        category = model.index(source_row, 2, source_parent).data()
        row_text = " ".join(
            str(model.index(source_row, col, source_parent).data() or "").lower() for col in range(model.columnCount())
        )

        if self.level != "All" and level != self.level:
            return False
        if self.category != "All" and category != self.category:
            return False
        if self.keyword and self.keyword not in row_text:
            return False
        return True


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Atlassian Log Analyzer")
        self.analyzer = Analyzer(rules_dir=rules_dir())
        self.report_generator = ReportGenerator()
        self.result: AnalysisResult | None = None

        self.model = QStandardItemModel(0, 5)
        self.model.setHorizontalHeaderLabels(["Time", "Level", "Category", "File", "Message"])
        self.proxy = EventFilterProxy()
        self.proxy.setSourceModel(self.model)

        self._build_ui()
        self._build_toolbar()

    def _build_toolbar(self) -> None:
        toolbar = QToolBar("Main")
        self.addToolBar(toolbar)

        open_files = QAction("Open Files", self)
        open_files.triggered.connect(self.choose_files)
        toolbar.addAction(open_files)

        open_folder = QAction("Open Folder", self)
        open_folder.triggered.connect(self.choose_folder)
        toolbar.addAction(open_folder)

        open_zip = QAction("Open Support Zip", self)
        open_zip.triggered.connect(self.choose_zip)
        toolbar.addAction(open_zip)

        toolbar.addSeparator()

        export = QAction("Export Report", self)
        export.triggered.connect(self.export_report)
        toolbar.addAction(export)

    def _build_ui(self) -> None:
        root = QWidget()
        layout = QVBoxLayout(root)
        layout.setContentsMargins(16, 14, 16, 16)
        layout.setSpacing(12)

        title = QLabel("Atlassian Log Analyzer")
        title.setObjectName("Title")
        layout.addWidget(title)

        summary = QGridLayout()
        summary.setHorizontalSpacing(12)
        summary.setVerticalSpacing(8)
        self.summary_labels: dict[str, QLabel] = {}
        fields = [
            ("Product", "product"),
            ("Files", "file_count"),
            ("ERROR", "total_errors"),
            ("WARN", "total_warnings"),
            ("First Error", "first_error_time"),
            ("Last Error", "last_error_time"),
            ("Top Category", "top_category"),
        ]
        for index, (label, key) in enumerate(fields):
            caption = QLabel(label)
            caption.setObjectName("Caption")
            value = QLabel("-")
            value.setObjectName("Metric")
            value.setTextInteractionFlags(Qt.TextSelectableByMouse)
            self.summary_labels[key] = value
            summary.addWidget(caption, index // 4 * 2, index % 4)
            summary.addWidget(value, index // 4 * 2 + 1, index % 4)
        layout.addLayout(summary)

        filter_bar = QHBoxLayout()
        self.level_filter = QComboBox()
        self.level_filter.addItems(["All", "ERROR", "WARN"])
        self.category_filter = QComboBox()
        self.category_filter.addItems(CATEGORIES)
        self.keyword_filter = QLineEdit()
        self.keyword_filter.setPlaceholderText("Keyword")
        self.clear_filters_button = QPushButton("Clear")
        filter_bar.addWidget(QLabel("Level"))
        filter_bar.addWidget(self.level_filter)
        filter_bar.addWidget(QLabel("Category"))
        filter_bar.addWidget(self.category_filter)
        filter_bar.addWidget(self.keyword_filter, 1)
        filter_bar.addWidget(self.clear_filters_button)
        layout.addLayout(filter_bar)

        self.table = QTableView()
        self.table.setModel(self.proxy)
        self.table.setSortingEnabled(True)
        self.table.setSelectionBehavior(QTableView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        layout.addWidget(self.table, 1)

        self.level_filter.currentTextChanged.connect(self.apply_filters)
        self.category_filter.currentTextChanged.connect(self.apply_filters)
        self.keyword_filter.textChanged.connect(self.apply_filters)
        self.clear_filters_button.clicked.connect(self.clear_filters)

        root.setStyleSheet(
            """
            QLabel#Title { font-size: 24px; font-weight: 700; color: #172b4d; }
            QLabel#Caption { color: #5e6c84; font-size: 12px; }
            QLabel#Metric { font-size: 18px; font-weight: 600; color: #172b4d; }
            QTableView { border: 1px solid #dfe1e6; gridline-color: #ebecf0; }
            QLineEdit, QComboBox { min-height: 28px; }
            """
        )
        self.setCentralWidget(root)

    def choose_files(self) -> None:
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Select log files",
            "",
            "Logs and archives (*.log *.txt *.out *.gz *.zip);;All files (*)",
        )
        if files:
            self.analyze([Path(file) for file in files])

    def choose_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select log folder")
        if folder:
            self.analyze([Path(folder)])

    def choose_zip(self) -> None:
        file_name, _ = QFileDialog.getOpenFileName(self, "Select support zip", "", "Zip archives (*.zip)")
        if file_name:
            self.analyze([Path(file_name)])

    def analyze(self, paths: list[Path]) -> None:
        try:
            self.result = self.analyzer.analyze_paths(paths)
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Analysis failed", str(exc))
            return
        self.update_summary()
        self.update_table(self.result.events)

    def update_summary(self) -> None:
        if not self.result:
            return
        summary = self.result.summary
        self.summary_labels["product"].setText(summary.product)
        self.summary_labels["file_count"].setText(str(summary.file_count))
        self.summary_labels["total_errors"].setText(str(summary.total_errors))
        self.summary_labels["total_warnings"].setText(str(summary.total_warnings))
        self.summary_labels["first_error_time"].setText(summary.first_error_time or "-")
        self.summary_labels["last_error_time"].setText(summary.last_error_time or "-")
        self.summary_labels["top_category"].setText(summary.top_category)

    def update_table(self, events: list[LogEvent]) -> None:
        self.model.removeRows(0, self.model.rowCount())
        for event in events:
            row = [
                QStandardItem(event.time),
                QStandardItem(event.level),
                QStandardItem(event.category),
                QStandardItem(event.file),
                QStandardItem(event.message),
            ]
            for item in row:
                item.setEditable(False)
            self.model.appendRow(row)
        self.table.resizeColumnsToContents()

    def apply_filters(self) -> None:
        self.proxy.set_filters(
            self.level_filter.currentText(),
            self.category_filter.currentText(),
            self.keyword_filter.text(),
        )

    def clear_filters(self) -> None:
        self.level_filter.setCurrentText("All")
        self.category_filter.setCurrentText("All")
        self.keyword_filter.clear()

    def export_report(self) -> None:
        if not self.result:
            QMessageBox.information(self, "No report", "Analyze logs before exporting a report.")
            return

        file_name, selected_filter = QFileDialog.getSaveFileName(
            self,
            "Export report",
            "atlassian-log-report.html",
            "HTML (*.html);;Markdown (*.md);;JSON (*.json);;CSV (*.csv)",
        )
        if not file_name:
            return

        report_format = format_from_filter(selected_filter, file_name)
        try:
            rendered = self.report_generator.render(self.result, report_format)
            Path(file_name).write_text(rendered, encoding="utf-8")
        except Exception as exc:  # noqa: BLE001
            QMessageBox.critical(self, "Export failed", str(exc))


def format_from_filter(selected_filter: str, file_name: str) -> str:
    suffix = Path(file_name).suffix.lower()
    if suffix == ".md":
        return "markdown"
    if suffix == ".json":
        return "json"
    if suffix == ".csv":
        return "csv"
    if "Markdown" in selected_filter:
        return "markdown"
    if "JSON" in selected_filter:
        return "json"
    if "CSV" in selected_filter:
        return "csv"
    return "html"


def rules_dir() -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path.cwd()))
    bundled_rules = bundle_root / "rules"
    if bundled_rules.exists():
        return bundled_rules
    return Path("rules")
