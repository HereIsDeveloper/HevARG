import discord
from discord import app_commands
import random
import string
import os
from flask import Flask
from threading import Thread

# --- 系統參數配置 ---
# 注意：Token 現已改為從 Render 的環境變數讀取，確保安全性
TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_ROLE_ID = 1487094611607556306
ADMIN_USER_ID = 0000000000000000  # 替換為你的管理員 ID
PROTOCOL_NAME = "EDCS-SDT / NULL-INPUT-MODE"

# --- WEB SERVER 存活機制 (繞過休眠) ---
app = Flask('')

@app.route('/')
def home():
    return "EDCS-SDT TERMINAL IS ACTIVE."

def run():
    # Render 自動分配 PORT，若無則預設 8080
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- BOT 核心實例 ---
class EdcsSecurityBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True
        intents.message_content = True 
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active_channel_id = None
        self.user_keys = {}

    async def setup_hook(self):
        await self.tree.sync()

client = EdcsSecurityBot()

# --- EDCS-SDT 混沌擴散算法 ---
SYMS = "ψξ∇∭∑ΓζφΞ⊥⊗∆⌈⌋ℵℶθ∏≈∞∰"

def edcs_sdt_encode(text: str, x0: float = 0.456123, r: float = 3.99) -> str:
    x = x0
    last_salt = 0
    out = ""
    for char in text:
        x = r * x * (1 - x)
        char_code = ord(char)
        diffused = (char_code ^ int(x * 255)) + int(last_salt % 13)
        sym = SYMS[int(x * len(SYMS)) % len(SYMS)]
        hex_val = hex(diffused)[2:].upper()
        out += f"{sym}{hex_val}"
        last_salt = diffused
    return out

# --- 頻道肅清過濾器 ---
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if client.active_channel_id and message.channel.id == client.active_channel_id:
        if not message.interaction:
            try:
                await message.delete()
            except discord.Forbidden:
                print("[SYSTEM ERROR] 權限不足，無法執行清除協議。")

# --- 指令系統 ---
@client.tree.command(name="argstart", description="[ADMIN] 部署 EDCS-SDT 並開啟「零輸入」模式")
async def argstart(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("```[FATAL] 權限不足。存取遭拒。```", ephemeral=True)
        return

    client.active_channel_id = interaction.channel_id
    
    instructions = (
        f"```TERMINAL\n"
        f"協議啟動 : {PROTOCOL_NAME}\n"
        f"當前狀態 : 執行中 (RUNNING)\n"
        f"頻道監控 : ACTIVE / DELETE_NON_CMD\n"
        f"--------------------------------------------------\n"
        f"【互動協議說明】\n"
        f"1. 頻道進入「零輸入」模式，無關數據將遭抹除。\n"
        f"2. 輸入 /request 提取加密序列。\n"
        f"3. 逆向解構後獲取明文。\n"
        f"4. 使用 /decrypt [明文] 提交驗證。\n"
        f"--------------------------------------------------\n"
        f"[SYSTEM] 終端就緒。\n"
        f"```"
    )
    await interaction.response.send_message(instructions)

@client.tree.command(name="request", description="[USER] 提取個人擴散加密序列")
async def request(interaction: discord.Interaction):
    if client.active_channel_id != interaction.channel_id:
        await interaction.response.send_message("```[ERROR] 區域未初始化。```", ephemeral=True)
        return

    raw_key = ''.join(random.choices(string.ascii_uppercase, k=4))
    encrypted_data = edcs_sdt_encode(raw_key)
    client.user_keys[interaction.user.id] = raw_key

    response = (
        f"```TERMINAL\n"
        f"[AUTH] 用戶: {interaction.user.name}\n"
        f"[DATA] 受控序列: {encrypted_data}\n"
        f"[TASK] 逆向解構並回傳明文。\n"
        f"```"
    )
    await interaction.response.send_message(response, ephemeral=True)

@client.tree.command(name="decrypt", description="[USER] 提交解構明文")
async def decrypt(interaction: discord.Interaction, key: str):
    user_id = interaction.user.id
    correct_key = client.user_keys.get(user_id)

    if not correct_key:
        await interaction.response.send_message("```[ERROR] 無存取紀錄。```", ephemeral=True)
        return

    if key.upper() == correct_key:
        role = interaction.guild.get_role(TARGET_ROLE_ID)
        if role:
            await interaction.user.add_roles(role)
            await interaction.response.send_message(
                f"```TERMINAL\n"
                f"[SUCCESS] 序列吻合。身份組 {TARGET_ROLE_ID} 已授權。\n"
                f"```", ephemeral=True
            )
            del client.user_keys[user_id]
        else:
            await interaction.response.send_message("```[CRITICAL] 目標權限組丟失。```", ephemeral=True)
    else:
        await interaction.response.send_message("```[DENIED] 序列特徵不符。```", ephemeral=True)

@client.event
async def on_ready():
    print(f"[ONLINE] {PROTOCOL_NAME} 系統監控中...")

# --- 啟動程序 ---
if __name__ == "__main__":
    keep_alive()  # 啟動 Flask 偽裝伺服器
    if TOKEN:
        client.run(TOKEN)
    else:
        print("[FATAL] 系統啟動失敗：未配置 DISCORD_TOKEN 環境變數。")