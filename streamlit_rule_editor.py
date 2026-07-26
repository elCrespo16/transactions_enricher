from __future__ import annotations
import copy
from flask import config
import yaml
from pathlib import Path
from itertools import count

import streamlit as st
import streamlit.components.v1 as components
from code_editor import code_editor

from transactions_rules.bank_rules import BankConfiguration, Rule


APP_TITLE = "Transactions Rules Editor"


class ThemeConfig:
    """Centralized theme and styling constants."""

    ACCENT_PRIMARY = "#2563eb"
    ACCENT_SECONDARY = "#3b82f6"
    ACCENT_LIGHT = "#dbeafe"

    BACKGROUND_MAIN = "#f8fbff"
    BACKGROUND_SECONDARY = "#eef4ff"

    TEXT_PRIMARY = "#0f172a"
    TEXT_SECONDARY = "#475569"
    TEXT_LIGHT = "#64748b"

    SIDEBAR_DARK = "#0f172a"
    SIDEBAR_DARKER = "#1e3a8a"

    BORDER_COLOR = "#dbeafe"
    BORDER_LIGHT = "rgba(255, 255, 255, 0.2)"

    SHADOW_LIGHT = "0 8px 24px rgba(37, 99, 235, 0.08)"
    SHADOW_MEDIUM = "0 6px 18px rgba(15, 23, 42, 0.04)"
    SHADOW_LIGHT_1 = "0 4px 12px rgba(37, 99, 235, 0.04)"


