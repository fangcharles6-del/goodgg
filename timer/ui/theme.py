"""番茄钟主题配色常量与 Qt 样式表生成。"""

# ── 颜色常量 ──────────────────────────────────────────

COLORS = {
    "window_bg":        "#fff5f5",
    "card_bg":          "#ffffff",
    "primary_text":     "#2c3e50",
    "secondary_text":   "#7f8c8d",
    "accent":           "#e74c3c",
    "accent_hover":     "#c0392b",
    "accent_light":     "#fadbd8",
    "warning":          "#f39c12",
    "warning_hover":    "#d68910",
    "progress_bg":      "#fadbd8",
    "progress_chunk":   "#e74c3c",
    "border":           "#f5b7b1",
}

# ── 全局样式表 ────────────────────────────────────────

APP_STYLESHEET = f"""
QWidget {{
    background-color: {COLORS["window_bg"]};
    color: {COLORS["primary_text"]};
    font-family: "Microsoft YaHei", "Segoe UI", sans-serif;
}}

/* 进度条 */
QProgressBar {{
    border: none;
    border-radius: 6px;
    background-color: {COLORS["progress_bg"]};
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS["progress_chunk"]};
    border-radius: 6px;
}}

/* 按钮公共属性 */
QPushButton#btnStart, QPushButton#btnPause, QPushButton#btnReset {{
    border-radius: 6px;
    padding: 8px 10px;
    font-size: 12px;
    font-weight: bold;
    min-width: 60px;
}}

/* 主按钮（开始） */
QPushButton#btnStart {{
    background-color: {COLORS["accent"]};
    color: white;
    border: none;
}}

QPushButton#btnStart:hover {{
    background-color: {COLORS["accent_hover"]};
}}

QPushButton#btnStart:disabled {{
    background-color: {COLORS["border"]};
    color: #999;
}}

/* 次按钮（暂停/重置） */
QPushButton#btnPause {{
    background-color: {COLORS["warning"]};
    color: white;
    border: none;
}}

QPushButton#btnPause:hover {{
    background-color: {COLORS["warning_hover"]};
}}

QPushButton#btnReset {{
    background-color: transparent;
    color: {COLORS["secondary_text"]};
    border: 1px solid {COLORS["border"]};
}}

QPushButton#btnReset:hover {{
    background-color: {COLORS["accent_light"]};
    color: {COLORS["accent"]};
}}

/* 复选框 */
QCheckBox {{
    color: {COLORS["secondary_text"]};
    font-size: 12px;
    spacing: 6px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border-radius: 3px;
    border: 2px solid {COLORS["border"]};
    background-color: {COLORS["card_bg"]};
}}

QCheckBox::indicator:checked {{
    background-color: {COLORS["accent"]};
    border-color: {COLORS["accent"]};
}}

/* 标签 */
QLabel {{
    color: {COLORS["primary_text"]};
    background: transparent;
}}

QLabel#labelCountdown {{
    font-size: 56px;
    font-weight: bold;
    color: {COLORS["accent"]};
    background: transparent;
}}

QLabel#labelSession {{
    font-size: 16px;
    font-weight: bold;
    color: {COLORS["primary_text"]};
    background: transparent;
}}

QLabel#labelPomodoro {{
    font-size: 13px;
    color: {COLORS["secondary_text"]};
    background: transparent;
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
