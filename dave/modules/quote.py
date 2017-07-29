"""Quote system"""
from sqlalchemy.exc import SQLAlchemyError
import dave.module
import dave.config
import uuid
import random
from dave.models import Quote
from twisted.words.protocols.irc import assembleFormattedText, attributes as A

@dave.module.help("Syntax: aq [quote] (-- attribute). Add a quote.")
@dave.module.command(["aq", "addquote"], "(.*?)(?: (?:--|—) ?(.+?))?$")
def add_quote(bot, args, sender, source):
    generated_uuid = str(uuid.uuid4())
    quote = Quote(id=generated_uuid, quote=args[0], attributed=args[1], added_by=sender)
    dave.config.session.add(quote)

    bot.reply(source, sender, assembleFormattedText(
        A.normal["Successfully added quote: ", A.bold[args[0]], " by ",
                 (args[1] or sender)]))

    bot.msg(sender, "You can remove this quote later using \"dave dq {}\"".format(
        generated_uuid))

@dave.module.help("Syntax: q. Return a random quote.")
@dave.module.command(["q", "quote"])
def quote(bot, args, sender, source):
    query = dave.config.session.query(Quote)

    if not query.count():
        bot.reply(source, sender, "No quotes found.")
        return

    row = query.offset(
        random.randrange(query.count())
    ).first()

    bot.reply(source, sender, assembleFormattedText(A.normal[
        A.bold[row.quote], " by ", (row.attributed or row.added_by)
    ]))

@dave.module.help("Syntax: fq [search]. Search for a quote.")
@dave.module.command(["fq", "findquote"], "(.*)$")
def find_quote(bot, args, sender, source):
    try:
        quotes = dave.config.session.query(Quote).filter(
            (Quote.quote.op("~")(args[0])) | (Quote.attributed.op("~")(args[0]))
                | (Quote.added_by.op("~")(args[0]))
        ).all()
    except SQLAlchemyError as e:
        bot.reply(source, sender, SQLAlchemyError.__str__(e))
        return

    if len(quotes) == 0:
        bot.reply(source, sender, "No results for query.")

    if len(quotes) > 3:
        bot.reply(source, sender, "Your query yielded too many results ({}), here's a " \
                                  "random sample:".format(len(quotes)))
        quotes = random.sample(quotes, 3)

    for quote in quotes:
        bot.reply(source, sender, assembleFormattedText(A.normal[
            A.bold[quote.quote], " by ", (quote.attributed or quote.added_by)
        ]))

@dave.module.help("Syntax: dq [uuid]. Allow the quote owner to delete a quote.")
@dave.module.command(["dq", "deletequote"], "(.*)$")
def delete_quote(bot, args, sender, source):
    query = dave.config.session.query(Quote).filter(Quote.id == args[0])

    if not query.count():
        bot.reply(source, sender, "Couldn't find a quote with that UUID.")
        return

    query.delete()
    bot.reply(source, sender, "Successfully deleted quote.")