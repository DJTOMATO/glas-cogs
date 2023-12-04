import discord
from discord import Embed
from datetime import datetime
from redbot.core import commands


class GuildID(commands.Cog):
    @commands.command()
    @commands.is_owner()
    async def istats(self, ctx, invite_link: str):
        """Returns server stats from an invite link"""
        """Keep in mind the bot has to be in the target server to be able to retrieve the information"""
        async with ctx.channel.typing():
            try:
                invite = await ctx.bot.fetch_invite(invite_link)

                # Check if the invite is partial or full
                if isinstance(invite.guild, discord.PartialInviteGuild):
                    # Extract information from PartialInviteGuild
                    guild_id = invite.guild.id
                    guild_name = invite.guild.name
                    guild_description = invite.guild.description
                    guild_features = [
                        feature.replace("_", " ").title()
                        for feature in invite.guild.features
                    ]

                    guild_icon = invite.guild.icon
                    guild_banner = invite.guild.banner
                    guild_splash = invite.guild.splash
                    guild_vanity_url = invite.guild.vanity_url
                    guild_vanity_url_code = invite.guild.vanity_url_code
                    guild_nsfw_level = invite.guild.nsfw_level
                    guild_verification_level = invite.guild.verification_level
                    guild_premium_subscription_count = (
                        invite.guild.premium_subscription_count
                    )

                    # Check if the bot is in the guild before fetching members
                    if ctx.bot.get_guild(guild_id):
                        members = await invite.guild.chunk()
                        online_members = sum(
                            member.status == discord.Status.online for member in members
                        )
                        text_channels = len(invite.guild.text_channels)
                        voice_channels = len(invite.guild.voice_channels)
                        emojis_count = len(invite.guild.emojis)
                        stickers_count = len(invite.guild.stickers)
                        roles_count = len(invite.guild.roles)
                    else:
                        # If the bot is not in the guild, set member-related information to None
                        members = None
                        online_members = (
                            text_channels
                        ) = (
                            voice_channels
                        ) = emojis_count = stickers_count = roles_count = None

                elif isinstance(invite, discord.Invite):
                    # Extract information from Invite
                    guild_id = invite.guild.id
                    guild_banner = invite.guild.banner
                    guild_name = invite.guild.name
                    owner_name = getattr(invite.guild.owner, "name", "N/A")
                    created_at = invite.guild.created_at.strftime("%Y-%m-%d %H:%M:%S")
                    approximate_member_count = invite.approximate_member_count
                    approximate_presence_count = invite.approximate_presence_count
                    channel = invite.channel
                    code = invite.code
                    guild_icon = invite.guild.icon
                    expires_at = invite.expires_at
                    inviter = invite.inviter
                    max_age = invite.max_age
                    max_uses = invite.max_uses
                    revoked = invite.revoked
                    scheduled_event = invite.scheduled_event
                    scheduled_event_id = invite.scheduled_event_id
                    target_application = invite.target_application
                    target_type = invite.target_type
                    target_user = invite.target_user
                    temporary = invite.temporary
                    url = invite.url
                    uses = invite.uses

                    # Check if the bot is in the guild before fetching members
                    bot_in_guild = ctx.bot.get_guild(guild_id)
                    if bot_in_guild:
                        members = await invite.guild.chunk()
                        online_members = sum(
                            member.status == discord.Status.online for member in members
                        )
                        online = str(
                            len(
                                [
                                    m.status
                                    for m in members
                                    if str(m.status) == "online"
                                    or str(m.status) == "idle"
                                ]
                            )
                        )
                        # total_users = str(len(members))
                        text_channels = len(invite.guild.text_channels)
                        voice_channels = len(invite.guild.voice_channels)
                        emojis_count = len(invite.guild.emojis)
                        stickers_count = len(invite.guild.stickers)
                        roles_count = len(invite.guild.roles)
                    else:
                        # If the bot is not in the guild, set member-related information to None
                        members = None
                        online_members = (
                            text_channels
                        ) = (
                            voice_channels
                        ) = emojis_count = stickers_count = roles_count = 0

                else:
                    raise ValueError("Invalid invite type")

                # Create an embed
                embed = Embed(title="Server Stats", color=discord.Color.blue())
                embed.add_field(name="Guild ID", value=guild_id, inline=True)
                embed.add_field(name="Guild Name", value=guild_name, inline=True)

                if isinstance(invite.guild, discord.PartialInviteGuild):
                    # Add Guild Description field only if guild_description is not None
                    if guild_description is not None:
                        embed.add_field(
                            name="Guild Description",
                            value=guild_description,
                            inline=False,
                        )
                    # add attachment image

                    # Format features in pairs
                    formatted_features = [
                        f"{guild_features[i]}\n{guild_features[i + 1]}"
                        for i in range(0, len(guild_features) - 1, 2)
                    ]

                    # If there is an odd number of features, add the last one without a pair
                    if len(guild_features) % 2 != 0:
                        formatted_features.append(f"{guild_features[-1]}\nN/A")

                    embed.set_thumbnail(url=guild_icon)
                    embed.add_field(
                        name="Guild Banner",
                        value=f"[Click here]({guild_banner})",
                        inline=True,
                    )
                    # Add Guild Splash field only if guild_splash is not None
                    if guild_splash is not None:
                        embed.add_field(
                            name="Guild Splash",
                            value=f"[Click here]({guild_splash})",
                            inline=True,
                        )
                    embed.add_field(
                        name="Guild Vanity URL", value=guild_vanity_url, inline=False
                    )
                    embed.add_field(
                        name="Guild Vanity URL Code",
                        value=guild_vanity_url_code,
                        inline=True,
                    )
                    embed.add_field(
                        name="Guild NSFW Level", value=guild_nsfw_level, inline=True
                    )
                    embed.add_field(
                        name="Guild Verification Level",
                        value=guild_verification_level,
                        inline=True,
                    )
                    embed.add_field(
                        name="Guild Premium Subscription Count",
                        value=guild_premium_subscription_count,
                        inline=True,
                    )
                    # Add guild features only if there are features to display
                    if formatted_features:
                        embed.add_field(
                            name="Guild Features",
                            value="\n".join(formatted_features),
                            inline=False,
                        )

                elif isinstance(invite, discord.Invite):
                    embed.add_field(name="Owner", value=owner_name, inline=True)
                    embed.add_field(name="Created At", value=created_at, inline=True)
                    embed.add_field(
                        name="Approximate Member Count",
                        value=approximate_member_count,
                        inline=True,
                    )
                    embed.add_field(
                        name="Approximate Presence Count",
                        value=approximate_presence_count,
                        inline=True,
                    )
                    embed.set_image(url=guild_banner)
                    embed.set_thumbnail(url=guild_icon)
                    embed.add_field(name="Channel", value=channel, inline=True)
                    embed.add_field(name="Code", value=code, inline=True)

                    # Check for None values before adding fields
                    if expires_at is not None:
                        embed.add_field(
                            name="Expires At", value=expires_at, inline=True
                        )
                    if inviter is not None:
                        embed.add_field(name="Inviter", value=inviter, inline=True)
                    if max_age is not None:
                        embed.add_field(name="Max Age", value=max_age, inline=True)
                    if max_uses is not None:
                        embed.add_field(name="Max Uses", value=max_uses, inline=True)
                    if revoked is not None:
                        embed.add_field(name="Revoked", value=revoked, inline=True)
                    if scheduled_event is not None:
                        embed.add_field(
                            name="Scheduled Event", value=scheduled_event, inline=True
                        )
                    if scheduled_event_id is not None:
                        embed.add_field(
                            name="Scheduled Event ID",
                            value=scheduled_event_id,
                            inline=True,
                        )
                    if target_application is not None:
                        embed.add_field(
                            name="Target Application",
                            value=target_application,
                            inline=True,
                        )
                    # Modify the display value for Target Type
                    target_type_value = (
                        "Non-Targetted"
                        if target_type == discord.InviteTarget.unknown
                        else target_type
                    )
                    embed.add_field(
                        name="Target Type", value=target_type_value, inline=True
                    )

                    if target_user is not None:
                        embed.add_field(
                            name="Target User", value=target_user, inline=True
                        )
                    if temporary is not None:
                        embed.add_field(name="Temporary", value=temporary, inline=True)
                    if url is not None:
                        embed.add_field(name="URL", value=url, inline=True)
                    if uses is not None:
                        embed.add_field(name="Uses", value=uses, inline=True)

                # Add member-related information only if the bot is in the guild
                # Add member-related information only if the bot is in the guild
                if members is not None:
                    if online_members is not None:
                        embed.add_field(
                            name="Online Members",
                            value=f"{online}/{len(members)} online",
                            inline=True,
                        )
                    if text_channels is not None:
                        embed.add_field(
                            name="Text Channels", value=text_channels, inline=True
                        )
                    if voice_channels is not None:
                        embed.add_field(
                            name="Voice Channels", value=voice_channels, inline=True
                        )
                    if emojis_count is not None:
                        embed.add_field(
                            name="Emojis Count", value=emojis_count, inline=True
                        )
                    if stickers_count is not None:
                        embed.add_field(
                            name="Stickers Count", value=stickers_count, inline=True
                        )
                    if roles_count is not None:
                        embed.add_field(
                            name="Roles Count", value=roles_count, inline=True
                        )

                # Send the guild id
                variable = f"{guild_id}"
                await ctx.send(variable)
                # Send the embed
                await ctx.send(embed=embed)

            except discord.errors.NotFound:
                await ctx.send("Invalid invite link or the invite has expired.")
            except ValueError as e:
                await ctx.send(str(e))
            except Exception as e:
                await ctx.send(
                    f"An error occurred while processing the invitacion! {str(e)}"
                )
                await ctx.send(f"Error: {str(e)}")

    @commands.command()
    @commands.is_owner()
    async def serverinvites(self, ctx):
        """Get a list of server invites"""
        async with ctx.typing():
            server_name = ctx.guild.name
            embed = Embed(title=f"Server Invites for {server_name}:", description="")
            embed.set_footer(text="Non used invites won't be displayed.")
            # Obtain the guild banner
            guild_banner = ctx.guild.banner

            # Check if the guild has a banner
            if guild_banner:
                embed.set_image(url=guild_banner)
            invites = await ctx.guild.invites()

            for invite in invites:
                if not invite.expires_at or invite.expires_at > discord.utils.utcnow():
                    # Check if the invite has not expired
                    if invite.uses > 0:
                        invite_url = f"https://discord.gg/{invite.code}"
                        embed.description += f"\n[Invite Code: {invite.code}]({invite_url}) - Uses: {invite.uses} - Max Uses: {invite.max_uses}"

            await ctx.send(embed=embed)
