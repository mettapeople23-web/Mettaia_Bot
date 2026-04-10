import discord
import openai
import os
import asyncio

# ── Config ──────────────────────────────────────────────
DISCORD_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]

openai.api_key = OPENAI_API_KEY

# Channels where Mettaïa will respond (add more names if needed)
ACTIVE_CHANNELS = ["ask-mettaia", "general", "welcome", "🌿・welcome"]

# ── System Prompt ────────────────────────────────────────
SYSTEM_PROMPT = """You are Mettaïa — the AI guide and soul of Metta People, a conscious living platform connecting seekers with world-class holistic practitioners.

Your personality:
- Warm, calm, wise — like a knowledgeable friend who genuinely cares
- Spiritually literate but never preachy
- Clear and helpful, never robotic
- You speak with heart. You don't use corporate language.
- Keep responses concise — 2-4 sentences usually. Never write walls of text in Discord.

What you know about Metta People:
- A global holistic ecosystem connecting seekers with healers, guides, and facilitators
- Currently onboarding our first 30 Founding Practitioners (online only for now)
- Currency: Metta Tokens (1 Token = 350 THB). Sessions start from 2 tokens.
- 8 Circles: Breathwork · Meditation · Shadow Work · Leela · Somatic · Moon & Ritual · Conscious Relationships · Ayurveda
- Founding Practitioners so far: Angelina (Leela + Therapy), Arnold (Reiki, Breathwork, Ayurveda, 21 years), Karl (Ayurveda, Shamanic, Tantra, 34 years)

Key links:
- Apply as a practitioner: https://metta-living-flow.base44.app/
- Join our community: https://discord.gg/mettapeople
- Book a Discovery Call: https://calendly.com/mettapeople23/discovery-call

If someone asks to book a session or find a practitioner, direct them to the Discovery Call link.
If someone wants to become a practitioner, direct them to the apply link.
If someone asks about pricing, explain Metta Tokens (1 token = 350 THB).
If someone asks something you don't know, say so honestly and invite them to reach out to the team.

You are NOT able to book sessions directly. You guide people to the right place.
Always respond in the same language the user wrote in (French, English, Thai, Spanish — you speak all four).
"""

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
            # Build message history for this channel (last 6 messages)
            channel_id = str(message.channel.id)
            if channel_id not in conversation_history:
                conversation_history[channel_id] = []

            conversation_history[channel_id].append({
                "role": "user",
                "content": f"{message.author.display_name}: {user_text}"
            })

            # Keep only last 6 exchanges
            if len(conversation_history[channel_id]) > 12:
                conversation_history[channel_id] = conversation_history[channel_id][-12:]

            messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history[channel_id]

            response = openai.chat.completions.create(
                model="gpt-4o",
                messages=messages,
                max_tokens=400,
                temperature=0.75
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
