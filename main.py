import streamlit as st
import mysql.connector
from mysql.connector import Error
import hashlib

def create_connection():
    return mysql.connector.connect(
        host='localhost',
        database='users_auth',
        user='root',  # Ganti dengan user MySQL Anda
        password=''   # Ganti dengan password MySQL Anda
    )

def create_user(username, password):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_password))
        connection.commit()
        cursor.close()
        connection.close()
    except Error as e:
        st.error(f"Error: {e}")

def login_user(username, password):
    try:
        connection = create_connection()
        cursor = connection.cursor()
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE username = %s AND password = %s", (username, hashed_password))
        user = cursor.fetchone()
        cursor.close()
        connection.close()
        return user
    except Error as e:
        st.error(f"Error: {e}")
        return None

def register():
    st.subheader("Register")
    username = st.text_input("Username", key="register_username")
    password = st.text_input("Password", type="password", key="register_password")
    if st.button("Register"):
        create_user(username, password)
        st.success("Registration successful!")

def login():
    st.subheader("Login")
    username = st.text_input("Username", key="login_username")
    password = st.text_input("Password", type="password", key="login_password")
    if st.button("Login"):
        user = login_user(username, password)
        if user:
            st.success("Login successful!")
        else:
            st.error("Invalid username or password")

def main():
    st.title("User Authentication System")
    menu = ["Login", "Register"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Register":
        register()
    elif choice == "Login":
        login()

if __name__ == '_main_':
    main()