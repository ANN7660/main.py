# ========== main.py ==========
import discord
from discord.ext import commands
from discord import app_commands
import os
from flask import Flask
from threading import Thread
import json

# Serveur Flask pour Render
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
intents = discord.Intents.all()
bot = commands.Bot(command_prefix='!', intents=intents, help_command=None)

# Stockage des configurations
server_configs = {}
questionnaire_responses = {}

# Vue pour le menu de configuration
class ConfigView(discord.ui.View):
    def __init__(self, guild_id):
        super().__init__(timeout=300)
        self.guild_id = guild_id
        
    @discord.ui.select(
        placeholder="🏠 Choisir le salon de bienvenue",
        min_values=1,
        max_values=1,
        custom_id="welcome_channel"
    )
    async def select_welcome_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        server_configs[self.guild_id]['welcome_channel'] = int(select.values[0])
        await interaction.response.send_message(f"✅ Salon de bienvenue configuré : <#{select.values[0]}>", ephemeral=True)
    
    @discord.ui.select(
        placeholder="📝 Choisir le salon de logs",
        min_values=1,
        max_values=1,
        custom_id="log_channel"
    )
    async def select_log_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        server_configs[self.guild_id]['log_channel'] = int(select.values[0])
        await interaction.response.send_message(f"✅ Salon de logs configuré : <#{select.values[0]}>", ephemeral=True)
    
    @discord.ui.select(
        placeholder="👤 Choisir le rôle auto",
        min_values=1,
        max_values=1,
        custom_id="auto_role"
    )
    async def select_auto_role(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        server_configs[self.guild_id]['auto_role'] = int(select.values[0])
        await interaction.response.send_message(f"✅ Rôle automatique configuré : <@&{select.values[0]}>", ephemeral=True)
    
    @discord.ui.button(label="✅ Activer le questionnaire", style=discord.ButtonStyle.green, custom_id="toggle_questionnaire")
    async def toggle_questionnaire(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        
        current = server_configs[self.guild_id].get('questionnaire_enabled', False)
        server_configs[self.guild_id]['questionnaire_enabled'] = not current
        
        if not current:
            button.label = "❌ Désactiver le questionnaire"
            button.style = discord.ButtonStyle.red
            await interaction.response.send_message("✅ Questionnaire activé !", ephemeral=True)
        else:
            button.label = "✅ Activer le questionnaire"
            button.style = discord.ButtonStyle.green
            await interaction.response.send_message("❌ Questionnaire désactivé !", ephemeral=True)
        
        await interaction.message.edit(view=self)

# Questionnaire pour les nouveaux membres
class QuestionnaireModal(discord.ui.Modal, title="📋 Questionnaire d'arrivée"):
    gender = discord.ui.TextInput(
        label="Genre",
        placeholder="Homme / Femme / Autre",
        required=True,
        max_length=20
    )
    
    age = discord.ui.TextInput(
        label="Âge",
        placeholder="Votre âge",
        required=True,
        max_length=3
    )
    
    interests = discord.ui.TextInput(
        label="Centres d'intérêt",
        placeholder="Gaming, musique, sport...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=200
    )
    
    reason = discord.ui.TextInput(
        label="Pourquoi rejoins-tu ce serveur ?",
        placeholder="...",
        required=False,
        style=discord.TextStyle.paragraph,
        max_length=300
    )
    
    async def on_submit(self, interaction: discord.Interaction):
        guild_id = str(interaction.guild.id)
        user_id = str(interaction.user.id)
        
        # Stocker les réponses
        if guild_id not in questionnaire_responses:
            questionnaire_responses[guild_id] = {}
        
        questionnaire_responses[guild_id][user_id] = {
            'gender': self.gender.value,
            'age': self.age.value,
            'interests': self.interests.value,
            'reason': self.reason.value
        }
        
        # Log les réponses
        if guild_id in server_configs and 'log_channel' in server_configs[guild_id]:
            log_channel = interaction.guild.get_channel(server_configs[guild_id]['log_channel'])
            if log_channel:
                embed = discord.Embed(title="📋 Nouveau questionnaire", color=discord.Color.blue())
                embed.add_field(name="Membre", value=f"{interaction.user.mention} ({interaction.user})", inline=False)
                embed.add_field(name="Genre", value=self.gender.value, inline=True)
                embed.add_field(name="Âge", value=self.age.value, inline=True)
                embed.add_field(name="Centres d'intérêt", value=self.interests.value or "Non renseigné", inline=False)
                embed.add_field(name="Raison", value=self.reason.value or "Non renseigné", inline=False)
                embed.timestamp = discord.utils.utcnow()
                await log_channel.send(embed=embed)
        
        await interaction.response.send_message("✅ Merci d'avoir complété le questionnaire ! Bienvenue sur le serveur 🎉", ephemeral=True)

@bot.event
async def on_ready():
    print(f'✅ {bot.user} est connecté !')
    await bot.change_presence(activity=discord.Game(name="!help | !config"))

@bot.event
async def on_member_join(member):
    guild_id = str(member.guild.id)
    
    # Message de bienvenue
    if guild_id in server_configs and 'welcome_channel' in server_configs[guild_id]:
        channel = bot.get_channel(server_configs[guild_id]['welcome_channel'])
        if channel:
            emoji = server_configs[guild_id].get('emoji', '<a:arrow:1441923828631470170>')
            message = f"{emoji} Bienvenue {member.mention}\n{emoji} Nous sommes maintenant {member.guild.member_count} membres"
            await channel.send(message)
    
    # Rôle automatique
    if guild_id in server_configs and 'auto_role' in server_configs[guild_id]:
        role = member.guild.get_role(server_configs[guild_id]['auto_role'])
        if role:
            await member.add_roles(role)
    
    # Questionnaire
    if guild_id in server_configs and server_configs[guild_id].get('questionnaire_enabled', False):
        try:
            await member.send("👋 Bienvenue ! Merci de compléter ce questionnaire pour accéder au serveur :")
            await member.send(view=QuestionnaireButton())
        except:
            pass
    
    # Log
    if guild_id in server_configs and 'log_channel' in server_configs[guild_id]:
        log_channel = bot.get_channel(server_configs[guild_id]['log_channel'])
        if log_channel:
            embed = discord.Embed(title="📥 Membre rejoint", color=discord.Color.green())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Membre", value=f"{member.mention} ({member})", inline=False)
            embed.add_field(name="ID", value=member.id, inline=True)
            embed.add_field(name="Compte créé", value=f"<t:{int(member.created_at.timestamp())}:R>", inline=True)
            embed.add_field(name="Nombre de membres", value=member.guild.member_count, inline=True)
            embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=embed)

@bot.event
async def on_member_remove(member):
    guild_id = str(member.guild.id)
    
    if guild_id in server_configs and 'log_channel' in server_configs[guild_id]:
        log_channel = bot.get_channel(server_configs[guild_id]['log_channel'])
        if log_channel:
            embed = discord.Embed(title="📤 Membre parti", color=discord.Color.red())
            embed.set_thumbnail(url=member.display_avatar.url)
            embed.add_field(name="Membre", value=f"{member} ({member.id})", inline=False)
            embed.add_field(name="A rejoint", value=f"<t:{int(member.joined_at.timestamp())}:R>" if member.joined_at else "Inconnu", inline=True)
            embed.add_field(name="Nombre de membres", value=member.guild.member_count, inline=True)
            embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=embed)

