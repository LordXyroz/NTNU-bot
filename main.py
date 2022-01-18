import discord
import os
import regex

from discord.ext import commands

# Set intents for member management
intents = discord.Intents.default()
intents.members = True

client = commands.Bot(command_prefix="", intents=intents)

# Set up values
welcome_msg = """__Norwegian:__
Velkommen til Programmering i Gjøvik NTNU discord kanalen {name}!
Vennligst oppgi klassen din (eller staff hvis du er ansatt ved NTNU) og ditt fulle navn i {welcome} kanalen på følgende format:
`<klasse> <fullt navn>`
Eksempel:
`14HBSPA Ola Nordmann`
Vennligst les reglene i {rules} kanalen og ha et hyggelig opphold. Kontakt gjerne en @admin dersom du har noen spørsmål.

__English:__
Welcome to the programming discord for NTNU Gjøvik {name}!
Please state your class (or staff if you work at NTNU) and your full name in the {welcome} channel in the following format:
`<class> <full name>`
Example:
`14HBSPA Ola Nordmann`
Please read the rules in {rules} and enjoy your stay. Feel free to contact an @admin if you have any questions.
"""
class_regex = "(\d\d[a-zA-Z]{5,8})|MACS|ALUMNI|(?i)International"
channel_ID_welcome = os.environ['channel_ID_welcome']
channel_ID_rules = os.environ['channel_ID_rules']


# Helper function spliting a string into 3 parts if regex part is found
# 1: Everything before the regex if found, everything otherwise
# 2: The regex if found, empty otherwise
# 3: Everything after the regex, empty otherwise
def regex_partition(content, separator):
  separator_match = regex.search(separator, content)
  if not separator_match:
    return content, '', ''
  
  matched_separator = separator_match.group(0)
  parts = regex.split(matched_separator, content, 1)
  return parts[0], matched_separator, parts[1]


# Try find guild role with regex, ignoring case
def regex_role_ignorecase(roleToFind, guildRoles):
  roleFound = None

  if not roleToFind:
    return roleFound

  for role in guildRoles:
    if regex.search(roleToFind, role.name, regex.IGNORECASE):
      roleFound = role
      break

  return roleFound


# Send and error message to a channel, message expects {roleID}
# Fallback with mention to guild owner
async def error_msg(msg, channel):
  try: 
    role_id = regex_role_ignorecase("admin", channel.guild.roles).id
    await channel.send(msg.format(roleID=role_id))
  except AttributeError:
    fail_msg = "Admin role not found, fallback to owner: {mention}"
    await channel.send(fail_msg.format(mention=channel.guild.owner.mention))
  except:
    fail_msg = "Fatal excepetion, fallback to owner: {mention}"
    await channel.send(fail_msg.format(mention=channel.guild.owner.mention))


# Message an @admin in case anything goes wrong
async def something_went_wrong():
  msg = "Oops, something went wrong!\nAn <@&{roleID}> will be here shortly!"
  channel = await client.fetch_channel(channel_ID_welcome)
  await error_msg(msg, channel)


# Message and @admin for staff role
async def staff_call_admin():
  msg = "Hi staff!\nAn <@&{roleID}> will be here shortly!"
  channel = await client.fetch_channel(channel_ID_welcome)
  await error_msg(msg, channel)


# Someone used !Help
async def call_admin():
  msg = "An <@&{roleID}> will be here shortly!"
  channel = await client.fetch_channel(channel_ID_welcome)
  await error_msg(msg, channel)


# Role not found message to user
async def role_not_found(member):
  msg = "{name} Role could not be found, did you spell it correctly?\nType !help for an admin"
  channel = await client.fetch_channel(channel_ID_welcome)
  await channel.send(msg.format(name=member.mention))


# Name to short message to user
async def name_too_short(member):
  msg = "{name} Your name is too short, we need atleast a first and last name.\nType !help for an admin"
  channel = await client.fetch_channel(channel_ID_welcome)
  await channel.send(msg.format(name=member.mention))


# Edit the member's nickname and roles
async def edit_member_name_role(message):
  member_roles = message.author.roles
  is_unnamed = False

  for role in member_roles:
    if role.name == "Unnamed":
      is_unnamed = True
      member_roles.remove(role)
      break

  # Return early if member role isn't Unnamed (has gotten a class)
  if not is_unnamed:
    return

  guild_roles = message.guild.roles
  split_string = regex_partition(message.content, class_regex)
  name_index = 0 if split_string[0] else 2

  role_found = regex_role_ignorecase(split_string[1], guild_roles)

  # If the class doesn't exist something went wrong
  if not role_found:
    match = regex.search("staff", message.content, regex.IGNORECASE)
    if match:
      await staff_call_admin()
      return

    help = regex.search("!help", message.content, regex.IGNORECASE)

    if help:
      await call_admin()
    elif split_string[1] == '':
      return
    else:
      await role_not_found(message.author)

    return  # Return out so we don't edit with wrong values

  check_name = split_string[name_index].split(' ')
  if len(check_name) <= 1:
    await name_too_short(message.author)
    return
  
  member_roles.append(role_found)

  # Try to edit the member with new role and nickname
  try:
    await message.author.edit(nick=split_string[name_index].lstrip(), roles=member_roles)
  except discord.Forbidden as e:
    print(e)
    await something_went_wrong()
  except discord.HTTPException as e:
    print(e)
    await something_went_wrong()
  

# Wait for member to join, set's role to "UNNAMED" and changes nickname
@client.event
async def on_member_join(member):
  member_roles = member.roles
  member_roles.append(regex_role_ignorecase("Unnamed", member.guild.roles))
  channel = await client.fetch_channel(channel_ID_welcome)

  welcome_mention = channel.mention
  rules_mention = (await client.fetch_channel(channel_ID_rules)).mention

  await channel.send(welcome_msg.format(name=member.mention, welcome=welcome_mention, rules=rules_mention))

  try:
    await member.edit(roles=member_roles)
  except discord.Forbidden as e:
    print(e)
    await something_went_wrong()
  except discord.HTTPException as e:
    print(e)
    await something_went_wrong()


# Wait for message in the welcome channel, returns early if not correct channel, DM or from bot
@client.event
async def on_message(message):
  if str(message.channel.id) != str(channel_ID_welcome):
    return
  if message.author.bot:
    return

  await edit_member_name_role(message)


@client.event
async def on_ready():
  print('BOT ready')


client.run(os.environ['TOKEN'])
