import html
import streamlit as st


def safe_text(value):
    """
    Prevent HTML injection and safely display text.
    """

    if value is None:
        return ""

    return html.escape(str(value))


def card_title(title, subtitle=None):
    """
    Display a standard section heading.
    """

    st.markdown(f"### {title}")

    if subtitle:
        st.caption(subtitle)


def success_box(message):
    st.success(message)


def warning_box(message):
    st.warning(message)


def error_box(message):
    st.error(message)


def info_box(message):
    st.info(message)


def divider():
    st.markdown("---")


def empty_space(lines=1):

    for _ in range(lines):
        st.write("")
