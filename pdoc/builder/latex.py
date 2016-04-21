
import os
import textwrap

from .. import model

from . import builder

def xstr(s):
	""" Converts None to an empty string """
	return '' if s is None else str(s)


class TableBuilder(builder.Builder):
	
	class State:
		def __init__(self):
			self.useMinMax = False
	
	def __init__(self, model, templateFile, imagePath):
		builder.Builder.__init__(self, model)
		
		if templateFile is None:
			templateFile = '#latex_table.tpl'
		self.templateFile = templateFile
		self.imagePath = imagePath
	
	def generate(self, outpath):
		self.outpath = outpath
		
		for packet in self.model.telemetries.values():
			self._generatePacket(packet)
		for packet in self.model.telecommands.values():
			self._generatePacket(packet)
		
	def _generatePacket(self, packet):
		parameters = []
		self.state = self.State()
		for parameter in packet.parameters:
			self._packetParameter(parameter, parameters)
		
		if self.imagePath is None:
			image = None
		else:
			image = os.path.join(self.imagePath, packet.uid)
				
		substitutions = {
			'identifier': packet.uid,
			'parameters': parameters,
			'packet': packet,
			'image': image,
			'useMinMax': self.state.useMinMax,
		}
		
		filename = os.path.join(self.outpath, "%s.tex" % packet.uid)
		
		template = self._template(self.templateFile, alternateMarking=True)
		self._write(filename, template.render(substitutions) + "\n")

	def _packetParameter(self, parameter, parameters):
		
		if parameter.valueType == model.Parameter.RANGE:
		  minimum = xstr(parameter.valueRange.min)
		  maximum = xstr(parameter.valueRange.max)
		elif parameter.valueType == model.Parameter.FIXED:
		  minimum = xstr(parameter.value)
		  maximum = xstr(parameter.value)
		else:
		  minimum = ""
		  maximum = ""
		
		parameters.append({
			'name': parameter.name,
			'description': parameter.description,
			'shortName': parameter.shortName,
			'type': str(parameter.type),
			'width': parameter.type.width,
			'unit': xstr(parameter.unit),
			'min': minimum,
			'max': maximum,
		})
		
		if parameter.valueType == model.Parameter.RANGE or parameter.valueType == model.Parameter.FIXED:
			self.state.useMinMax = True
		
		if isinstance(parameter, model.Group):
			self._packetGroup(parameter, parameters)
	
	def _packetGroup(self, group, parameters):
		for parameter in group.parameters:
			self._packetParameter(parameter, parameters)


class OverviewBuilder(builder.Builder):
	
	def __init__(self, packets, templateFile):
		builder.Builder.__init__(self, packets)
		
		if templateFile is None:
			templateFile = '#latex_overview.tpl'
		self.templateFile = templateFile

	def generate(self, outpath, target):
		if target is None or target == '':
			target = 'overview.tex'
		
		basename, ext = os.path.splitext(target)
		self._generateOverview(os.path.join(outpath, basename + '_tm' + ext), list(self.model.telemetries.values()))
		self._generateOverview(os.path.join(outpath, basename + '_tc' + ext), list(self.model.telecommands.values()))

	def _generateOverview(self, filename, packets):
		headings = []
		for packet in packets:
			for designator in packet.designators:
				if designator['name'] not in headings:
					headings.append(designator['name'])
		
		entries = []
		for packet in packets:
			entry = []
			for d in headings:
				for designator in packet.designators:
					if designator['name'] == d:
						entry.append(designator['value'])
						break
				else:
					entry.append("-")
			entry.append(packet.name)
			entries.append(entry)
		
		# 'headings' is one shorter than every entry of 'entries'.
		substitutions = {
			'headings': headings,
			'entries': sorted(entries),
		}
		
		template = self._template(self.templateFile, alternateMarking=True)
		self._write(filename, template.render(substitutions) + "\n")


class EnumerationBuilder(builder.Builder):

	def __init__(self, enumerations, templateFile):
		builder.Builder.__init__(self, None)
		self.enumerations = enumerations

		if templateFile is None:
			templateFile = '#latex_enumeration.tpl'
		self.templateFile = templateFile

	def generate(self, outpath):
		self.outpath = outpath

		for enumeration in self.enumerations.values():
			self._generateEnumeration(enumeration)

	def _generateEnumeration(self, enumeration):
		substitutions = {
			'enumeration': enumeration,
		}

		filename = os.path.join(self.outpath, "enumeration_%s.tex" % enumeration.uid)
		template = self._template(self.templateFile, alternateMarking=True)
		self._write(filename, template.render(substitutions) + "\n")

