import datetime
import json
import os
import time
from typing import Optional

import discord
import discord.ext
import discord.ext.commands
import pytz
from utils.loadconfig import load_config

config = load_config()
FILENAME = config['Economy']['EconomyPath']

def load_data():
    if os.path.exists(FILENAME):
        with open(FILENAME, 'r') as file:
            data = json.load(file)
            return data
    else:
        with open(FILENAME, 'w') as file:
            json.dump({}, file, indent=4)
        return {}

def save_data(data):
    with open(FILENAME, 'w') as file:
        json.dump(data, file, indent=4)

def limit_number(amount: float) -> float:
  return round(amount, 2)

def register_user(user_id: str) -> None:
    data = load_data()
    if user_id not in data:
        data[user_id] = {
            "money": 0,
            "transactions": [],
            "last_daily_claim": 0
        }
        save_data(data)

def is_user_registered(user_id: str) -> bool:
    data = load_data()
    return bool(user_id in data)

def pay_money(user_id: str, receiver_id: str, amount: float) -> bool:
    data = load_data()
    if user_id not in data or receiver_id not in data:
        return False
    if data[user_id]["money"] < amount:
        return False

    data[user_id]["money"] -= limit_number(amount)
    data[receiver_id]["money"] += limit_number(amount)
    save_data(data)
    add_transaction(str(user_id), "Pix", -amount, None)
    add_transaction(str(receiver_id), "Pix", amount, str(user_id))
    return True

def add_money(user_id: str, amount: float) -> None:
    data = load_data()
    if user_id in data:
        data[user_id]["money"] += limit_number(amount)
        save_data(data)

def remove_money(user_id: str, amount: float) -> None:
    data = load_data()
    if user_id in data and data[user_id]["money"] >= amount:
        data[user_id]["money"] -= limit_number(amount)
        save_data(data)

def set_money(user_id: str, amount: float) -> None:
    data = load_data()
    if user_id in data:
        data[user_id]["money"] = limit_number(amount)
        save_data(data)

def get_money(user_id: str)-> float:
    data = load_data()
    if user_id in data:
        return data[user_id]["money"]
    return None

def get_money_daily(user_id: str, amount: float) -> bool:
    data = load_data()
    current_time = int(time.time())
    if user_id in data:
        if current_time - data[user_id]["last_daily_claim"] >= 86400:
            data[user_id]["money"] += limit_number(amount)
            data[user_id]["last_daily_claim"] = current_time
            save_data(data)
            add_transaction(user_id, "Daily claim", amount, None)
            return True
    return False

def add_transaction(user_id: str, transaction_type: str, amount: float, from_id: Optional[str]) -> None:
    data = load_data()
    if user_id in data:
        transaction = {
            "timestamp": int(datetime.datetime.now().timestamp()),
            "type": transaction_type,
            "amount": amount,
            "from": from_id if from_id else None
        }
        data[user_id]["transactions"].append(transaction)
        save_data(data)

def remove_transaction(user_id: str, index: int) -> None:
    data = load_data()
    if user_id in data and 0 <= index < len(data[user_id]["transactions"]):
        data[user_id]["transactions"].pop(index)
        save_data(data)

def get_transactions(user_id: str, bot: discord.ext.commands.Bot):
    data = load_data()
    if user_id in data:
        # Fuso horário de Brasília (UTC-3)
        brasilia_tz = pytz.timezone('America/Sao_Paulo')
        
        # Retorna as transações como uma string formatada para melhor visualização
        text = "\n".join([
            # Define o valor e o emoji dentro do loop
            f"{'💳' if str(t['amount']).startswith('-') else '💰'} | Tipo: {t['type']} | Valor: {t['amount']} {f'| De: {bot.get_user(int(t['from'])).name}' if t['from'] is not None else ''} | "
            f"Data: {datetime.datetime.fromtimestamp(t['timestamp'], tz=pytz.utc).astimezone(brasilia_tz).strftime('%Y-%m-%d %H:%M:%S')}\n"
            for t in reversed(data[user_id]["transactions"])
        ])
        return text
    return "Nenhuma transação encontrada."
