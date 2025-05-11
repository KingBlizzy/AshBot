import discord
from discord.ext import commands
import random
import sqlite3
import os

TOKEN = os.getenv("TOKEN")
WIN_CHANCE = 0.45
THREE_X_CHANCE = 0.1
STARTING_BALANCE = 1000

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix=".", intents=intents)

conn = sqlite3.connect("balances.db")
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS balances (
        user_id INTEGER PRIMARY KEY,
        balance INTEGER
    )
''')
conn.commit()

def get_balance(user_id):
    c.execute("SELECT balance FROM balances WHERE user_id = ?", (user_id,))
    result = c.fetchone()
    if result:
        return result[0]
    else:
        c.execute("INSERT INTO balances (user_id, balance) VALUES (?, ?)", (user_id, STARTING_BALANCE))
        conn.commit()
        return STARTING_BALANCE

def update_balance(user_id, new_balance):
    c.execute("UPDATE balances SET balance = ? WHERE user_id = ?", (new_balance, user_id))
    conn.commit()

@bot.command()
async def bet(ctx, amount: int):
    user_id = ctx.author.id
    balance = get_balance(user_id)

    if amount <= 0:
        return await ctx.send(embed=discord.Embed(description="❌ Bet must be more than 0.", color=0xFF0000))
    if balance < amount:
        return await ctx.send(embed=discord.Embed(description="❌ Not enough balance.", color=0xFF0000))

    win = random.random() < WIN_CHANCE
    three_x = win and (random.random() < THREE_X_CHANCE)

    if win:
        winnings = amount * (3 if three_x else 2)
        new_balance = balance + winnings - amount
        description = f"You won {winnings} coins. Your balance is {new_balance}."
        color = 0x00FF00
    else:
        new_balance = balance - amount
        description = f"You lost {amount} coins. Your balance is {new_balance}."
        color = 0xFF0000

    update_balance(user_id, new_balance)
    embed = discord.Embed(title="🎲 Bet Result", description=description, color=color)
    await ctx.send(embed=embed)

@bot.command()
async def bal(ctx, member: discord.Member = None):
    member = member or ctx.author
    balance = get_balance(member.id)
    embed = discord.Embed(title=f"💰 {member.display_name}'s Balance", description=f"{balance} coins", color=0x3498DB)
    await ctx.send(embed=embed)

@bot.command()
async def baltop(ctx):
    c.execute("SELECT user_id, balance FROM balances ORDER BY balance DESC LIMIT 10")
    top = c.fetchall()
    embed = discord.Embed(title="🏆 Top 10 Balances", color=0xFFD700)
    for i, (uid, bal) in enumerate(top, start=1):
        try:
            user = await bot.fetch_user(uid)
            embed.add_field(name=f"{i}. {user.name}", value=f"{bal} coins", inline=False)
        except:
            embed.add_field(name=f"{i}. Unknown User", value=f"{bal} coins", inline=False)
    await ctx.send(embed=embed)

@bot.command()
async def pay(ctx, amount: int, recipient: discord.Member):
    sender_id = ctx.author.id
    recipient_id = recipient.id
    sender_balance = get_balance(sender_id)

    if amount <= 0:
        return await ctx.send(embed=discord.Embed(description="❌ Amount must be greater than 0.", color=0xFF0000))
    if sender_balance < amount:
        return await ctx.send(embed=discord.Embed(description="❌ Not enough balance.", color=0xFF0000))

    recipient_balance = get_balance(recipient_id)
    update_balance(sender_id, sender_balance - amount)
    update_balance(recipient_id, recipient_balance + amount)

    embed = discord.Embed(title="💸 Payment Sent", description=f"You sent {amount} coins to {recipient.display_name}. Your new balance is {sender_balance - amount}.", color=0x00FF00)
    await ctx.send(embed=embed)