@bot.event
async def on_message_delete(message):
    if message.author.bot:
        return
    
    guild_id = str(message.guild.id)
    
    if guild_id in server_configs and 'log_channel' in server_configs[guild_id]:
        log_channel = bot.get_channel(server_configs[guild_id]['log_channel'])
        if log_channel:
            embed = discord.Embed(title="🗑️ Message supprimé", color=discord.Color.orange())
            embed.add_field(name="Auteur", value=f"{message.author.mention}", inline=True)
            embed.add_field(name="Salon", value=f"{message.channel.mention}", inline=True)
            embed.add_field(name="Contenu", value=message.content[:1024] if message.content else "*Aucun contenu*", inline=False)
            embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=embed)

@bot.event
async def on_message_edit(before, after):
    if before.author.bot or before.content == after.content:
        return
    
    guild_id = str(before.guild.id)
    
    if guild_id in server_configs and 'log_channel' in server_configs[guild_id]:
        log_channel = bot.get_channel(server_configs[guild_id]['log_channel'])
        if log_channel:
            embed = discord.Embed(title="✏️ Message modifié", color=discord.Color.blue())
            embed.add_field(name="Auteur", value=f"{before.author.mention}", inline=True)
            embed.add_field(name="Salon", value=f"{before.channel.mention}", inline=True)
            embed.add_field(name="Avant", value=before.content[:512] if before.content else "*Vide*", inline=False)
            embed.add_field(name="Après", value=after.content[:512] if after.content else "*Vide*", inline=False)
            embed.timestamp = discord.utils.utcnow()
            await log_channel.send(embed=embed)

