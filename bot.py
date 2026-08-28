import discord
import json
import random
import os
import asyncio
from discord.ext import tasks
from datetime import datetime

CLASSEMENT_CHANNEL_ID = 1542679923200630914
CHANNEL_ID = 1499102303737872386
TOKEN = os.getenv("DISCORD_BOT_TOKEN")
intents = discord.Intents.default()
intents.message_content = True

client = discord.Client(intents=intents)

current_answer = None
question_active = False


@client.event
async def on_ready():
    print(f"✅ Connecté en tant que {client.user}")

    if not quiz_auto.is_running():
        quiz_auto.start()

    if not reset_hebdo.is_running():
        reset_hebdo.start()

@tasks.loop(minutes=20)
async def quiz_auto():

    global current_answer

    channel = client.get_channel(CHANNEL_ID)

    with open("questions.json", "r", encoding="utf-8") as f:
        questions = json.load(f)

    with open("flags.json", "r", encoding="utf-8") as f:
        flags = json.load(f)

    contenu = questions + flags

    question = random.choice(contenu)

    current_answer = question["answer"]

    embed = discord.Embed(
        title="🧠 Question Quiz",
        description=question["question"],
        color=discord.Color.purple()
    )

    embed.set_footer(
        text="Premier à répondre gagne 1 point ! 🏆"
    )

    await channel.send(embed=embed)

    await asyncio.sleep(30)

    if current_answer is not None:
        bonne_reponse = current_answer
        current_answer = None

        await channel.send(
            f"⏰ Temps écoulé ! Personne n'a trouvé la bonne réponse.\n💡 La bonne réponse était : **{bonne_reponse}**"
        )


async def update_classement():

    channel = client.get_channel(CLASSEMENT_CHANNEL_ID)

    with open("scores.json", "r", encoding="utf-8") as f:
        scores = json.load(f)

    classement = sorted(
        scores.items(),
        key=lambda x: x[1],
        reverse=True
    )

    embed = discord.Embed(
        title="🏆 Classement Quiz",
        description="Top des joueurs les plus performants",
        color=discord.Color.gold()
    )

    texte = ""

    medailles = ["🥇", "🥈", "🥉"]

    for i, (user_id, points) in enumerate(classement[:10], start=1):

        try:
            member = await channel.guild.fetch_member(int(user_id))
            pseudo = member.display_name
        except:
            pseudo = f"Utilisateur {user_id}"

        if i == 1:
            texte += f"👑 {medailles[0]} **{pseudo}** • `{points}` pts\n"

        elif i == 2:
            texte += f"{medailles[1]} **{pseudo}** • `{points}` pts\n"

        elif i == 3:
            texte += f"{medailles[2]} **{pseudo}** • `{points}` pts\n"

        else:
            texte += f"`#{i}` **{pseudo}** • `{points}` pts\n"

    if texte == "":
        texte = "Aucun score enregistré."

    embed.add_field(
        name="📊 Classement actuel",
        value=texte,
        inline=False
    )

    await channel.purge(limit=10)
    await channel.send(embed=embed)
async def update_roi():

    with open("scores.json", "r", encoding="utf-8") as f:
        scores = json.load(f)

    if not scores:
        return

    guild = client.guilds[0]

    premier_id = max(scores, key=scores.get)

    membre = await guild.fetch_member(int(premier_id))

    role_roi = discord.utils.get(
        guild.roles,
        name="👑 𝑹𝒐𝒊 𝒅𝒖 𝑸𝒖𝒊𝒛"
    )

    role_reine = discord.utils.get(
        guild.roles,
        name="👑 𝑹𝒆𝒊𝒏𝒆 𝒅𝒖 𝑸𝒖𝒊𝒛"
    )

    role_lady = discord.utils.get(
        guild.roles,
        name="🎀 𝑳𝒂𝒅𝒚"
    )

    for member in guild.members:

        if role_roi and role_roi in member.roles:
            await member.remove_roles(role_roi)

        if role_reine and role_reine in member.roles:
            await member.remove_roles(role_reine)

    if role_lady and role_lady in membre.roles:

        if role_reine:
            await membre.add_roles(role_reine)

    else:

        if role_roi:
            await membre.add_roles(role_roi)

