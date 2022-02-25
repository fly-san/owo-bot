import threading

from discord.ext import commands
from pyspark.shell import spark
from pyspark.sql.functions import *
from pyspark.sql.types import *


def get_show_string(df, n=20, truncate=True, vertical=False):
    if isinstance(truncate, bool) and truncate:
        return df._jdf.showString(n, 20, vertical)
    else:
        return df._jdf.showString(n, int(truncate), vertical)


class Stats(commands.Cog):
    def __init__(self, bot, bpath):
        self.bot = bot
        self.spark_lock = threading.Lock()
        sc = spark.sparkContext

        schema = StructType([
            StructField("author_id", LongType(), False),
            StructField("channel_id", LongType(), False),
            StructField("time", DoubleType(), False),
            StructField("msg", StringType(), False)
        ])

        self.df = spark.read \
            .option("header", True) \
            .option("multiLine", True) \
            .option("escape", '"') \
            .schema(schema) \
            .csv(bpath + "msgs.csv")

        self.df = self.df.withColumn("u_time", from_unixtime("time")).drop("time")

    def get_messages_by_author(self, author):
        rejectChans = [937308889425281034, 946545522167124000, 779413828051664966]
        return self.df.filter((col("author_id") == author.id) & (~self.df["channel_id"].isin(rejectChans)))

    async def check_allow_query(self, ctx):
        if self.spark_lock.locked():
            await ctx.channel.send(f"Sorry, another query seems to be running")
            return False

    @commands.group()
    async def stats(self, ctx):
        pass

    @stats.command(brief="when do you procrastinate?")
    async def activity(self, ctx):
        if not self.check_allow_query(ctx):
            return
        with self.spark_lock:
            dfa = self.get_messages_by_author(ctx.author)
            dft = dfa.groupBy(hour("u_time").alias("hour")).agg(count("u_time").alias("count"))
            dft = dft.orderBy("hour")
            res = get_show_string(dft, n=24)
            await ctx.channel.send(f'```\n{res}total messages: {dfa.count()}```')

    @stats.command(brief="use your words")
    async def words(self, ctx):
        if not self.check_allow_query(ctx):
            return
        with self.spark_lock:
            dfa = self.get_messages_by_author(ctx.author)
            dfw = dfa.withColumn("word", explode(split(col("msg"), " "))) \
                .groupBy("word") \
                .count() \
                .orderBy("count", ascending=False)
            res = get_show_string(dfw, n=20)
            await ctx.channel.send(f'```\n{res.replace("`", "")}\n```')
