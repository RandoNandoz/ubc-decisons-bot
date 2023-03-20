"""
This is a bot for the UBC applicant server to display their received admissions decisions.
"""
from datetime import datetime
from os import environ

import discord
import pymongo
from discord.ext import commands

from ApplicantDecision import ApplicantDecision
from Campus import Campus
from Decision import Decision
from UBCProgram import UBCProgram

import dateutil.parser

intents = discord.Intents.all()

bot = commands.Bot(intents=intents, debug_guilds=[environ["TEST_GUILD_ID"]])

mongo_client = pymongo.MongoClient(environ["MONGO_URL"])

db = mongo_client["ubc-admissions-bot"]

reviewed_decisions = db["reviewed_decisions"]

unreviewed_decisions = db["unreviewed_decisions"]


@bot.event
async def on_ready():
    print("Bot is ready")


# default callable is noop https://stackoverflow.com/questions/690622/whats-a-standard-way-to-do-a-no-op-in-python
async def send_applicant_to_channel(applicant: ApplicantDecision, channel: discord.TextChannel,
                                    message_cb: callable = lambda *x, **y: None):
    user = await bot.fetch_user(applicant.discord_id)
    embed = discord.Embed(
        title=f"{user} {applicant.decision.value} for {applicant.program.value} at UBC {applicant.campus.value}!",
        color=discord.Color.blurple(), description=f"**User:** {user}\n"
                                                   f"**Campus:** {applicant.campus.value}\n"
                                                   f"**Program:** {applicant.program.value}\n"
                                                   f"**Decision:** {applicant.decision.value}\n"
                                                   f"**Decision Date:** {applicant.decision_date.strftime('%Y-%m-%d')}\n"
                                                   f"**International:** {applicant.international}\n"
                                                   f"**Curriculum:** {applicant.curriculum}\n"
                                                   f"**Average:** {applicant.average}\n"
                                                   f"**Application Date:** {applicant.application_date.strftime('%Y-%m-%d')}\n"
                                                   f"**Comments:** {applicant.comments}\n"
                                                   f"**Intended Major:** {applicant.intended_major}\n"
                                                   f"**Attachment:** {applicant.attachment}\n")

    sent_message = await channel.send(embed=embed)
    message_cb(applicant, sent_message)

async def get_unreviewed_decisions() -> list[str]:
    users = [d['discord_username'] for d in unreviewed_decisions.find({})]
    unique_users = list(set(users))
    return unique_users


@bot.slash_command(name="accept_all", description="Review a decision")
async def accept_all(ctx: discord.ApplicationContext):
    for d in unreviewed_decisions.find({}):
        member = await bot.fetch_user(d["discord_id"])
        await ctx.respond(f"Accepting {member.mention}")
        await accept(ctx, member)

# noinspection PyTypeChecker
@bot.slash_command(name="accept", description="Accept a decision")
async def accept(ctx: discord.ApplicationContext, applicant: discord.Option(discord.Member, description="The applicant to accept", required=True, autocomplete=get_unreviewed_decisions)):
    db_applicant = ApplicantDecision.from_dict(unreviewed_decisions.find_one({"discord_id": applicant.id}))
    if db_applicant is None:
        await ctx.respond(f"Could not find {applicant.mention} in the database!")
        return
    # guaranteed to be a discord.TextChannel object
    # noinspection PyTypeChecker
    await send_applicant_to_channel(db_applicant, bot.get_channel(int(environ["ACCEPTED_CHANNEL_ID"])))
    review_channel: discord.TextChannel = await bot.fetch_channel(int(environ["REVIEW_CHANNEL_ID"]))
    review_msg: discord.Message = await review_channel.fetch_message(db_applicant.msg_id)
    await review_msg.delete()
    unreviewed_decisions.delete_one({"discord_id": applicant.id})
    reviewed_decisions.insert_one(db_applicant.__dict__())
    await ctx.respond(f"Accepted {applicant.mention}!")


# noinspection PyTypeChecker
@bot.slash_command(name="reject", description="Reject a decision")
async def reject(ctx: discord.ApplicationContext, applicant: discord.Option(discord.Member, description="The applicant to reject", required=True, autocomplete=get_unreviewed_decisions)):
    try:
        applicant_decision = ApplicantDecision.from_dict(unreviewed_decisions.find_one({"discord_id": applicant.id}))
        review_channel: discord.TextChannel = await bot.fetch_channel(int(environ["REVIEW_CHANNEL_ID"]))
        db_applicant = unreviewed_decisions.find_one({"discord_id": applicant.id})
        review_msg: discord.Message = await review_channel.fetch_message(db_applicant["msg_id"])
        await review_msg.delete()
        await ctx.respond(f"Rejected {applicant.mention}!")
        unreviewed_decisions.delete_one(db_applicant)
    except TypeError:
        await ctx.respond(f"Could not find {applicant.mention} in the database!")



@bot.slash_command(name="decision", description="Submit your UBC admissions decision for review")
async def decision(ctx: discord.ApplicationContext, campus: discord.Option(Campus,
                                                                           description="The UBC Campus you applied to, either Vancouver or Okanagan",
                                                                           required=True),
                   program: discord.Option(UBCProgram, description="The UBC program you applied to", required=True),
                   applicant_decision: discord.Option(Decision, description="The decision you received from UBC",
                                                      required=True), decision_date: discord.Option(str,
                                                                                                    description="The date you received your decision, preferably in YYYY-MM-DD",
                                                                                                    required=True),
                   international: discord.Option(bool, description="Whether you are an international student or not",
                                                 required=True), curriculum: discord.Option(str,
                                                                                            description="The curriculum you're using, for example, BC, AB, IB, American, etc.",
                                                                                            required=True),
                   average: discord.Option(str, description="Your average, for example, 90.5", required=True, min=0,
                                           max=100), application_date: discord.Option(str,
                                                                                      description="The date you applied to UBC, preferably in YYYY-MM-DD",
                                                                                      required=True),
                   comments: discord.Option(str, description="Any comments you have about your decision",
                                            required=False), intended_major: discord.Option(str,
                                                                                            description="The program you intended to apply to, if you applied to a different program",
                                                                                            required=False),
                   attachment: discord.Option(discord.Attachment, description="An attachment to your decision",
                                              required=False)):
    try:
        decision_date = dateutil.parser.parse(decision_date)
        application_date = dateutil.parser.parse(application_date)
        applicant_decision = ApplicantDecision(discord_username=ctx.author.name, discord_id=ctx.author.id,
                                               campus=campus, program=program, decision=applicant_decision,
                                               decision_date=decision_date, international=international,
                                               curriculum=curriculum, average=average,
                                               application_date=application_date, comments=comments,
                                               intended_major=intended_major, attachment=attachment)

        def add_msg_id_to_applicant(applicant: ApplicantDecision, msg: discord.Message):
            applicant.msg_id = msg.id
            unreviewed_decisions.insert_one(applicant_decision.__dict__())

        # REVIEW_CHANNEL_ID is guaranteed to be a discord.TextChannel object
        # noinspection PyTypeChecker
        await send_applicant_to_channel(applicant_decision,
                                        await bot.fetch_channel(int(environ["REVIEW_CHANNEL_ID"])), add_msg_id_to_applicant)

        await ctx.respond(
            "Success! Your decision has been submitted for review by the mods. Expect a response within 24 hours")
    except ValueError:
        await ctx.respond(
            "There was an issue parsing your date format, please use YYYY-MM-DD")

bot.run(environ["DISCORD_TOKEN"])
