import streamlit as st
import json

with open('chat.json', 'r', encoding='utf-8') as f:
    history = json.load(f)

for role_code, text in history:
    role = "user" if role_code == 'u' else "assistant"
    
    with st.chat_message(role):
        st.markdown(text)