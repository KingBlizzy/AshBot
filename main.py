import discord
from discord.ext import commands
import random
import sqlite3

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix=".", intents=intents)

# Initialize SQLite database
conn = sqlite3.connect("balances.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, balance INTEGER)")
conn.commit()

def get_balance(user_id):
    cursor.execute("SELECT balance FROM users WHERE id = ?", (user_id,))
    result = cursor.fetchone()
    if result:
        return result[0]
    else:
        cursor.execute("INSERT INTO users (id, balance) VALUES (?, 0)", (user_id,))
        conn.commit()
        return 0

def set_balance(user_id, balance):
    cursor.execute("INSERT OR REPLACE INTO users (id, balance) VALUES (?, ?)", (user_id, balance))
    conn.commit()

@bot.event
async def on_ready():
    print(f"Logged in as {bot.user}")

@bot.command()
async def bal(ctx, member: discord.Member = None):
    member = member or ctx.author
    balance = get_balance(member.id)
    if member == ctx.author:
        await ctx.send(f"You have {balance} coins.")
    else:
        await ctx.send(f"{member.display_name} has {balance} coins.")

@bot.command()
async def pay(ctx, member: discord.Member, amount: int):
    if amount <= 0:
        await ctx.send("Amount must be greater than zero.")
        return

    sender_balance = get_balance(ctx.author.id)
    if sender_balance < amount:
        await ctx.send("You do not have enough coins.")
        return

    receiver_balance = get_balance(member.id)
    set_balance(ctx.author.id, sender_balance - amount)
    set_balance(member.id, receiver_balance + amount)
    await ctx.send(f"Transferred {amount} coins to {member.display_name}.")

@bot.command()
async def bet(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Bet amount must be greater than zero.")
        return

    balance = get_balance(ctx.author.id)
    if balance < amount:
        await ctx.send("You do not have enough coins.")
        return

    roll = random.randint(1, 100)
    if roll <= 45:
        new_balance = balance - amount
        result = f"You lost {amount} coins. Your balance is {new_balance} coins."
    elif roll <= 95:
        new_balance = balance + amount
        result = f"You won {amount} coins. Your balance is {new_balance} coins."
    else:
        new_balance = balance + amount * 2
        result = f" You won {amount * 2} coins. Your balance is {new_balance} coins."

    set_balance(ctx.author.id, new_balance)
    await ctx.send(result)

@bot.command()
async def baltop(ctx):
    cursor.execute("SELECT id, balance FROM users ORDER BY balance DESC LIMIT 10")
    top_users = cursor.fetchall()
    leaderboard = []
    for idx, (user_id, balance) in enumerate(top_users, 1):
        user = await bot.fetch_user(user_id)
        leaderboard.append(f"{idx}. {user.name} - {balance} coins")
    await ctx.send("**Top 10 Wealthiest Users:**\n" + "\n".join(leaderboard))

bot.run("_INSERT_BOT_TOKEN_HERE_")