class StyleManager:
    """Manages all CSS styling for the application."""

    @staticmethod
    def apply_page_styles() -> None:
        st.markdown(
            f"""
            <style>
            .stApp {{
                background: linear-gradient(180deg, {ThemeConfig.BACKGROUND_MAIN} 0%, {ThemeConfig.BACKGROUND_SECONDARY} 100%);
                color: {ThemeConfig.TEXT_PRIMARY};
            }}

            [data-testid="stSidebar"] {{
                background: linear-gradient(180deg, {ThemeConfig.SIDEBAR_DARK} 0%, {ThemeConfig.SIDEBAR_DARKER} 100%);
            }}

            [data-baseweb="select"] div {{
                color: {ThemeConfig.SIDEBAR_DARK} !important;
            }}

            [data-testid="stSidebar"] * {{
                color: #eff6ff;
            }}

            [data-testid="stSidebar"] button {{
                background: rgba(255, 255, 255, 0.12) !important;
                border: 1px solid {ThemeConfig.BORDER_LIGHT} !important;
                color: #ffffff !important;
                border-radius: 999px !important;
                transition: all 0.2s ease !important;
            }}

            [data-testid="stSidebar"] button:hover {{
                background: rgba(255, 255, 255, 0.2) !important;
            }}

            [data-testid="stExpander"] {{
                background: rgba(255, 255, 255, 0.88);
                border: 1px solid {ThemeConfig.BORDER_COLOR};
                border-radius: 18px;
                box-shadow: {ThemeConfig.SHADOW_LIGHT};
            }}

            [data-testid="stExpander"] summary {{
                font-weight: 700;
                color: {ThemeConfig.TEXT_PRIMARY};
            }}

            .rule-card {{
                padding: 1.2rem;
                border-radius: 16px;
                border: 1px solid {ThemeConfig.BORDER_COLOR};
                background: linear-gradient(180deg, #ffffff 0%, {ThemeConfig.BACKGROUND_MAIN} 100%);
                margin-bottom: 0.75rem;
            }}

            .rule-card-header {{
                font-size: 1rem;
                font-weight: 700;
                color: {ThemeConfig.TEXT_PRIMARY};
                margin-bottom: 0.5rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .rule-card-id {{
                display: inline-block;
                background: {ThemeConfig.ACCENT_PRIMARY};
                color: white;
                padding: 0.25rem 0.5rem;
                border-radius: 6px;
                font-size: 0.75rem;
                font-weight: 800;
                min-width: 2rem;
                text-align: center;
            }}

            .rule-card-meta {{
                font-size: 0.9rem;
                color: {ThemeConfig.TEXT_SECONDARY};
            }}

            .rule-chip {{
                display: inline-block;
                padding: 0.2rem 0.6rem;
                margin: 0.15rem 0.2rem 0.15rem 0;
                border-radius: 999px;
                background: rgba({int(0x25):d}, {int(0x63):d}, {int(0xeb):d}, 0.12);
                color: #1d4ed8;
                font-size: 0.8rem;
                font-weight: 600;
            }}

            .chip-untagged {{
                background: rgba({ThemeConfig.TEXT_SECONDARY}, 0.1);
                color: {ThemeConfig.TEXT_SECONDARY};
            }}

            .metric-card {{
                border-radius: 16px;
                padding: 1.2rem 1.4rem;
                background: white;
                border: 1px solid {ThemeConfig.BORDER_COLOR};
                box-shadow: {ThemeConfig.SHADOW_MEDIUM};
                text-align: center;
            }}

            .metric-value {{
                font-size: 2.2rem;
                font-weight: 800;
                color: {ThemeConfig.ACCENT_PRIMARY};
                margin: 0.5rem 0;
            }}

            .metric-label {{
                font-size: 0.85rem;
                color: {ThemeConfig.TEXT_SECONDARY};
                text-transform: uppercase;
                letter-spacing: 0.05em;
                font-weight: 600;
            }}

            .overview-section {{
                background: white;
                border-radius: 18px;
                padding: 1.5rem;
                border: 1px solid {ThemeConfig.BORDER_COLOR};
                box-shadow: {ThemeConfig.SHADOW_LIGHT};
                margin-top: 1.5rem;
            }}

            .section-title {{
                font-size: 1.3rem;
                font-weight: 800;
                color: {ThemeConfig.TEXT_PRIMARY};
                margin-bottom: 1rem;
                display: flex;
                align-items: center;
                gap: 0.5rem;
            }}

            .section-title-icon {{
                font-size: 1.5rem;
            }}

            .tag-distribution {{
                margin-top: 1.5rem;
            }}

            .status-badge {{
                padding: 0.6rem 1rem;
                border-radius: 8px;
                font-size: 0.9rem;
                font-weight: 600;
            }}

            .status-success {{
                background: rgba(34, 197, 94, 0.12);
                color: #15803d;
                border: 1px solid rgba(34, 197, 94, 0.3);
            }}

            .status-error {{
                background: rgba(239, 68, 68, 0.12);
                color: #b91c1c;
                border: 1px solid rgba(239, 68, 68, 0.3);
            }}

            /* Selected file badge in the sidebar */
            .selected-file {{
                display: inline-block;
                background: {ThemeConfig.ACCENT_PRIMARY};
                color: #fff;
                padding: 0.35rem 0.8rem;
                border-radius: 999px;
                font-weight: 700;
                margin-bottom: 0.5rem;
                box-shadow: 0 4px 12px rgba(37,99,235,0.12);
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )


class FileManager:
    """Handles file discovery and loading."""

    @staticmethod
    def discover_rules_files(base_path: Path) -> list[Path]:
        candidates = []
        for pattern in ("**/*_bank_rules.yaml", "**/*_bank_rules.yml"):
            candidates.extend(base_path.glob(pattern))
        return sorted({path.resolve() for path in candidates if path.is_file()})

    @staticmethod
    def load_file_content(file_path: Path) -> str:
        return file_path.read_text(encoding="utf-8")


class YamlManager:
    """Handles YAML parsing and dumping."""

    @staticmethod
    def parse_rules_yaml(raw_yaml: str) -> BankConfiguration:
        parsed = yaml.safe_load(raw_yaml) or {}
        return BankConfiguration.parse_obj(parsed)

    @staticmethod
    def dump_rules_yaml(rules: BankConfiguration) -> str:
        return yaml.safe_dump(rules.dict(), sort_keys=False, allow_unicode=True)


class RulesEditorState:
    """Manages all editor state and rule operations."""

    @staticmethod
    def ensure_editor_state() -> None:
        st.session_state.setdefault("editor_rules", [])
        st.session_state.setdefault("next_rule_id", count(1))
        st.session_state.setdefault("active_tag_filter", [])
        st.session_state.setdefault("focus_rule_id", None)
        st.session_state.setdefault("scroll_to_top", False)

    @staticmethod
    def build_editor_rules(rules: BankConfiguration) -> list[dict]:
        editor_rules = []
        for rule in rules.rules:
            editor_rules.append(
                {
                    "id": next(st.session_state.next_rule_id),
                    "rule": rule,
                }
            )
        return editor_rules

    @staticmethod
    def refresh_parsed_from_editor() -> None:
        if st.session_state.parsed_rules is not None:
            st.session_state.parsed_rules.rules = [
                item["rule"] for item in st.session_state.editor_rules
            ]
        else:
            st.session_state.parsed_rules = BankConfiguration(
                rules=[item["rule"] for item in st.session_state.editor_rules]
            )
        st.session_state.yaml_text = YamlManager.dump_rules_yaml(st.session_state.parsed_rules)

    @staticmethod
    def load_rules_into_editor(rules: BankConfiguration) -> None:
        st.session_state.parsed_rules = rules
        st.session_state.editor_rules = RulesEditorState.build_editor_rules(rules)
        st.session_state.yaml_text = YamlManager.dump_rules_yaml(rules)

    @staticmethod
    def init_state() -> None:
        st.session_state.setdefault("yaml_text", "")
        st.session_state.setdefault("selected_file", None)
        st.session_state.setdefault("parsed_rules", None)
        st.session_state.setdefault("status_message", "")
        st.session_state.setdefault("status_type", "info")
        RulesEditorState.ensure_editor_state()

    @staticmethod
    def blank_rule() -> dict:
        return {"conditions": [], "operations": []}


class RuleOperations:
    """Handles operations on individual rules."""

    @staticmethod
    def add_blank_rule() -> None:
        new_rule_id = next(st.session_state.next_rule_id)
        editor_rule = {
            "id": new_rule_id,
            "rule": Rule.parse_obj(RulesEditorState.blank_rule()),
        }
        st.session_state.editor_rules.insert(0, editor_rule)
        RulesEditorState.refresh_parsed_from_editor()
        st.session_state.active_tag_filter = []
        st.session_state.focus_rule_id = new_rule_id
        st.session_state.scroll_to_top = True

    @staticmethod
    def delete_rule(rule_id: int) -> None:
        st.session_state.editor_rules = [
            item for item in st.session_state.editor_rules if item["id"] != rule_id
        ]
        RulesEditorState.refresh_parsed_from_editor()

    @staticmethod
    def duplicate_rule(rule_id: int) -> None:
        for index, item in enumerate(st.session_state.editor_rules):
            if item["id"] != rule_id:
                continue
            duplicated_rule = copy.deepcopy(item["rule"])
            new_editor_rule = {
                "id": next(st.session_state.next_rule_id),
                "rule": duplicated_rule,
            }
            st.session_state.editor_rules.insert(index + 1, new_editor_rule)
            RulesEditorState.refresh_parsed_from_editor()
            return


class RuleCardRenderer:
    """Renders individual rule cards."""

    @staticmethod
    def format_rule_summary(rule) -> str:
        condition_count = len(rule.conditions)
        operation_count = len(rule.operations)

        if condition_count == 0:
            condition_text = "Applies to all"
        elif condition_count == 1:
            first_condition = str(rule.conditions[0])
            condition_text = f"1 condition: {first_condition}"
        else:
            all_conditions = " and ".join(str(cond) for cond in rule.conditions)
            condition_text = f"{condition_count} conditions: {all_conditions}"

        operation_label = "operation" if operation_count == 1 else "operations"
        return f"{condition_text} → {operation_count} {operation_label}"

    @staticmethod
    def render(editor_rule: dict, display_index: int) -> None:
        rule = editor_rule["rule"]
        rule_id = editor_rule["id"]
        is_focused = st.session_state.focus_rule_id == rule_id

        rule_summary = RuleCardRenderer.format_rule_summary(rule)
        label = f"## #{display_index}\n**{rule_summary}**"

        with st.expander(label, expanded=is_focused or display_index == 1):

            # Build one YAML document
            rule_yaml = yaml.safe_dump(
                {
                    "conditions": [c.dict() for c in rule.conditions],
                    "operations": [o.dict() for o in rule.operations],
                },
                sort_keys=False,
                allow_unicode=True,
            )

            response = code_editor(
                rule_yaml,
                lang="yaml",
                theme="dark",
                shortcuts="vscode",
                height=400,
                key=f"rule_editor_{rule_id}",
                buttons=[
                    {
                        "name": "Save rule changes",
                        "feather": "Save",
                        "primary": True,
                        "alwaysOn": True,
                        "hasText": True,
                        "commands": ["submit"],
                        "style": {"top": "0.46rem", "right": "0.4rem"}
                    }
                ],
                props={
                    "tabSize": 2,
                    "useSoftTabs": True,
                    "showPrintMargin": False,
                    "wrap": True,
                },
                editor_props={
                    "tabSize": 2,
                    "useSoftTabs": True,
                    "showPrintMargin": False,
                    "wrap": True,
                },
            )

            # Handle save
            if response and response.get("type") == "submit":
                try:
                    parsed = yaml.safe_load(response["text"]) or {}

                    new_rule = Rule.parse_obj(
                        {
                            "conditions": parsed.get("conditions", []),
                            "operations": parsed.get("operations", []),
                            "tags": rule.tags,
                        }
                    )

                    editor_rule["rule"] = new_rule
                    RulesEditorState.refresh_parsed_from_editor()

                    st.session_state.status_message = "Saved rule changes"
                    st.session_state.status_type = "success"
                    render_status_message()

                except Exception as e:
                    st.error(str(e))

            # Action buttons
            col1, col2 = st.columns(2)

            with col1:
                if st.button("📋 Duplicate", key=f"duplicate_rule_{rule_id}"):
                    RuleOperations.duplicate_rule(rule_id)
                    st.session_state.focus_rule_id = None
                    st.session_state.status_message = "Duplicated rule"
                    st.session_state.status_type = "success"
                    st.rerun()

            with col2:
                if st.button("🗑️ Delete", key=f"delete_rule_{rule_id}"):
                    RuleOperations.delete_rule(rule_id)
                    st.session_state.status_message = "Deleted rule"
                    st.session_state.status_type = "success"
                    st.rerun()


class OverviewRenderer:
    """Renders the rules overview section."""

    @staticmethod
    def render(rules: BankConfiguration) -> None:
        if not rules.rules:
            st.info("📊 No rules to display yet.")
            return

        st.markdown(
            """
            <div class="overview-section">
                <div class="section-title">
                    <span class="section-title-icon">📊</span>
                    Overview
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        metric_data = [
            ("Total", len(rules.rules), "📝"),
        ]

        metric_cols = st.columns(4)
        for idx, (label, value, emoji) in enumerate(metric_data):
            with metric_cols[idx]:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <div class="metric-label">{emoji} {label}</div>
                        <div class="metric-value">{value}</div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )


