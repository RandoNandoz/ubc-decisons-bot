"""
This is a bot for the UBC applicant server to display their received admissions decisions.
"""
from datetime import datetime
from os import environ

import discord
import pymongo
from discord.ext import commands
from discord import default_permissions

from ApplicantDecision import ApplicantDecision
from Campus import Campus
from Decision import Decision
from UBCProgram import UBCProgram

intents = discord.Intents.all()

bot = commands.Bot(intents=intents, debug_guilds=[environ["TEST_GUILD_ID"]])

mongo_client = pymongo.MongoClient(environ["MONGO_URL"])

db = mongo_client["ubc-admissions-bot"]

reviewed_decisions = db["reviewed_decisions"]

unreviewed_decisions = db["unreviewed_decisions"]


async def send_applicant_to_review(applicant_decision: ApplicantDecision):
    review_channel = bot.get_channel(int(environ["REVIEW_CHANNEL_ID"]))
    accepted_channel = bot.get_channel(int(environ["ACCEPTED_CHANNEL_ID"]))
    user = await bot.fetch_user(applicant_decision.discord_id)

    review_embed = discord.Embed(title="New Applicant Decision", color=discord.Color.blurple(),
        description=f"**User:** {user}\n"
                    f"**Discord ID:** {applicant_decision.discord_id}\n"
                    f"**Campus:** {applicant_decision.campus.value}\n"
                    f"**Program:** {applicant_decision.program.value}\n"
                    f"**Decision:** {applicant_decision.decision.value}\n"
                    f"**Decision Date:** {applicant_decision.decision_date.strftime('%Y-%m-%d')}\n"
                    f"**International:** {applicant_decision.international}\n"
                    f"**Curriculum:** {applicant_decision.curriculum}\n"
                    f"**Average:** {applicant_decision.average}\n"
                    f"**Application Date:** {applicant_decision.application_date.strftime('%Y-%m-%d')}\n"
                    f"**Comments:** {applicant_decision.comments}\n"
                    f"**Intended Major:** {applicant_decision.intended_major}\n")

    review_embed.set_image(url=user.display_avatar)

    class ReviewView(discord.ui.View):
        @discord.ui.button(label="Accept", style=discord.ButtonStyle.green, emoji="✅")
        async def accept(self, button: discord.ui.Button, interaction: discord.Interaction):
            reviewed_decisions.insert_one(applicant_decision.__dict__())
            unreviewed_decisions.delete_one({"discord_id": applicant_decision.discord_id})
            await interaction.response.send_message("Accepted", ephemeral=True)
            accepted_embed = discord.Embed(
                title=f"{user} {applicant_decision.decision.value} for {applicant_decision.program.value} at UBC {applicant_decision.campus.value}!",
                color=discord.Color.blurple(), description=f"**User:** {user}\n"
                                                           f"**Campus:** {applicant_decision.campus.value}\n"
                                                           f"**Program:** {applicant_decision.program.value}\n"
                                                           f"**Decision:** {applicant_decision.decision.value}\n"
                                                           f"**Decision Date:** {applicant_decision.decision_date.strftime('%Y-%m-%d')}\n"
                                                           f"**International:** {applicant_decision.international}\n"
                                                           f"**Curriculum:** {applicant_decision.curriculum}\n"
                                                           f"**Average:** {applicant_decision.average}\n"
                                                           f"**Application Date:** {applicant_decision.application_date.strftime('%Y-%m-%d')}\n"
                                                           f"**Comments:** {applicant_decision.comments}\n"
                                                           f"**Intended Major:** {applicant_decision.intended_major}\n")

            accepted_embed.set_image(url=user.display_avatar)

            await accepted_channel.send(embed=accepted_embed)

            # button.disabled = True

            await interaction.message.delete()

        @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, emoji="❌")
        async def reject(self, button: discord.ui.Button, interaction: discord.Interaction):
            unreviewed_decisions.delete_one({"discord_id": applicant_decision.discord_id})
            await interaction.response.send_message(f"Rejected, make sure to PM why <@{applicant_decision.discord_id}>",
                                                    ephemeral=True)
            await interaction.message.delete()

    await review_channel.send(embed=review_embed, view=ReviewView())


@bot.event
async def on_ready():
    print("Bot is ready")


@bot.slash_command(name="decision")
async def decision(ctx: discord.ApplicationContext,
        campus: discord.Option(Campus, description="The UBC Campus you applied to, either Vancouver or Okanagan",
                               required=True),
        program: discord.Option(UBCProgram, description="The UBC program you applied to", required=True),
        applicant_decision: discord.Option(Decision, description="The decision you received from UBC", required=True),
        decision_date: discord.Option(str, description="The date you received your decision, in YYYY-MM-DD",
                                      required=True),
        international: discord.Option(bool, description="Whether you are an international student or not",
                                      required=True), curriculum: discord.Option(str,
                                                                                 description="The curriculum you're using, for example, BC, AB, IB, American, etc.",
                                                                                 required=True),
        average: discord.Option(float, description="Your average, for example, 90.5", required=True, min=0, max=100),
        application_date: discord.Option(str, description="The date you applied to UBC, in YYYY-MM-DD", required=True),
        comments: discord.Option(str, description="Any comments you have about your decision", required=False),
        intended_major: discord.Option(str,
                                       description="The program you intended to apply to, if you applied to a different program",
                                       required=False)):
    try:
        decision_date = datetime.strptime(decision_date, "%Y-%m-%d")
        application_date = datetime.strptime(application_date, "%Y-%m-%d")
        applicant_decision = ApplicantDecision(discord_username=ctx.author.name, discord_id=ctx.author.id,
            campus=campus, program=program, decision=applicant_decision, decision_date=decision_date,
            international=international, curriculum=curriculum, average=average, application_date=application_date,
            comments=comments, intended_major=intended_major)

        unreviewed_decisions.insert_one(applicant_decision.__dict__())

        await send_applicant_to_review(applicant_decision)

        await ctx.respond(
            "Success! Your decision has been submitted for review by the mods. Expect a response within 24 hours")
    except ValueError:
        await ctx.respond("Invalid date format, please use YYYY-MM-DD")
    except:
        await ctx.respond("An error occurred, pinging the dev: <@215994239920766977>")


bot.run(environ["DISCORD_TOKEN"])