@client.event
async def on_message(message):

    global current_answer

    if message.author.bot:
        return

    if message.content.lower().strip() == "!resetquiz":

        if not message.author.guild_permissions.administrator:
            await message.channel.send("❌ Tu n'as pas la permission.")
            return

        with open("scores.json", "w", encoding="utf-8") as f:
            json.dump({}, f)

        current_answer = None

        await message.channel.send(
            "⚠️ Tous les scores ont été supprimés.\n🏆 Nouveau classement lancé !"
        )

    if message.content.lower() == "!quiz":

        if not message.author.guild_permissions.administrator:
            await message.channel.send("❌ Tu n'as pas la permission.")
            return

        with open("questions.json", "r", encoding="utf-8") as f:
            questions = json.load(f)

        with open("flags.json", "r", encoding="utf-8") as f:
            flags = json.load(f)

        contenu = questions + flags

        question = random.choice(contenu)
        current_answer = question["answer"]
        question_active = True

        embed = discord.Embed(
            title="🧠 Question Quiz",
            description=question["question"],
            color=discord.Color.purple()
    )

        embed.set_footer(
            text="Premier à répondre gagne 1 point ! 🏆"
    )
        channel = client.get_channel(1499102303737872386)
        await message.channel.send(embed=embed)
        
        print("QUESTION ENVOYEE")

        print("Réponse détectée :", message.content)

        if message.content.lower().strip() == current_answer.lower().strip():

            await message.add_reaction("✅")

            with open("scores.json", "r", encoding="utf-8") as f:
                scores = json.load(f)

            user_id = str(message.author.id)

            if user_id not in scores:
                scores[user_id] = 0

            scores[user_id] += 1

            with open("scores.json", "w", encoding="utf-8") as f:
                json.dump(scores, f, indent=4)

            # On ferme IMMÉDIATEMENT la question
            current_answer = None
            question_active = False

            await update_classement()
            await update_roi()

            await message.channel.send(
                f"🎉 Bravo {message.author.mention} ! Bonne réponse ! (+1 point)"
        )

    if message.content.lower().strip().startswith("!drapeau"):
        if not message.author.guild_permissions.administrator:
            await message.channel.send("❌ Tu n'as pas la permission.")
            return
        with open("flags.json", "r", encoding="utf-8") as f:
            flags = json.load(f)

        flag = random.choice(flags)

        current_answer = flag["answer"]

        embed = discord.Embed(
            title="🌍 Devine le pays",
            description=flag["question"],
            color=discord.Color.blue()
    )

        embed.set_footer(
            text="Premier à répondre gagne 1 point !"
    )

        await message.channel.send(embed=embed)

    if message.content.lower().startswith("!profil"):

        membre = message.author

        if message.mentions:
            membre = message.mentions[0]

        with open("scores.json", "r", encoding="utf-8") as f:
            scores = json.load(f)

        user_id = str(membre.id)
        points = scores.get(user_id, 0)

        classement = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        rang = "Non classé"

        for i, (id_joueur, score) in enumerate(classement, start=1):
            if id_joueur == user_id:
                rang = i
                break

        titre = "Joueur"

        if any(role.name == "👑 𝑹𝒐𝒊 𝒅𝒖 𝑸𝒖𝒊𝒛" for role in membre.roles):
            titre = "👑 Roi du Quiz"

        elif any(role.name == "👑 𝑹𝒆𝒊𝒏𝒆 𝒅𝒖 𝑸𝒖𝒊𝒛" for role in membre.roles):
            titre = "👑 Reine du Quiz"

        embed = discord.Embed(
            title="📖 𝐏𝐫𝐨𝐟𝐢𝐥 𝐐𝐮𝐢𝐳",
            color=discord.Color.purple()
)
        embed.description = f"⭐ **{points} points** • 🏆 **Rang #{rang}**"
        embed.set_thumbnail(
            url=membre.display_avatar.url
)

        embed.add_field(
            name="👤 Joueur",
            value=membre.display_name,
            inline=False
)

        embed.add_field(
            name="🏆 Rang",
            value=f"#{rang}",
            inline=True
)

        embed.add_field(
            name="⭐ Points",
            value=str(points),
            inline=True
)

        embed.add_field(
            name="👑 Titre",
            value=titre,
            inline=False
)

        embed.set_footer(
            text="KMK Quiz • Continue de grimper dans le classement !"
        )

        await message.channel.send(embed=embed)
    if message.content.lower().strip() == "!top":

        with open("scores.json", "r", encoding="utf-8") as f:
            scores = json.load(f)

        classement = sorted(
            scores.items(),
            key=lambda x: x[1],
            reverse=True
        )

        embed = discord.Embed(
            title="🏆 Classement Quiz",
            description="Top des joueurs les plus performants",
            color=discord.Color.gold()
    )

        medailles = ["🥇", "🥈", "🥉"]

        texte = ""

        for i, (user_id, points) in enumerate(classement[:10], start=1):

            try:
                member = await message.guild.fetch_member(int(user_id))
                pseudo = member.display_name

            except:
                pseudo = f"Utilisateur {user_id}"

            if i == 1:
                texte += f"👑 {medailles[0]} **{pseudo}** • `{points}` pts\n"

            elif i == 2:
                texte += f"{medailles[1]} **{pseudo}** • `{points}` pts\n"

            elif i == 3:
                texte += f"{medailles[2]} **{pseudo}** • `{points}` pts\n"
            else:
                texte += f"`#{i}` **{pseudo}** • `{points}` pts\n"

        embed.add_field(
            name="📊 Classement actuel",
            value=texte if texte else "Personne n'est classé.",
            inline=False
    )

        await message.channel.send(embed=embed)

@tasks.loop(hours=1)
async def reset_hebdo():

    maintenant = datetime.now()

    if maintenant.weekday() == 6 and maintenant.hour == 0:

        with open("scores.json", "r", encoding="utf-8") as f:
            scores = json.load(f)

        if scores:

            gagnant_id = max(scores, key=scores.get)
            points = scores[gagnant_id]

            try:
                channel = client.get_channel(CHANNEL_ID)

                membre = await channel.guild.fetch_member(
                    int(gagnant_id)
                )
                
                await channel.send(
                    "📢 RÉSULTATS HEBDOMADAIRES 📢\n\n"
                    f"👑 {membre.mention} remporte cette semaine de quiz et devient {titre} !\n\n"
                    f"⭐ Score : {points} points\n\n"
                    "🏆 Tous les scores ont été réinitialisés.\n"
                    "Le nouveau classement débute dès maintenant.\n\n"
                    "✨ Que le meilleur gagne cette semaine !"
                )

            except:
                pass

        with open("scores.json", "w", encoding="utf-8") as f:
            json.dump({}, f, indent=4)
client.run(TOKEN)