class FileSelector:
    """Handles file selection UI."""

    @classmethod
    def render(cls,rule_files: list[Path]) -> Path | None:
        if not rule_files:
            st.warning("⚠️ No rules files found. Expected files like `*_bank_rules.yaml`.")
            return None

        # Map display names to full paths (show only filename in UI)
        name_to_path = {path.name: path for path in rule_files}
        options = list(name_to_path.keys())

        # keep selected filename in session for persistence
        selected_name = st.session_state.get("selected_file", options[0] if options else None)
        if selected_name not in options:
            selected_name = options[0] if options else None

        selected = st.sidebar.selectbox("📄 Rules file", options, index=options.index(selected_name))
        if selected != st.session_state.get("selected_file"):
            st.session_state.selected_file = selected  # store filename (not full path) for display elsewhere
            cls.load_selected_file(name_to_path[selected])
        return name_to_path[selected]

    @staticmethod
    def load_selected_file(file_path: Path) -> None:
        try:
            raw_yaml = FileManager.load_file_content(file_path)
            st.session_state.yaml_text = raw_yaml
            rules = YamlManager.parse_rules_yaml(raw_yaml)
            RulesEditorState.load_rules_into_editor(rules)
            st.session_state.active_tag_filter = []
            st.session_state.focus_rule_id = None
            st.session_state.scroll_to_top = False
            # keep only filename for the displayed badge
            st.session_state.selected_file = file_path.name
            st.session_state.status_message = f"Loaded {file_path.name}"
            st.session_state.status_type = "success"
        except Exception as exc:
            st.session_state.status_message = f"Invalid YAML: {exc}"
            st.session_state.status_type = "error"

