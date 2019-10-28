import discord
import datetime
import os
import struct
from PIL import Image

def changePNGColor(sourceFile, fromRgb, toRgb, deltaRank = 10):
    fromRgb = fromRgb.replace('#', '')
    toRgb = toRgb.replace('#', '')

    fromColor = struct.unpack('BBB', bytes.fromhex(fromRgb))
    toColor = struct.unpack('BBB', bytes.fromhex(toRgb))

    img = Image.open(sourceFile)
    img = img.convert("RGBA")
    pixdata = img.load()

    for x in range(0, img.size[0]):
        for y in range(0, img.size[1]):
            rdelta = pixdata[x, y][0] - fromColor[0]
            gdelta = pixdata[x, y][0] - fromColor[0]
            bdelta = pixdata[x, y][0] - fromColor[0]
            if abs(rdelta) <= deltaRank and abs(gdelta) <= deltaRank and abs(bdelta) <= deltaRank:
                pixdata[x, y] = (toColor[0] + rdelta, toColor[1] + gdelta, toColor[2] + bdelta, pixdata[x, y][3])

    img.save(os.path.dirname(sourceFile) + os.sep + f"{toRgb}" + os.path.splitext(sourceFile)[1])

def create_embed(title=None, title_url=None, author_avatar=None, author_name=None, author_url=None, description=None, image=None, thumbnail=None, footer_text=None, footer_icon=None, timestamp=None):

	e = discord.Embed(color=0x4595f4)

	if timestamp is None:
		pass
	elif timestamp == "True":
		e.timestamp = datetime.datetime.utcnow()

	e.title = title
	e.description = description

	if title_url is not None:
		e.url = title_url

	if image is not None:
		e.set_image(url=image)

	if thumbnail is not None:
		e.set_thumbnail(url=thumbnail)

	if footer_icon is None:
		if footer_text is None:
			pass
		else:
			e.set_footer(text=footer_text)

	else:
		if footer_text is None:
			e.set_footer(icon_url=footer_icon)
		else:
			e.set_footer(text=footer_text, icon_url=footer_icon)

	if author_url is None:
		e.set_author(icon_url=author_avatar.avatar_url, name=author_name)

	else:
		e.set_author(icon_url=author_avatar.avatar_url, name=author_name, url=author_url)

	return e