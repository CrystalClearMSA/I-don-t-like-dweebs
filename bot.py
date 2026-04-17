import discord
from discord.ext import commands
import json
import os

# ── Config ────────────────────────────────────────────────────────────────────
PREFIX = "!"
DATA_FILE = "kicklist.json"  # persists kick list between restarts

# ── Persistence ───────────────────────────────────────────────────────────────
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            return set(data.get("ids", [])), data.get("enabled", True)
    return set(), True

def save_data(ids: set, enabled: bool):
    with open(DATA_FILE, "w") as f:
        json.dump({"ids": list(ids), "enabled": enabled}, f, indent=2)

# ── Bot setup ─────────────────────────────────────────────────────────────────
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix=PREFIX, intents=intents)

kick_ids, auto_kick_enabled = load_data()

# ── Events ────────────────────────────────────────────────────────────────────
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print(f"Auto-kick: {'ON' if auto_kick_enabled else 'OFF'} | Watching {len(kick_ids)} ID(s)")

@bot.event
async def on_member_join(member: discord.Member):
    if not auto_kick_enabled:
        return
    if member.id in kick_ids:
        try:
            await member.send("go away")
        except (discord.Forbidden, discord.HTTPException):
            pass  # user has DMs disabled, kick anyway
        try:
            await member.kick(reason="Auto-kick: ID on blocklist")
            print(f"Kicked {member} ({member.id}) on join")
        except discord.Forbidden:
            print(f"Missing permissions to kick {member} ({member.id})")
        except discord.HTTPException as e:
            print(f"Failed to kick {member}: {e}")

# ── Commands ──────────────────────────────────────────────────────────────────
@bot.command(name="addkick")
@commands.has_permissions(kick_members=True)
async def add_kick(ctx, user_id: int):
    """!addkick <user_id> — Add an ID to the auto-kick list."""
    global kick_ids
    if user_id in kick_ids:
        await ctx.send(f"`{user_id}` is already on the list.")
        return
    kick_ids.add(user_id)
    save_data(kick_ids, auto_kick_enabled)
    await ctx.send(f"Added `{user_id}` to the auto-kick list. ({len(kick_ids)} total)")

@bot.command(name="removekick")
@commands.has_permissions(kick_members=True)
async def remove_kick(ctx, user_id: int):
    """!removekick <user_id> — Remove an ID from the auto-kick list."""
    global kick_ids
    if user_id not in kick_ids:
        await ctx.send(f"`{user_id}` is not on the list.")
        return
    kick_ids.discard(user_id)
    save_data(kick_ids, auto_kick_enabled)
    await ctx.send(f"Removed `{user_id}` from the auto-kick list. ({len(kick_ids)} remaining)")

@bot.command(name="listkicks")
@commands.has_permissions(kick_members=True)
async def list_kicks(ctx):
    """!listkicks — Show all IDs currently on the auto-kick list."""
    if not kick_ids:
        await ctx.send("Auto-kick list is empty.")
        return
    formatted = "\n".join(f"• `{uid}`" for uid in sorted(kick_ids))
    await ctx.send(f"**Auto-kick list ({len(kick_ids)}):**\n{formatted}")

@bot.command(name="togglekick")
@commands.has_permissions(kick_members=True)
async def toggle_kick(ctx):
    """!togglekick — Enable or disable auto-kick without clearing the list."""
    global auto_kick_enabled
    auto_kick_enabled = not auto_kick_enabled
    save_data(kick_ids, auto_kick_enabled)
    state = "**ON**" if auto_kick_enabled else "**OFF**"
    await ctx.send(f"Auto-kick is now {state}.")

@bot.command(name="kickstatus")
@commands.has_permissions(kick_members=True)
async def kick_status(ctx):
    """!kickstatus — Show current state of the auto-kick system."""
    state = "ON" if auto_kick_enabled else "OFF"
    await ctx.send(f"Auto-kick: **{state}** | IDs on list: **{len(kick_ids)}**")

# ── Error handling ────────────────────────────────────────────────────────────
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.send("You need **Kick Members** permission to use this.")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("That doesn't look like a valid user ID (must be a number).")
    elif isinstance(error, commands.CommandNotFound):
        pass  # silently ignore unknown commands
    else:
        raise error

# ── Run ───────────────────────────────────────────────────────────────────────
TOKEN = os.environ.get("DISCORD_BOT_TOKEN", "MTQ5NDYwNTg4OTk3NjQwMTk3MA.GLMka0.Lgfs1ppzDwdpEp1h1uCnB8sfWbCNiG7DcU9Y60")

bot.run(TOKEN)
