# -*- coding: utf-8 -*-
import textwrap

import PIL
from PIL import ImageFont, ImageDraw, Image
import os
import sys


def make_meme(topString, bottomString, img) -> Image:
	fontsize = int(round(img.size[1] / 6))
	draw = ImageDraw.Draw(img)
	impact = ImageFont.truetype(font=os.path.abspath('./data/impact.ttf'), size=fontsize)
	top_strings = textwrap.wrap(topString, width=40)
	bottom_strings = textwrap.wrap(bottomString, width=40)
	longest_top_string = ' '
	longest_bottom_string = ' '
	for string in top_strings:
		if draw.textsize(string, impact)[0] > draw.textsize(longest_top_string, impact)[0]:
			longest_top_string = string
	for string in bottom_strings:
		if draw.textsize(string, impact)[0] > draw.textsize(longest_bottom_string, impact)[0]:
			longest_bottom_string = string
	while draw.textsize(longest_top_string, impact)[0] > (img.size[0]-10):
		fontsize -= 1
		impact = ImageFont.truetype(font=os.path.abspath('./data/impact.ttf'), size=fontsize)
	i = 0
	for string in top_strings:
		draw.text(
			anchor='ms',
			font=impact,
			text=string,
			xy=(int(round(img.size[0]/2)), fontsize+2+(i*(fontsize+2))),
			align='center',
			fill=(255, 255, 255),
			stroke_fill=(0, 0, 0),
			stroke_width=int(round(fontsize/20))
		)
		i += 1
	fontsize = int(round(img.size[1]/6))
	impact = ImageFont.truetype(font=os.path.abspath('./data/impact.ttf'), size=fontsize)
	while draw.textsize(longest_bottom_string, impact)[0] > (img.size[0]-10):
		fontsize -= 1
		impact = ImageFont.truetype(font=os.path.abspath('./data/impact.ttf'), size=fontsize)
	i = 0
	for string in bottom_strings:
		draw.text(
			anchor='ms',
			font=impact,
			text=string,
			xy=(int(round(img.size[0]/2)), img.size[1]-10-(len(bottom_strings)-1-i)*(fontsize+2)),
			align='center',
			fill=(255, 255, 255),
			stroke_fill=(0, 0, 0),
			stroke_width=int(round(fontsize/20))
		)
		i += 1
	return img
