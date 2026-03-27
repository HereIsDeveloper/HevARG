import discord
from discord import app_commands
import random
import string
import os
import asyncio
from flask import Flask
from threading import Thread

# --- 核心參數鏈路 ---
# 警告：TOKEN 必須在 Render 的 Environment Variables 設定為 DISCORD_TOKEN
TOKEN = os.getenv('DISCORD_TOKEN')
TARGET_ROLE_ID = 1487094611607556306
ADMIN_USER_ID = 1078656329645822042  # <--- 請在此處填入你的 Discord 使用者 ID (數字)
PROTOCOL_NAME = "EDCS-SDT / NULL-INPUT-MODE"

# --- 系統存活補償 (Flask Server) ---
app = Flask('')

@app.route('/')
def home():
    return "EDCS-SDT TERMINAL STATUS: ONLINE"

def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run_flask)
    t.daemon = True
    t.start()

# --- 終端核心實例 ---
class EdcsSecurityBot(discord.Client):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True          # 用於授予身分組
        intents.message_content = True   # 用於刪除普通訊息
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)
        self.active_channel_id = None
        self.user_keys = {}

    async def setup_hook(self):
        # 同步斜槓指令至 Discord 全域
        await self.tree.sync()

client = EdcsSecurityBot()

# --- EDCS-SDT 混沌擴散算法 (二次擾動) ---
SYMS = "ψξ∇∭∑ΓζφΞ⊥⊗∆⌈⌋ℵℶθ∏≈∞∰"

def edcs_sdt_encode(text: str, x0: float = 0.456123, r: float = 3.99) -> str:
    x = x0
    last_salt = 0
    out = ""
    for char in text:
        x = r * x * (1 - x)
        char_code = ord(char)
        # 二次擴散位移運算
        diffused = (char_code ^ int(x * 255)) + int(last_salt % 13)
        sym = SYMS[int(x * len(SYMS)) % len(SYMS)]
        hex_val = hex(diffused)[2:].upper()
        out += f"{sym}{hex_val}"
        last_salt = diffused
    return out

# --- 監控協議：非法數據抹除 ---
@client.event
async def on_message(message):
    if message.author == client.user:
        return

    # 若頻道已鎖定，刪除所有非指令訊息
    if client.active_channel_id and message.channel.id == client.active_channel_id:
        if not message.interaction:
            try:
                await message.delete()
            except discord.Forbidden:
                pass # 權限不足時忽略

# --- 指令集 (APP COMMANDS) ---

@client.tree.command(name="argstart", description="[ADMIN] 部署 EDCS-SDT 並開啟「零輸入」模式")
async def argstart(interaction: discord.Interaction):
    if interaction.user.id != ADMIN_USER_ID:
        await interaction.response.send_message("```[FATAL] 權限不足。存取遭拒。```", ephemeral=True)
        return

    client.active_channel_id = interaction.channel_id
    
    instructions = (
        f"```TERMINAL\n"
        f"協議啟動 : {PROTOCOL_NAME}\n"
        f"頻道監控 : ACTIVE / DELETE_NON_CMD\n"
        f"--------------------------------------------------\n"
        f"【互動協議說明】\n"
        f"1. 頻道已進入嚴格「零輸入」模式。\n"
        f"2. 輸入 /request 獲取唯一加密序列。\n"
        f"3. 根據 EDCS-SDT 邏輯逆向解構後獲取明文。\n"
        f"4. 使用 /decrypt [明文] 提交驗證。\n"
        f"--------------------------------------------------\n"
        f"[SYSTEM] 指令鏈路已就緒。\n"
        f"```"
    )
    await interaction.response.send_message(instructions)

@client.tree.command(name="request", description="[USER] 提取個人擴散加密序列")
async def request(interaction: discord.Interaction):
    if client.active_channel_id != interaction.channel_id:
        await interaction.response.send_message("```[ERROR] 區域未啟動。```", ephemeral=True)
        return

    # 生成 4 位大寫隨機碼
    raw_key = ''.join(random.choices(string.ascii_uppercase, k=4))
    encrypted_data = edcs_sdt_encode(raw_key)
    client.user_keys[interaction.user.id] = raw_key

    response = (
        f"```TERMINAL\n"
        f"[AUTH] 用戶識別碼: {interaction.user.id}\n"
        f"[DATA] 加密序列: {encrypted_data}\n"
        f"[TASK] 解構序列並回傳 4 位原始明文。\n"
        f"```"
    )
    await interaction.response.send_message(response, ephemeral=True)

@client.tree.command(name="decrypt", description="[USER] 提交解碼後的明文序列")
@app_commands.describe(key="輸入 4 位原始英文字元")
async def decrypt(interaction: discord.Interaction, key: str):
    user_id = interaction.user.id
    correct_key = client.user_keys.get(user_id)

    if not correct_key:
        await interaction.response.send_message("```[ERROR] 無當前存取紀錄。```", ephemeral=True)
        return

    if key.upper() == correct_key:
        role = interaction.guild.get_role(TARGET_ROLE_ID)
        if role:
            try:
                await interaction.user.add_roles(role)
                await interaction.response.send_message(
                    f"```TERMINAL\n"
                    f"[SUCCESS] 序列吻合。身份組授權成功。\n"
                    f"```", ephemeral=True
                )
                del client.user_keys[user_id]
            except Exception:
                await interaction.response.send_message("```[CRITICAL] 權限提升失敗。請檢查 Bot 角色權限層級。```", ephemeral=True)
        else:
            await interaction.response.send_message("```[CRITICAL] 目標身份組 ID 無效。```", ephemeral=True)
    else:
        await interaction.response.send_message("```[DENIED] 序列特徵錯誤。```", ephemeral=True)

@client.event
async def on_ready():
    print(f"[{PROTOCOL_NAME}] ONLINE / INTERFACE: {client.user.id}")

# --- 啟動程序 ---
if __name__ == "__main__":
    keep_alive()  # 開啟網頁心跳
    if TOKEN:
        client.run(TOKEN)
    else:
        print("[FATAL] 未偵測到 DISCORD_TOKEN 環境變數。系統終止。")
