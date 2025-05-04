import discord
from discord.ext import tasks
import asyncio
from dotenv import load_dotenv
import os

# ========== CONFIGURACIÓN ==========
load_dotenv()
BOT_TOKEN = os.getenv("DISCORD_TOKEN")

CANAL_BIENVENIDA_ID = 1368039936040898560
CANAL_COMO_UNIRSE_ID = 1368055624558186578
CANAL_INVITADO_ID = 1368056182736027668
MENSAJE_BIENVENIDA = """Bienvenido/a {user_mention}
Este es el Discord del gremio "We Smash Daily".

Si estás interesado en unirte a nosotros, ve al canal <#{canal_unirse}> y sigue las instrucciones para postularte.

Si vienes como invitado, ve al canal <#{canal_invitado}> y sigue las instrucciones para ingresar como invitado."""
# ===================================

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

client = discord.Client(intents=intents)

# Esta es la tarea que enviará mensajes programados
@tasks.loop(seconds=30)
async def keep_alive():
    canal = client.get_channel(1368355275484168242)
    if canal:
        mensaje = await canal.send("¡El bot sigue activo!")
        await asyncio.sleep(10)
        await mensaje.delete()
        print("👾 El bot envió un mensaje para mantenerse activo y luego lo borró.")

@client.event
async def on_ready():
    print(f'✅ Bot conectado como {client.user}')
    keep_alive.start()

@client.event
async def on_member_join(member):
    guild = member.guild

    rol_auto = discord.utils.get(guild.roles, name="sin procesar")
    if rol_auto:
        await member.add_roles(rol_auto)
        print(f'✅ Rol "sin procesar" asignado a {member.name}')
    else:
        print(f'❌ No se encontró el rol "sin procesar"')

    canal = client.get_channel(CANAL_BIENVENIDA_ID)
    if canal:
        try:
            mensaje_formateado = MENSAJE_BIENVENIDA.format(
                user_mention=member.mention,
                canal_unirse=CANAL_COMO_UNIRSE_ID,
                canal_invitado=CANAL_INVITADO_ID
            )
            await canal.set_permissions(member, view_channel=True, send_messages=False)
            await canal.send(mensaje_formateado)
            print(f'👋 Se envió el mensaje de bienvenida a {member.name}')
        except Exception as e:
            print(f'❌ Error al enviar mensaje de bienvenida: {e}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    content = message.content.lower().strip()
    guild = message.guild
    autor = message.author

    if message.channel.id == CANAL_COMO_UNIRSE_ID and content == "ticket":
        await message.delete(delay=5)

        rol_reclutador = discord.utils.get(guild.roles, name="Reclutador")

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            autor: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            rol_reclutador: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        categoria_temporal = await guild.create_category(f"Temporal-{autor.name}")

        canal_ticket = await guild.create_text_channel(
            name=f"ticket-{autor.name}",
            overwrites=overwrites,
            category=categoria_temporal
        )

        canal_voz = await guild.create_voice_channel(
            name=f"Entrevista-{autor.name}",
            overwrites=overwrites,
            category=categoria_temporal
        )

        mencion_reclutador = f"<@&{rol_reclutador.id}>" if rol_reclutador else "@Reclutador"

        mensaje_ticket = f"Hola {autor.mention}, copia y pega el mensaje mostrado anteriormente de ejemplo y reemplaza con tu información del juego, luego espera a un {mencion_reclutador} para que siga con una entrevista."

        await canal_ticket.send(mensaje_ticket)
        print(f'🎫 Se creó el canal de ticket y el canal de voz para {autor.name} dentro de la categoría Temporal-{autor.name}')

    elif message.channel.id == CANAL_INVITADO_ID and content == "invitado":
        await message.delete(delay=5)

        rol_invitado = discord.utils.get(guild.roles, name="Invitados")
        rol_sin_procesar = discord.utils.get(guild.roles, name="sin procesar")
        if rol_invitado:
            await autor.add_roles(rol_invitado)
            print(f'🎟️ Se otorgó el rol "Invitados" a {autor.name}')
            if rol_sin_procesar in autor.roles:
                await autor.remove_roles(rol_sin_procesar)
                print(f'🗑️ Se quitó el rol "sin procesar" de {autor.name}')

client.run(BOT_TOKEN)
