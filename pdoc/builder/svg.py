
import os
import textwrap

from .. import model

from . import builder


class ImageBuilder(builder.Builder):

	class DecodingState:
		def __init__(self):
			self.x = 0
			self.elementCount = 0

	def __init__(self, model, templateFile=None, align=False):
		builder.Builder.__init__(self, model)
		
		self.boxWidth = 90
		self.groupDelimiterWidth = 10
		self.textHeight = 14
		
		if templateFile is None:
			templateFile = '#svg.tpl'
		self.templateFile = templateFile
		self.align = align
		
		self.state = self.DecodingState()

	def generate(self, outpath):
		self.outpath = outpath
		
		for packet in self.model.telemetries.values():
			filename = os.path.join(self.outpath, "%s.svg" % packet.uid)
			self._write(filename, self.generatePacket(packet) + "\n")
		for packet in self.model.telecommands.values():
			filename = os.path.join(self.outpath, "%s.svg" % packet.uid)
			self._write(filename, self.generatePacket(packet) + "\n")
		
	def generatePacket(self, packet):
		self.state = self.DecodingState()
		elements = []
		
		for parameter in packet.parameters:
			self._packetParameter(parameter, elements)
		
		defaultWidth = 525
		if (self.state.x + 20) > defaultWidth:
			xOffset = 10
			width = self.state.x + 20
		else:
			if self.align:
				xOffset = 10
			else:
				xOffset = int((defaultWidth - (self.state.x)) / 2)
			width = defaultWidth
		height = 85 + (packet.depth - 1) * 20 + 5
		
		substitutions = {
			'elements': elements,
			'xOffset': xOffset,
			'yOffset': 5 + packet.depth * 5,
			'width': width,
			'height': height,
		}
		
		template = self._template(self.templateFile)
		return template.render(substitutions)

	def _packetParameter(self, parameter, elements):
		wrapper = textwrap.TextWrapper()
		wrapper.width = 14
		
		text = wrapper.wrap(parameter.name)
		
		texts = []
		offset = (40 - self.textHeight * len(text)) / 2 - 3
		for t in text:
			offset += self.textHeight
			texts.append({
				'text': t,
				'y': offset,
			})
	
		elements.append({
			'type': 'element',
			'parameterName': texts,
			'parameterType': str(parameter.type),
			'parameterWidth': parameter.type.width,
			'x': self.state.x,
			'width': self.boxWidth,
		})
		self.state.x += self.boxWidth
		self.state.elementCount += 1
		
		if isinstance(parameter, model.Group):
			self._packetGroup(parameter, elements)

	def _packetGroup(self, group, elements):
		elements.append({
			'type': 'groupStart',
			'x': self.state.x,
			'width': self.groupDelimiterWidth,
			'depth': group.depth,
		})
		self.state.x += self.groupDelimiterWidth
		startPosition = self.state.x
		startCount = self.state.elementCount
		
		for parameter in group.parameters:
			self._packetParameter(parameter, elements)
		
		if elements[-1]["type"] == "groupEnd":
			self.state.x -= int(self.groupDelimiterWidth / 2)
		
		groupWidth = self.state.elementCount - startCount
		elements.append({
			'type': 'groupEnd',
			'x': self.state.x,
			'width': self.groupDelimiterWidth,
			'depth': group.depth,
			'textposition': int(startPosition + (self.state.x - startPosition) / 2),
			'groupRepeatText': ("repeated %s times" if (groupWidth > 1) else "rep. %s times") % group.name,
		})
		self.state.x += self.groupDelimiterWidth