class ScrollManager:
    """Handles scroll positioning."""

    @staticmethod
    def scroll_to_top_if_needed() -> None:
        if st.session_state.scroll_to_top:
            components.html(
                "<script>window.scrollTo({ top: 0, behavior: 'smooth' });</script>",
                height=0,
            )
            st.session_state.scroll_to_top = False


def render_status_message() -> None:
    """Render status message with appropriate styling."""
    if st.session_state.status_message:
        status_type = st.session_state.get("status_type", "info")
        status_class = f"status-{status_type}"
        emoji = "✅" if status_type == "success" else "❌" if status_type == "error" else "ℹ️"

        st.markdown(
            f"""
            <div class="status-badge {status_class}">
            {emoji} {st.session_state.status_message}
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_sidebar_controls(selected_file: Path | None) -> None:
    """Render sidebar control buttons and filters."""
    with st.sidebar:
        st.subheader("Actions")
        if selected_file and st.button("🔄 Reload"):
            FileSelector.load_selected_file(selected_file)
            st.rerun()

        if st.session_state.parsed_rules is not None:
            total_count = len(st.session_state.editor_rules)
            st.caption(f"**{total_count}** rules")

        render_status_message()


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, layout="wide")
    RulesEditorState.init_state()
    StyleManager.apply_page_styles()

    st.title(f"✏️ {APP_TITLE}")
    st.caption("Structured editor with tag filtering and YAML backup.")

    rule_files = FileManager.discover_rules_files(Path.cwd())
    selected_file = FileSelector.render(rule_files)

    render_sidebar_controls(selected_file)

    if selected_file and not st.session_state.yaml_text:
        FileSelector.load_selected_file(selected_file)

    if not st.session_state.yaml_text:
        st.info("📂 Select a rules file to get started.")
        return

    ScrollManager.scroll_to_top_if_needed()

    structured_tab, raw_tab = st.tabs(["Structured editor", "Raw YAML"])

    with structured_tab:
        st.subheader("✏️ Structured editor")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("➕ Add rule"):
                RuleOperations.add_blank_rule()
        with col2:
            if st.button("✔️ Validate"):
                try:
                    RulesEditorState.refresh_parsed_from_editor()
                    rule_count = len(st.session_state.parsed_rules.rules)
                    st.session_state.status_message = f"Valid • {rule_count} rule(s)"
                    st.session_state.status_type = "success"
                    st.rerun()
                except Exception as exc:
                    st.session_state.status_message = f"Invalid: {exc}"
                    st.session_state.status_type = "error"
        with col3:
            if st.button("💾 Save"):
                try:
                    RulesEditorState.refresh_parsed_from_editor()
                    selected_file.write_text(YamlManager.dump_rules_yaml(st.session_state.parsed_rules), encoding="utf-8")
                    st.session_state.status_message = f"Saved {selected_file.name}"
                    st.session_state.status_type = "success"
                    st.rerun()
                except Exception as exc:
                    st.session_state.status_message = f"Save failed: {exc}"
                    st.session_state.status_type = "error"

        visible_rules = st.session_state.editor_rules

        if not visible_rules:
            st.info("No rules match the current filter.")
        if not st.session_state.editor_rules:
            st.info("No rules yet. Click '➕ Add rule' to create one.")
        else:
            for display_index, editor_rule in enumerate(visible_rules, start=1):
                RuleCardRenderer.render(editor_rule, display_index)
                if st.session_state.focus_rule_id == editor_rule["id"]:
                    st.session_state.focus_rule_id = None

        if st.session_state.parsed_rules is not None:
            OverviewRenderer.render(st.session_state.parsed_rules)

    with raw_tab:
        st.subheader("📝 Raw YAML")
        code_editor(
            st.session_state.yaml_text,
            lang="yaml",
            theme="dark",
            shortcuts="vscode",
            key=f"yaml_text",
            props={
                "tabSize": 2,
                "useSoftTabs": True,
                "showPrintMargin": False,
                "wrap": True,
            },
            editor_props={
                "tabSize": 2,
                "useSoftTabs": True,
                "showPrintMargin": False,
                "wrap": True,
                "readOnly": True,
            },
        )


if __name__ == "__main__":
    main()