# ========== main.py ==========
import discord
from discord.ext import commands
import os
from flask import Flask
from threading import Thread

# Serveur Flask pour garder le bot en ligne sur Render
app = Flask('')

@app.route('/')
def home():
    return "Bot Discord en ligne ! 🤖"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# Configuration du bot
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Stockage des configurations
config = {}

@bot.event
async def on_ready():
    print(f'✅ {bot.user} est connecté !')
    await bot.change_presence(activity=discord.Game(name="!help"))

# Événement quand un membre rejoint
@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    
    if guild_id not in config or 'channel_id' not in config[guild_id]:
        return
    
    channel = bot.get_channel(config[guild_id]['channel_id'])
    if not channel:
        return
    
    emoji = config[guild_id].get('emoji', '👋')
    message = f"{emoji} Bienvenue {member.mention}\n{emoji} Nous sommes {member.guild.member_count} membres"
    
    await channel.send(message)

# Commande !help
@bot.command(name='help')
async def help_command(ctx):
    help_message = """**📋 Liste des commandes :**

**Configuration :**
**!config <#salon> <emoji>** - Configure le message de bienvenue
*Exemple : !config #bienvenue 🎉*

**Modération :**
**!kick <@membre> [raison]** - Expulse un membre
**!ban <@membre> [raison]** - Bannit un membre
**!unban <ID>** - Débannit un membre
**!mute <@membre> <durée> [raison]** - Mute un membre (ex: 10m, 1h, 1d)
**!unmute <@membre>** - Unmute un membre
**!clear <nombre>** - Supprime des messages (max 100)
**!lock** - Verrouille le salon
**!unlock** - Déverrouille le salon

**!help** - Affiche ce message"""
    
    await ctx.reply(help_message)

# Commande !config
@bot.command(name='config')
@commands.has_permissions(administrator=True)
async def config_command(ctx, channel: discord.TextChannel = None, emoji: str = '👋'):
    if not channel:
        await ctx.reply('❌ Utilisation : `!config #salon emoji`\nExemple : `!config #bienvenue 🎉`')
        return
    
    guild_id = str(ctx.guild.id)
    config[guild_id] = {
        'channel_id': channel.id,
        'emoji': emoji
    }
    
    await ctx.reply(f'✅ Configuration sauvegardée !\n📍 Salon : {channel.mention}\n😀 Emoji : {emoji}')

@config_command.error
async def config_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu dois être administrateur pour utiliser cette commande !')

# Commande !lock
@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
        await ctx.reply('🔒 Salon verrouillé !')
    except:
        await ctx.reply('❌ Erreur lors du verrouillage du salon.')

@lock.error
async def lock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de gérer les salons !')

# Commande !unlock
@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    try:
        await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
        await ctx.reply('🔓 Salon déverrouillé !')
    except:
        await ctx.reply('❌ Erreur lors du déverrouillage du salon.')

@unlock.error
async def unlock_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de gérer les salons !')

# Commande !kick
@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply('❌ Utilisation : `!kick @membre [raison]`')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.reply('❌ Tu ne peux pas kick ce membre (rôle supérieur ou égal) !')
        return
    
    try:
        await member.kick(reason=reason)
        await ctx.reply(f'✅ {member.mention} a été expulsé !\n📝 Raison : {reason or "Aucune raison"}')
    except:
        await ctx.reply('❌ Erreur lors de l\'expulsion.')

@kick.error
async def kick_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission d\'expulser des membres !')

# Commande !ban
@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply('❌ Utilisation : `!ban @membre [raison]`')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.reply('❌ Tu ne peux pas ban ce membre (rôle supérieur ou égal) !')
        return
    
    try:
        await member.ban(reason=reason)
        await ctx.reply(f'🔨 {member.mention} a été banni !\n📝 Raison : {reason or "Aucune raison"}')
    except:
        await ctx.reply('❌ Erreur lors du bannissement.')

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de bannir des membres !')

# Commande !unban
@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int = None):
    if not user_id:
        await ctx.reply('❌ Utilisation : `!unban <ID_utilisateur>`')
        return
    
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.reply(f'✅ {user.name} a été débanni !')
    except discord.NotFound:
        await ctx.reply('❌ Cet utilisateur n\'est pas banni ou ID incorrect.')
    except:
        await ctx.reply('❌ Erreur lors du débannissement.')

@unban.error
async def unban_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de débannir des membres !')

# Commande !mute
@bot.command(name='mute')
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member = None, duration: str = None, *, reason=None):
    if not member or not duration:
        await ctx.reply('❌ Utilisation : `!mute @membre <durée> [raison]`\nExemple : `!mute @User 10m spam`\nDurées : 10s, 5m, 1h, 1d')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.reply('❌ Tu ne peux pas mute ce membre (rôle supérieur ou égal) !')
        return
    
    # Convertir la durée
    time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    try:
        amount = int(duration[:-1])
        unit = duration[-1]
        seconds = amount * time_units.get(unit, 0)
        
        if seconds == 0 or seconds > 2419200:  # Max 28 jours
            await ctx.reply('❌ Durée invalide ! Utilise : 10s, 5m, 1h, 1d (max 28j)')
            return
        
        await member.timeout(discord.utils.utcnow() + discord.timedelta(seconds=seconds), reason=reason)
        await ctx.reply(f'🔇 {member.mention} a été mute pendant {duration} !\n📝 Raison : {reason or "Aucune raison"}')
    except:
        await ctx.reply('❌ Erreur lors du mute.')

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de timeout des membres !')

# Commande !unmute
@bot.command(name='unmute')
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member = None):
    if not member:
        await ctx.reply('❌ Utilisation : `!unmute @membre`')
        return
    
    try:
        await member.timeout(None)
        await ctx.reply(f'🔊 {member.mention} a été unmute !')
    except:
        await ctx.reply('❌ Erreur lors du unmute.')

@unmute.error
async def unmute_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de retirer les timeouts !')

# Commande !clear
@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = None):
    if not amount:
        await ctx.reply('❌ Utilisation : `!clear <nombre>`\nExemple : `!clear 10`')
        return
    
    if amount < 1 or amount > 100:
        await ctx.reply('❌ Tu peux supprimer entre 1 et 100 messages !')
        return
    
    try:
        deleted = await ctx.channel.purge(limit=amount + 1)
        msg = await ctx.send(f'✅ {len(deleted) - 1} messages supprimés !')
        await msg.delete(delay=3)
    except:
        await ctx.reply('❌ Erreur lors de la suppression des messages.')

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.MissingPermissions):
        await ctx.reply('❌ Tu n\'as pas la permission de gérer les messages !')

# Lancement du bot
if __name__ == "__main__":
    print("🚀 Démarrage du bot...")
    token = os.getenv('TOKEN')
    
    if not token:
        print("❌ ERREUR: Le TOKEN n'est pas configuré dans les variables d'environnement !")
        print("Va sur Render → Environment → Ajoute TOKEN = ton_token_discord")
        exit(1)
    
    print("✅ TOKEN détecté")
    print("🌐 Démarrage du serveur Flask...")
    keep_alive()
    print("🤖 Connexion à Discord...")
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ ERREUR lors de la connexion: {e}")
        exit(1)



