import datetime
import sys
import discord
import psycopg2
from discord.ext import commands
from psycopg2 import sql, pool
import common


class Quotes(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        try:
            self.pool = psycopg2.pool.ThreadedConnectionPool(
                1, 20,
                host="localhost",
                database="owo",
                user="langj"
            )
        except psycopg2.DatabaseError as e:

            print(f'postgres db seems to be fucked: {e}')
            sys.exit(1)

    @commands.group()
    async def qt(self, ctx):
        pass

    @qt.command(brief="<author> quote")
    async def add(self, ctx, member: discord.Member, *, quote: str):
        conn = self.pool.getconn()
        cur = conn.cursor()
        cur.execute(sql.SQL("insert into {} values (DEFAULT, %s, %s, %s)")
                    .format(sql.Identifier('quotes')),
                    [member.id, datetime.datetime.now(), quote])
        cur.close()
        conn.commit()
        self.pool.putconn(conn)

    @qt.command(brief="<text>")
    async def get(self, ctx, *, msg: str):
        conn = self.pool.getconn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM quotes WHERE quotes.quote ILIKE %s ESCAPE ''", (f"%%{msg.replace('%', '')}%%",))
        res = cur.fetchone()
        author_id = res[1]
        author = ctx.guild.get_member(author_id)
        if author is None:
            author = await self.bot.fetch_user(author_id)
        await ctx.channel.send(f"```\n{res[3].replace('`', '')}``` - {common.get_nick_or_name(author)}")
        cur.close()
        self.pool.putconn(conn)

    @qt.command(brief="lists quotes")
    async def list(self, ctx):
        conn = self.pool.getconn()
        cur = conn.cursor()
        cur.execute("SELECT * FROM quotes")
        res = cur.fetchall()
        for qt in res:
            author_id = qt[1]
            author = ctx.guild.get_member(author_id)
            if author is None:
                author = await self.bot.fetch_user(author_id)
            await ctx.channel.send(f"```\n{qt[3].replace('`', '')}``` - {common.get_nick_or_name(author)}")
        cur.close()
        self.pool.putconn(conn)
