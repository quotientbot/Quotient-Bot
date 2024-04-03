from collections import Counter

import discord
from typing import Union
from core import Context


async def _self_clean_system(ctx: Context, search: int) -> dict:
    count = 0
    async for msg in ctx.history(limit=search, before=ctx.message):
        if msg.author == ctx.me:
            await msg.delete()
            count += 1
    return {"Bot": count}


async def _complex_cleanup_strategy(ctx: Context, search) -> Counter:
    def check(m: discord.Message):
        return m.author == ctx.me or m.content.startswith(ctx.prefix)

    deleted = await ctx.channel.purge(limit=search, check=check, before=ctx.message)
    return Counter(m.author.display_name for m in deleted)


async def do_removal(ctx: Context, limit, predicate, *, before=None, after=None):
    if limit > 2000:
        return await ctx.error(f"Too many messages to search given ({limit}/2000)")

    if before is None:
        before = ctx.message
    else:
        before = discord.Object(id=before)

    if after is not None:
        after = discord.Object(id=after)

    try:
        deleted = await ctx.channel.purge(limit=limit, before=before, after=after, check=predicate)
    except discord.Forbidden as e:
        return await ctx.error("I do not have permissions to delete messages.")
    except discord.HTTPException as e:
        return await ctx.error(f"Error: {e} (try a smaller search?)")

    spammers = Counter(m.author.display_name for m in deleted)
    deleted = len(deleted)
    messages = [f'{deleted} message{" was" if deleted == 1 else "s were"} removed.']
    if deleted:
        messages.append("")
        spammers = sorted(spammers.items(), key=lambda t: t[1], reverse=True)
        messages.extend(f"**{name}**: {count}" for name, count in spammers)

    to_send = "\n".join(messages)

    if len(to_send) > 2000:
        await ctx.send(f"Successfully removed {deleted} messages.", delete_after=10)
    else:
        await ctx.send(to_send, delete_after=10)




async def mod_chan_perms(self, ctx, chan: discord.TextChannel, targ: Union[discord.Member, discord.Role], perm_val: bool, view_perm: bool):
    overwrites = chan.overwrites_for(targ)
    if overwrites is not None:
        if view_perm:
            if overwrites.view_channel == perm_val:
                return await ctx.send(f"The channel {chan.mention} is already {'unhidden' if perm_val else 'hidden'} for {targ.mention if isinstance(targ, Member) else targ.name}.")
            overwrites.view_channel = perm_val
        else:
            if overwrites.send_messages == perm_val:
                return await ctx.send(f"The channel {chan.mention} is already {'unlocked' if perm_val else 'locked'} for {targ.mention if isinstance(targ, Member) else targ.name}.")
            overwrites.send_messages = perm_val
    else:
        overwrites = chan.overwrites_for(ctx.guild.default_role)
        if view_perm:
            overwrites.view_channel = perm_val
        else:
            overwrites.send_messages = perm_val
    await chan.set_permissions(targ, overwrite=overwrites, reason=f"Action done by {ctx.author} | ({ctx.author.id})")
    await ctx.send(f"The channel {chan.mention} is {'🔓 unlocked' if perm_val else '🔒 locked'} for {targ.mention if isinstance(targ, Member) else targ.name}." if not view_perm else f"The channel {chan.mention} is now {'unhidden' if perm_val else 'hidden'} for {targ.mention if isinstance(targ, Member) else targ.name}.")
