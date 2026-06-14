"""淡蓝色主题配色常量与 Qt 样式表生成。"""

# ── 颜色常量 ──────────────────────────────────────────

COLORS = {
    "window_bg":        "#e8f0fe",
    "card_bg":          "#ffffff",
    "card_border":      "#b0c4de",
    "primary_text":     "#1a237e",
    "secondary_text":   "#5c6bc0",
    "timestamp_text":   "#9e9e9e",
    "accent":           "#42a5f5",
    "accent_hover":     "#1e88e5",
    "danger":           "#ef5350",
    "danger_hover":     "#e53935",
    "success":          "#66bb6a",
    "pinned_bg":        "#fff8e1",
    "pinned_border":    "#ffe082",
    "scrollbar_handle": "#90caf9",
    "scrollbar_bg":     "#e8f0fe",
    "search_bg":        "#ffffff",
    "search_border":    "#90caf9",
}

# ── 全局样式表 ────────────────────────────────────────

APP_STYLESHEET = f"""
QMainWindow {{
    background-color: {COLORS["window_bg"]};
}}

QWidget#centralWidget {{
    background-color: {COLORS["window_bg"]};
}}

/* 滚动区域 */
QScrollArea {{
    border: none;
    background-color: transparent;
}}

QScrollBar:vertical {{
    background: {COLORS["scrollbar_bg"]};
    width: 8px;
    border-radius: 4px;
}}

QScrollBar::handle:vertical {{
    background: {COLORS["scrollbar_handle"]};
    border-radius: 4px;
    min-height: 30px;
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* 按钮 */
QPushButton {{
    border: 1px solid {COLORS["card_border"]};
    border-radius: 4px;
    padding: 4px 12px;
    background-color: {COLORS["card_bg"]};
    color: {COLORS["primary_text"]};
    font-size: 12px;
}}

QPushButton:hover {{
    background-color: {COLORS["accent"]};
    color: white;
    border-color: {COLORS["accent"]};
}}

QPushButton:pressed {{
    background-color: {COLORS["accent_hover"]};
}}

/* 搜索框 */
QLineEdit {{
    border: 2px solid {COLORS["search_border"]};
    border-radius: 20px;
    padding: 8px 16px;
    background-color: {COLORS["search_bg"]};
    color: {COLORS["primary_text"]};
    font-size: 14px;
}}

QLineEdit:focus {{
    border-color: {COLORS["accent"]};
}}

/* 下拉框 */
QComboBox {{
    border: 1px solid {COLORS["card_border"]};
    border-radius: 4px;
    padding: 4px 8px;
    background-color: {COLORS["card_bg"]};
    color: {COLORS["primary_text"]};
}}

QComboBox:hover {{
    border-color: {COLORS["accent"]};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 8px;
}}

/* 标签 */
QLabel {{
    color: {COLORS["primary_text"]};
}}

/* 工具提示 */
QToolTip {{
    background-color: {COLORS["primary_text"]};
    color: white;
    border: none;
    border-radius: 4px;
    padding: 4px 8px;
}}
"""
