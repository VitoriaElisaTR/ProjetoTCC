# auth.py
import streamlit as st
import json
import os
import pandas as pd

try:
    import cx_Oracle
    _ORACLE_AVAILABLE = True
except ImportError:
    _ORACLE_AVAILABLE = False

from config.mock_db import mock_database_connection, mock_get_data, mock_insert_process

USERS_FILE = "data/users.json"

# controla qual backend está ativo: True = SQLite mock, False = Oracle
_USE_MOCK = False


def is_mock_mode():
    return _USE_MOCK


def database_conection(user_bd='admin', password_bd='admin', tns_bd='DKR_NAC_213'):
    global _USE_MOCK
    if _ORACLE_AVAILABLE and not _USE_MOCK:
        try:
            conn = cx_Oracle.connect(user=str(user_bd), password=str(password_bd), dsn=str(tns_bd))
            cursor = conn.cursor()
            return conn, cursor
        except Exception:
            pass
    # fallback SQLite
    _USE_MOCK = True
    return mock_database_connection(username=user_bd)


def get_data(query, cursor):
    global _USE_MOCK
    if _USE_MOCK:
        return mock_get_data(query, cursor)
    try:
        cursor.execute(query)
        results = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        df = pd.DataFrame(results, columns=columns)
        return df
    except Exception:
        return None
    

def make_db_highq_login(cursor):

    #script_dir = os.path.dirname(__file__)
    file_path = os.path.join('config/query.json')

    with open(file_path) as file:
        querys = json.load(file)

    
    df_login_user_data = get_data(querys['loginUserData'], cursor)
    df_user_bd = get_data(querys['userBD'], cursor)
    return df_login_user_data, df_user_bd


def make_db_register(cursor):

    #script_dir = os.path.dirname(__file__)
    file_path = os.path.join('config/query.json')

    with open(file_path) as file:
        querys = json.load(file)
    
    df_estados = get_data(querys['estadosBR'], cursor)
    df_class_process = get_data(querys['classProcess'], cursor)
    df_path_process = get_data(querys['pathProcess'], cursor)
    df_datajud_endpoints = get_data(querys['datajudEndpoints'], cursor)
    return df_estados, df_class_process, df_path_process, df_datajud_endpoints


def make_db_process(cursor):

    #script_dir = os.path.dirname(__file__)
    file_path = os.path.join('config/query.json')

    with open(file_path) as file:
        querys = json.load(file)
    
    df_process = get_data(querys['processJurid'], cursor)
    return df_process


def load_users():
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, "r") as f:
            return json.load(f)
    return {}


def save_users(users):
    with open(USERS_FILE, "w") as f:
        json.dump(users, f)


def login(username, password):
    conn, cursor = database_conection()
    df_login_user_data, df_user_bd = make_db_highq_login(cursor)
    password_bd = df_login_user_data[df_login_user_data['EMAIL'] == username]['LOGIN_PASSWORD'].reset_index(drop=True)[0]
    if username in df_login_user_data['EMAIL'].to_list() and password == password_bd:
        print("Usuário encontrado no banco de dados.")
        return True
    else: 
        print("Usuário ou senha inválidos.") 
        return False


def insert_user_data(conn, cursor, register_dict):
    sql = """
        INSERT INTO login_user_data(NAME, EMAIL, LOGIN_PASSWORD, NUM_OAB, USERNAME)
        VALUES (:1, :2, :3, :4, :5)
    """
    try:
        cursor.execute(sql, (register_dict['nome'], register_dict['email'], register_dict['senha'], register_dict['num_oab'], register_dict['username']))
        conn.commit()
    except Exception:
        st.toast("Erro ao tentar fazer cadastro de novo usuário!", icon="❌")
        return False
    return True


def insert_db_user(conn, cursor, register_bd_dict):
    sql = """
        INSERT INTO users(USERNAME, PASSWORD)
        VALUES (:1, :2)
    """
    try:
        cursor.execute(sql, (register_bd_dict['username'], register_bd_dict['password']))
        conn.commit()
    except Exception as e:
        print(f"Erro ao tentar inserir usuário no banco de dados: {e}")
        st.toast("Erro ao tentar fazer cadastro de novo usuário!", icon="❌")
        return False
    return True


def register(register_dict, register_bd_dict):
    conn, cursor = database_conection()
    status_insert_user_data = insert_user_data(conn, cursor, register_dict)
    status_db_user = insert_db_user(conn, cursor, register_bd_dict)
    if status_insert_user_data and status_db_user:
        return True
    else:
        st.toast("Erro ao tentar fazer cadastro de novo usuário!", icon="❌")
        return False


def register_new_password(email, new_password):
    conn, cursor = database_conection()
    status_new_password = update_new_password(conn, cursor, email, new_password)
    if status_new_password:
        return True
    else:
        return False


def update_new_password(conn, cursor, email, new_password):
    sql = """
        UPDATE login_user_data
        SET LOGIN_PASSWORD = :1
        WHERE EMAIL = :2
    """
    try:
        cursor.execute(sql, (new_password, email))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao tentar atualizar senha: {e}")
        return False


def update_user_data(conn, cursor, register_dict):
    sql = """
        UPDATE login_user_data
        SET NAME = :1, LOGIN_PASSWORD = :2, NUM_OAB = :3
        WHERE EMAIL = :4
    """
    try:
        cursor.execute(sql, (register_dict['nome'], register_dict['senha'], register_dict['oab'], register_dict['email']))
        conn.commit()
        return True
    except Exception as e:
        print(f"Erro ao tentar atualizar usuário: {e}")
        st.toast("Erro ao tentar fazer cadastro de novo usuário!", icon="❌")
        return False
    