class QuestionnaireButton(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.button(label="📋 Compléter le questionnaire", style=discord.ButtonStyle.primary)
    async def questionnaire_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(QuestionnaireModal())

# Vue pour le menu de configuration avec embeds stylés
class ConfigView(discord.ui.View):
    def __init__(self, ctx):
        super().__init__(timeout=300)
        self.ctx = ctx
        self.guild_id = str(ctx.guild.id)
    
    @discord.ui.select(
        placeholder="🏠 Choisir le salon de bienvenue",
        min_values=1,
        max_values=1,
        custom_id="welcome_channel"
    )
    async def select_welcome_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        server_configs[self.guild_id]['welcome_channel'] = int(select.values[0])
        
        embed = discord.Embed(
            title="✅ Salon de bienvenue configuré",
            description=f"Les nouveaux membres seront accueillis dans <#{select.values[0]}>",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update_main_message()
    
    @discord.ui.select(
        placeholder="📝 Choisir le salon de logs",
        min_values=1,
        max_values=1,
        custom_id="log_channel"
    )
    async def select_log_channel(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        server_configs[self.guild_id]['log_channel'] = int(select.values[0])
        
        embed = discord.Embed(
            title="✅ Salon de logs configuré",
            description=f"Tous les événements seront loggés dans <#{select.values[0]}>",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update_main_message()
    
    @discord.ui.select(
        placeholder="👤 Choisir le rôle automatique",
        min_values=1,
        max_values=1,
        custom_id="auto_role"
    )
    async def select_auto_role(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        server_configs[self.guild_id]['auto_role'] = int(select.values[0])
        
        embed = discord.Embed(
            title="✅ Rôle automatique configuré",
            description=f"Les nouveaux membres recevront <@&{select.values[0]}>",
            color=discord.Color.green()
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update_main_message()
    
    @discord.ui.button(label="📋 Questionnaire", style=discord.ButtonStyle.secondary, emoji="📋", row=3)
    async def toggle_questionnaire(self, interaction: discord.Interaction, button: discord.ui.Button):
        if self.guild_id not in server_configs:
            server_configs[self.guild_id] = {}
        
        current = server_configs[self.guild_id].get('questionnaire_enabled', False)
        server_configs[self.guild_id]['questionnaire_enabled'] = not current
        
        embed = discord.Embed(
            title="📋 Questionnaire " + ("activé" if not current else "désactivé"),
            description="Les nouveaux membres " + ("recevront" if not current else "ne recevront plus") + " un questionnaire en DM",
            color=discord.Color.green() if not current else discord.Color.red()
        )
        
        button.style = discord.ButtonStyle.success if not current else discord.ButtonStyle.secondary
        
        await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.update_main_message()
        await interaction.message.edit(view=self)
    
    @discord.ui.button(label="💾 Sauvegarder", style=discord.ButtonStyle.success, emoji="💾", row=3)
    async def save_config(self, interaction: discord.Interaction, button: discord.ui.Button):
        embed = discord.Embed(
            title="💾 Configuration sauvegardée !",
            description="Toutes les modifications ont été enregistrées avec succès.",
            color=discord.Color.green()
        )
        embed.add_field(
            name="📊 Récapitulatif",
            value=self.get_config_summary(),
            inline=False
        )
        await interaction.response.send_message(embed=embed, ephemeral=True)
    
    def get_config_summary(self):
        config = server_configs.get(self.guild_id, {})
        welcome = f"<#{config.get('welcome_channel')}>" if config.get('welcome_channel') else '❌ Non configuré'
        logs = f"<#{config.get('log_channel')}>" if config.get('log_channel') else '❌ Non configuré'
        role = f"<@&{config.get('auto_role')}>" if config.get('auto_role') else '❌ Non configuré'
        quest = '✅ Activé' if config.get('questionnaire_enabled') else '❌ Désactivé'
        
        return f"""
🏠 **Bienvenue:** {welcome}
📝 **Logs:** {logs}
👤 **Rôle auto:** {role}
📋 **Questionnaire:** {quest}
        """
    
    async def update_main_message(self):
        # Cette méthode pourrait être appelée pour mettre à jour le message principal
        pass

# Commande !config avec menu déroulant et embed
@bot.command(name='config')
@commands.has_permissions(administrator=True)
async def config_command(ctx):
    guild_id = str(ctx.guild.id)
    
    # Embed principal
    embed = discord.Embed(
        title="⚙️ Configuration du serveur",
        description="Utilise les menus déroulants ci-dessous pour configurer le bot",
        color=discord.Color.blue()
    )
    
    # Ajouter la config actuelle
    config = server_configs.get(guild_id, {})
    welcome = f"<#{config.get('welcome_channel')}>" if config.get('welcome_channel') else '❌ Non configuré'
    logs = f"<#{config.get('log_channel')}>" if config.get('log_channel') else '❌ Non configuré'
    role = f"<@&{config.get('auto_role')}>" if config.get('auto_role') else '❌ Non configuré'
    quest = '✅ Activé' if config.get('questionnaire_enabled') else '❌ Désactivé'
    
    embed.add_field(
        name="📊 Configuration actuelle",
        value=f"""
🏠 **Salon de bienvenue:** {welcome}
📝 **Salon de logs:** {logs}
👤 **Rôle automatique:** {role}
📋 **Questionnaire:** {quest}
        """,
        inline=False
    )
    
    embed.add_field(
        name="📚 Guide",
        value="""
**1.** Choisis le salon de bienvenue (où le bot accueillera les nouveaux membres)
**2.** Choisis le salon de logs (pour suivre tous les événements)
**3.** Choisis le rôle à donner automatiquement aux nouveaux
**4.** Active/désactive le questionnaire d'arrivée
**5.** Clique sur 💾 pour sauvegarder
        """,
        inline=False
    )
    
    embed.set_thumbnail(url=ctx.guild.icon.url if ctx.guild.icon else None)
    embed.set_footer(text=f"Configuré par {ctx.author}", icon_url=ctx.author.avatar.url if ctx.author.avatar else None)
    
    # Créer la vue avec les selects
    view = ConfigView(ctx)
    
    # Ajouter les options de salons
    channel_options = [
        discord.SelectOption(label=f"#{channel.name}", value=str(channel.id), emoji="💬")
        for channel in ctx.guild.text_channels[:25]
    ]
    
    log_options = [
        discord.SelectOption(label=f"#{channel.name}", value=str(channel.id), emoji="📋")
        for channel in ctx.guild.text_channels[:25]
    ]
    
    role_options = [
        discord.SelectOption(label=role.name, value=str(role.id), emoji="🎭")
        for role in ctx.guild.roles[1:26] if not role.managed
    ]
    
    view.children[0].options = channel_options
    view.children[1].options = log_options
    view.children[2].options = role_options
    
    # Configurer le bouton questionnaire selon l'état actuel
    questionnaire_enabled = server_configs.get(guild_id, {}).get('questionnaire_enabled', False)
    view.children[3].style = discord.ButtonStyle.success if questionnaire_enabled else discord.ButtonStyle.secondary
    
    await ctx.reply(embed=embed, view=view)

# Commande !reactionrole
@bot.command(name='reactionrole')
@commands.has_permissions(administrator=True)
async def reaction_role(ctx, emoji, role: discord.Role, *, message_text):
    """Crée un message avec reaction role"""
    embed = discord.Embed(title="🎭 Reaction Role", description=message_text, color=discord.Color.purple())
    embed.add_field(name="Comment obtenir le rôle ?", value=f"Réagis avec {emoji} pour obtenir {role.mention}", inline=False)
    
    msg = await ctx.send(embed=embed)
    await msg.add_reaction(emoji)
    
    # Sauvegarder la config (simplifié)
    guild_id = str(ctx.guild.id)
    if guild_id not in server_configs:
        server_configs[guild_id] = {}
    if 'reaction_roles' not in server_configs[guild_id]:
        server_configs[guild_id]['reaction_roles'] = {}
    
    server_configs[guild_id]['reaction_roles'][str(msg.id)] = {
        'emoji': str(emoji),
        'role_id': role.id
    }
    
    await ctx.message.add_reaction('✅')

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    guild_id = str(payload.guild_id)
    
    if guild_id in server_configs and 'reaction_roles' in server_configs[guild_id]:
        msg_id = str(payload.message_id)
        if msg_id in server_configs[guild_id]['reaction_roles']:
            config = server_configs[guild_id]['reaction_roles'][msg_id]
            if str(payload.emoji) == config['emoji']:
                guild = bot.get_guild(payload.guild_id)
                role = guild.get_role(config['role_id'])
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.add_roles(role)

@bot.event
async def on_raw_reaction_remove(payload):
    guild_id = str(payload.guild_id)
    
    if guild_id in server_configs and 'reaction_roles' in server_configs[guild_id]:
        msg_id = str(payload.message_id)
        if msg_id in server_configs[guild_id]['reaction_roles']:
            config = server_configs[guild_id]['reaction_roles'][msg_id]
            if str(payload.emoji) == config['emoji']:
                guild = bot.get_guild(payload.guild_id)
                role = guild.get_role(config['role_id'])
                member = guild.get_member(payload.user_id)
                if role and member:
                    await member.remove_roles(role)

# Vue pour le menu help avec select
class HelpView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=180)
    
    @discord.ui.select(
        placeholder="📚 Choisir une catégorie",
        options=[
            discord.SelectOption(label="Configuration", description="Commandes de configuration", emoji="⚙️", value="config"),
            discord.SelectOption(label="Modération", description="Commandes de modération", emoji="🛡️", value="moderation"),
            discord.SelectOption(label="Utilitaires", description="Commandes utiles", emoji="🔧", value="utils"),
            discord.SelectOption(label="Menu principal", description="Retour au menu principal", emoji="🏠", value="home")
        ]
    )
    async def help_select(self, interaction: discord.Interaction, select: discord.ui.Select):
        category = select.values[0]
        
        if category == "home":
            embed = discord.Embed(
                title="📚 Menu d'aide du bot",
                description="Sélectionne une catégorie dans le menu déroulant pour voir les commandes disponibles !",
                color=discord.Color.blue()
            )
            embed.add_field(
                name="⚙️ Configuration",
                value="Paramètres du serveur, bienvenue, logs, questionnaire",
                inline=False
            )
            embed.add_field(
                name="🛡️ Modération",
                value="Kick, ban, mute, clear et gestion des membres",
                inline=False
            )
            embed.add_field(
                name="🔧 Utilitaires",
                value="Reaction roles et autres outils",
                inline=False
            )
            embed.set_footer(text="Utilise le menu déroulant ci-dessous pour naviguer")
        
        elif category == "config":
            embed = discord.Embed(
                title="⚙️ Commandes de Configuration",
                description="Toutes les commandes pour configurer ton serveur",
                color=discord.Color.green()
            )
            embed.add_field(
                name="!config",
                value="```Ouvre le menu de configuration interactif avec :\n• Salon de bienvenue\n• Salon de logs\n• Rôle automatique\n• Questionnaire d'arrivée```",
                inline=False
            )
            embed.set_footer(text="💡 Utilise !config pour tout paramétrer facilement")
        
        elif category == "moderation":
            embed = discord.Embed(
                title="🛡️ Commandes de Modération",
                description="Commandes pour gérer ton serveur",
                color=discord.Color.red()
            )
            embed.add_field(
                name="!kick <@membre> [raison]",
                value="```Expulse un membre du serveur```",
                inline=False
            )
            embed.add_field(
                name="!ban <@membre> [raison]",
                value="```Bannit un membre du serveur```",
                inline=False
            )
            embed.add_field(
                name="!unban <ID>",
                value="```Débannit un utilisateur (utilise son ID)```",
                inline=False
            )
            embed.add_field(
                name="!mute <@membre> <durée> [raison]",
                value="```Mute temporairement (10s, 5m, 1h, 1d)```",
                inline=False
            )
            embed.add_field(
                name="!unmute <@membre>",
                value="```Retire le mute d'un membre```",
                inline=False
            )
            embed.add_field(
                name="!clear <nombre>",
                value="```Supprime des messages (1-100)```",
                inline=False
            )
            embed.add_field(
                name="!lock / !unlock",
                value="```Verrouille ou déverrouille le salon actuel```",
                inline=False
            )
            embed.set_footer(text="⚠️ Permissions requises pour utiliser ces commandes")
        
        elif category == "utils":
            embed = discord.Embed(
                title="🔧 Commandes Utilitaires",
                description="Outils supplémentaires",
                color=discord.Color.purple()
            )
            embed.add_field(
                name="!reactionrole <emoji> <@role> <texte>",
                value="```Crée un message avec reaction role\nExemple : !reactionrole 🎮 @Gamer Réagis pour être gamer !```",
                inline=False
            )
            embed.set_footer(text="✨ Plus de commandes à venir !")
        
        await interaction.response.edit_message(embed=embed, view=self)

# Commande !help avec menu déroulant
@bot.command(name='help')
async def help_command(ctx):
    embed = discord.Embed(
        title="📚 Menu d'aide du bot",
        description="Sélectionne une catégorie dans le menu déroulant pour voir les commandes disponibles !",
        color=discord.Color.blue()
    )
    embed.add_field(
        name="⚙️ Configuration",
        value="Paramètres du serveur, bienvenue, logs, questionnaire",
        inline=False
    )
    embed.add_field(
        name="🛡️ Modération",
        value="Kick, ban, mute, clear et gestion des membres",
        inline=False
    )
    embed.add_field(
        name="🔧 Utilitaires",
        value="Reaction roles et autres outils",
        inline=False
    )
    embed.set_footer(text="Utilise le menu déroulant ci-dessous pour naviguer")
    embed.set_thumbnail(url=bot.user.avatar.url if bot.user.avatar else None)
    
    await ctx.reply(embed=embed, view=HelpView())

@bot.command(name='kick')
@commands.has_permissions(kick_members=True)
async def kick(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply('❌ Utilisation : `!kick @membre [raison]`')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.reply('❌ Tu ne peux pas kick ce membre !')
        return
    
    await member.kick(reason=reason)
    await ctx.reply(f'✅ {member.mention} a été expulsé !')

@bot.command(name='ban')
@commands.has_permissions(ban_members=True)
async def ban(ctx, member: discord.Member = None, *, reason=None):
    if not member:
        await ctx.reply('❌ Utilisation : `!ban @membre [raison]`')
        return
    
    if member.top_role >= ctx.author.top_role:
        await ctx.reply('❌ Tu ne peux pas ban ce membre !')
        return
    
    await member.ban(reason=reason)
    await ctx.reply(f'🔨 {member.mention} a été banni !')

@bot.command(name='unban')
@commands.has_permissions(ban_members=True)
async def unban(ctx, user_id: int = None):
    if not user_id:
        await ctx.reply('❌ Utilisation : `!unban <ID>`')
        return
    
    try:
        user = await bot.fetch_user(user_id)
        await ctx.guild.unban(user)
        await ctx.reply(f'✅ {user.name} a été débanni !')
    except:
        await ctx.reply('❌ Utilisateur non trouvé ou non banni.')

@bot.command(name='mute')
@commands.has_permissions(moderate_members=True)
async def mute(ctx, member: discord.Member = None, duration: str = None, *, reason=None):
    if not member or not duration:
        await ctx.reply('❌ Utilisation : `!mute @membre <durée> [raison]`')
        return
    
    time_units = {'s': 1, 'm': 60, 'h': 3600, 'd': 86400}
    try:
        amount = int(duration[:-1])
        unit = duration[-1]
        seconds = amount * time_units.get(unit, 0)
        
        if seconds == 0 or seconds > 2419200:
            await ctx.reply('❌ Durée invalide !')
            return
        
        await member.timeout(discord.utils.utcnow() + discord.timedelta(seconds=seconds), reason=reason)
        await ctx.reply(f'🔇 {member.mention} mute pendant {duration} !')
    except:
        await ctx.reply('❌ Erreur.')

@bot.command(name='unmute')
@commands.has_permissions(moderate_members=True)
async def unmute(ctx, member: discord.Member = None):
    if not member:
        await ctx.reply('❌ Utilisation : `!unmute @membre`')
        return
    
    await member.timeout(None)
    await ctx.reply(f'🔊 {member.mention} unmute !')

@bot.command(name='clear')
@commands.has_permissions(manage_messages=True)
async def clear(ctx, amount: int = None):
    if not amount or amount < 1 or amount > 100:
        await ctx.reply('❌ Utilisation : `!clear <1-100>`')
        return
    
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f'✅ {len(deleted) - 1} messages supprimés !')
    await msg.delete(delay=3)

@bot.command(name='lock')
@commands.has_permissions(manage_channels=True)
async def lock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=False)
    await ctx.reply('🔒 Salon verrouillé !')

@bot.command(name='unlock')
@commands.has_permissions(manage_channels=True)
async def unlock(ctx):
    await ctx.channel.set_permissions(ctx.guild.default_role, send_messages=None)
    await ctx.reply('🔓 Salon déverrouillé !')

# Lancement
if __name__ == "__main__":
    print("🚀 Démarrage du bot...")
    token = os.getenv('TOKEN')
    
    if not token:
        print("❌ TOKEN manquant !")
        exit(1)
    
    print("✅ TOKEN détecté")
    keep_alive()
    print("🤖 Connexion à Discord...")
    
    try:
        bot.run(token)
    except Exception as e:
        print(f"❌ Erreur: {e}")
        exit(1)
