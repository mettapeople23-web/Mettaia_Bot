import discord
import os
import asyncio
from mistralai import Mistral

# ── Config ──────────────────────────────────────────────
DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
MISTRAL_API_KEY = os.environ["MISTRAL_API_KEY"]
MISTRAL_AGENT_ID = os.environ["MISTRAL_AGENT_ID"]

mistral = Mistral(api_key=MISTRAL_API_KEY)

# Channels where Mettaïa will respond
ACTIVE_CHANNELS = ["ask-mettaia", "general", "welcome", "🌿・welcome"]

# ── Discord Client ───────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

client = discord.Client(intents=intents)

# Track recent conversation per channel (simple memory)
conversation_history = {}

@client.event
async def on_ready():
    print(f"✅ Mettaïa is live as {client.user}")

@client.event
async def on_message(message):
    # Ignore own messages
    if message.author == client.user:
        return

    # Only respond in active channels OR when directly mentioned
    channel_name = message.channel.name.lower() if hasattr(message.channel, 'name') else ""
    mentioned = client.user in message.mentions
    in_active_channel = any(ch in channel_name for ch in ACTIVE_CHANNELS)

    if not (in_active_channel or mentioned):
        return

    # Don't respond to bot accounts
    if message.author.bot:
        return

    user_text = message.content.replace(f"<@{client.user.id}>", "").strip()
    if not user_text:
        return

    # Show typing indicator
    async with message.channel.typing():
        try:
            # Build message history for this channel (last 6 exchanges)
            channel_id = str(message.channel.id)
            if channel_id not in conversation_history:
                conversation_history[channel_id] = []

            conversation_history[channel_id].append({
                "role": "user",
                "content": f"{message.author.display_name}: {user_text}"
            })

            # Keep only last 12 messages (6 exchanges)
            if len(conversation_history[channel_id]) > 12:
                conversation_history[channel_id] = conversation_history[channel_id][-12:]

            # Call Mistral Agent
            response = mistral.agents.complete(
                agent_id=MISTRAL_AGENT_ID,
                messages=conversation_history[channel_id]
            )

            reply = response.choices[0].message.content.strip()

            # Save assistant reply to history
            conversation_history[channel_id].append({
                "role": "assistant",
                "content": reply
            })

            # Discord has 2000 char limit — split if needed
            if len(reply) > 1900:
                parts = [reply[i:i+1900] for i in range(0, len(reply), 1900)]
                for part in parts:
                    await message.reply(part)
            else:
                await message.reply(reply)

        except Exception as e:
            print(f"Error: {e}")
            await message.reply("🌿 Something went quiet on my end — please try again in a moment.")

# ── Run ──────────────────────────────────────────────────
client.run(DISCORD_TOKEN)
