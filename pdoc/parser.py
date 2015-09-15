#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import re
import pkgutil
import copy

import urllib.request
import urllib.parse

def pkgutil_get_filename(package, resource):
	"""Rewrite of pkgutil.get_data() that return the file path.
	"""
	loader = pkgutil.get_loader(package)
	if loader is None or not hasattr(loader, 'get_data'):
		return None
	mod = sys.modules.get(package) or loader.load_module(package)
	if mod is None or not hasattr(mod, '__file__'):
		return None

	# Modify the resource name to be compatible with the loader.get_data
	# signature - an os.path format "filename" starting with the dirname of
	# the package's __file__
	parts = resource.split('/')
	parts.insert(0, os.path.dirname(mod.__file__))
	resource_name = os.path.normpath(os.path.join(*parts))
	
	return resource_name

catalogfile = pkgutil_get_filename('pdoc', 'resources/catalog.xml')
os.environ['XML_CATALOG_FILES'] = urllib.parse.urljoin('file:', urllib.request.pathname2url(catalogfile))

# lxml must be imported **after** the Catalog file have been set, otherwise
# it runs into an endless loop during verification.
import lxml.etree

from . import model


class ParserException(Exception):
	pass


class Parser:
	
	class ParameterList:
		def __init__(self):
			self.parameters = []
		def appendParameter(self, parameter):
			self.parameters.append(parameter)
	
	def parse(self, filename, xsdfile = None):
		rootnode = self._validateAndParse(filename, xsdfile)
		
		m = model.Model()
		listParameters = {}

		# Parse packet/parameter structure
		for serviceNode in rootnode.iterfind('service'):
			# TODO failure codes
			serviceName = serviceNode.attrib.get('name', '')
			
			for enumerationsNode in serviceNode.iterfind('enumerations'):
				for node in enumerationsNode.iterchildren('enumeration'):
					enumeration = self._parseEnumeration(node)
					m.enumerations[enumeration.uid] = enumeration
		
		for serviceNode in rootnode.iterfind('service'):
			serviceName = serviceNode.attrib.get('name', '')
			for parametersNode in serviceNode.iterfind('parameters'):
				for node in parametersNode.iterchildren():
					self._parseParameter(node, m.parameters, m.enumerations, listParameters)
					# Parameter is automatically added to the list of parameters

		for serviceNode in rootnode.iterfind('service'):
			serviceName = serviceNode.attrib.get('name', '')
			for telemtriesNode in serviceNode.iterfind('telemetries'):
				for node in telemtriesNode.iterchildren('telemetry'):
					tm = self._parseTelemetry(node, m.parameters, m.enumerations, listParameters)
					m.appendTelemetryPacket(tm)
			
			for telecommandsNode in serviceNode.iterfind('telecommands'):
				for node in telecommandsNode.iterchildren('telecommand'):
					tc = self._parseTelecommand(node, m.parameters, m.enumerations, m.telemetries, listParameters)
					m.appendTelecommandPacket(tc)
		
		# Parse SCOS mapping information
		for mappingNode in rootnode.iterfind('mapping'):
			subsystemId = int(mappingNode.attrib["subsystem"], 0)
			subsystem = m.getOrAddSubsystem(subsystemId)
			
			for node in mappingNode.iterfind('enumerations/telecommandEnumerationMapping'):
				uid, sid = self._parseMapping(node)
				enumeration = m.enumerations[uid]
				subsystem.telecommandEnumerations[uid] = model.EnumerationMapping(sid=sid, enumeration=enumeration)
			for node in mappingNode.iterfind('enumerations/telemetryEnumerationMapping'):
				uid, sid = self._parseMapping(node)
				enumeration = m.enumerations[uid]
				subsystem.telemetryEnumerations[uid] = model.EnumerationMapping(sid=sid, enumeration=enumeration)
			
			for node in mappingNode.iterfind('telecommandParameters/parameterMapping'):
				uid, sid = self._parseMapping(node)
				parameter = m.parameters[uid]
				subsystem.telecommandParameters[uid] = model.ParameterMapping(sid=sid, parameter=parameter)
			
			for node in mappingNode.iterfind('application'):
				app = self._parseApplicationMapping(node, m)
				subsystem.applications[app.apid] = app
		
		# Extract telecommand and telemetry enumerations
		# Might be done during parsing to be more efficient
		for subsystem in m.subsystems.values():
			for application in subsystem.applications.values():
				for tc in application.getTelecommands():
					for p in tc.telecommand.getParametersAsFlattenedList():
						if p.type.identifier == model.ParameterType.ENUMERATION:
							e = p.type.enumeration
							m.telecommandEnumerations[e] = m.enumerations[e]
				
				for tm in application.getTelemetries():
					for p in tm.telemetry.getParametersAsFlattenedList():
						if p.type.identifier == model.ParameterType.ENUMERATION:
							e = p.type.enumeration
							m.telemetryEnumerations[e] = m.enumerations[e]
		
		return m


	def _validateAndParse(self, filename, xsdfile):
		try:
			# parse the xml-file
			parser = lxml.etree.XMLParser(no_network=True)
			xmlroot = lxml.etree.parse(filename, parser=parser)
			xmlroot.xinclude()
			
			if xsdfile is None:
				xsdfile = pkgutil_get_filename('pdoc', 'resources/schema/telecommunication.xsd')

			xmlschema = lxml.etree.parse(xsdfile, parser=parser)
			
			schema = lxml.etree.XMLSchema(xmlschema)
			schema.assertValid(xmlroot)
	
			rootnode = xmlroot.getroot()
		except OSError as e:
			raise ParserException(e)
		except (lxml.etree.DocumentInvalid, lxml.etree.XMLSyntaxError, lxml.etree.XMLSchemaParseError) as e:
			raise ParserException("While parsing '%s': %s" % (e.error_log[0].filename, e))
		except lxml.etree.XIncludeError as e:
			raise ParserException("While including '%s': %s" % (e.error_log[0].filename, e))
		
		if rootnode.tag != "telecommunication":
			raise ParserException("Expected rootnode 'telecommunication', got '%s' in file '%s'" %
									(rootnode.tag, filename))
		
		return rootnode
	
	def _parseTelemetry(self, node, referenceParameters, enumerations, lists):
		p = model.Telemetry(name=node.attrib["name"],
		                    uid=node.attrib["uid"],
		                    description=self._parseText(node, "description", ""))
		
		self._parseShortName(p, node)
		self._parseDesignators(p, node)
		self._parseServiceType(p, node)
		
		self._parseParameters(p, node.find("parameters"), referenceParameters, enumerations, lists)
		p.updateGroupDepth()
		
		parameters = p.getParametersAsFlattenedList()
		self._parseIdentificationParameter(p, node, parameters)
		self._parsePacketAdditionalFields(p, node)
		
		return p
	
	def _parseTelecommand(self, node, referenceParameters, enumerations, telemetries, lists):
		p = model.Telecommand(name=node.attrib["name"],
		                      uid=node.attrib["uid"],
		                      description=self._parseText(node, "description", ""))
		
		self._parseShortName(p, node)
		self._parseDesignators(p, node)
		self._parseServiceType(p, node)
		
		self._parseParameters(p, node.find("parameters"), referenceParameters, enumerations, lists)
		p.updateGroupDepth()
		self._parseParameterValues(p, node, enumerations)
		
		self._parsePacketAdditionalFields(p, node)
		
		for telemetryUid in node.iterfind("relevantTelemetry/telemetryRef"):
			uid = telemetryUid.attrib["uid"]
			telemetry = telemetries[uid]
			p.relevantTelemetry.append(telemetry)
		
		critical = self._parseText(node, "critical", "No")
		p.critical = {"Yes": True, "No": False}[critical]
		
		# TODO failureIdentification
		
		return p

	def _parseDesignators(self, packet, node):
		designatorNodes = node.find("designators")
		if designatorNodes is not None:
			for designator in designatorNodes.iterfind("designator"):
				packet.designators.append({
					"name":  designator.attrib["name"],
					"value": designator.attrib["value"],
				})
				
	def _parseServiceType(self, packet, node):
		packet.serviceType = int(node.findtext("serviceType"))
		packet.serviceSubtype = int(node.findtext("serviceSubtype"))
	
	def _parseShortName(self, packet, node):
		packet.shortName = node.findtext("shortName", "")
		
		if packet.shortName == "":
			packet.shortName = packet.name

	def _parseIdentificationParameter(self, packet, node, parameters):
		for parameterNode in node.iterfind("packetIdentification/identificationParameter"):
			value = parameterNode.attrib["value"]
			uid   = parameterNode.attrib["uid"]
			
			for p in parameters:
				if p.uid == uid:
					parameter = model.TelemetryIdentificationParameter(parameter=p, value=value)
					break
			else:
				raise ParserException("Identification parameter '%s' was not found in packet '%s'" % (uid, packet.uid))
			
			packet.identificationParameter.append(parameter)


	def _parsePacketAdditionalFields(self, packet, node):
		for key, defaultHeading in [('note', 'Note'),
									('effects', 'Effects'),		# only for telecommand
									('purpose', 'Purpose'),
									('recommendation', 'Recommendation'),
									('seeAlso', 'See Also'),]:
			text = self._parseText(node, key)
			if text is not None:
				packet.additional[defaultHeading] = text
	
	def _parseParameters(self, packet, node, referenceParameters, enumerations, lists):
		for parameterNode in node:
			parameters = self._parseParameter(parameterNode, referenceParameters, enumerations, lists)
			if parameters is not None:
				for parameter in parameters:
					packet.appendParameter(parameter)
	
	def _parseParameter(self, node, referenceParameters, enumerations, lists):
		parameters = []
		uid = node.attrib.get("uid", "")
		if node.tag == "parameter" or node.tag == "group":
			name = node.attrib.get("name")
			description = self._parseText(node, "description", "")
			
			parameterType = self._parseType(node)
			if node.tag == "parameter":
				parameter = model.Parameter(name=name, uid=uid, description=description, parameterType=parameterType)
			
				parameter.unit = node.attrib.get("unit")
			elif node.tag == "group":
				parameter = model.Group(name=name, uid=uid, description=description, parameterType=parameterType)
				self._parseParameters(parameter, node, referenceParameters, enumerations, lists)
			
			self._parseShortName(parameter, node)
			
			value, valueType, valueRange = self._parseParameterValue(node)
			if valueType is not None:
				parameter.value = value
				parameter.valueType = valueType
				parameter.valueRange = valueRange
			
			referenceParameters[parameter.uid] = parameter
			parameters.append(parameter)
		elif node.tag == "enumerationParameter":
			name = node.attrib.get("name")
			description = self._parseText(node, "description", "")
			enumName = node.attrib.get("enumeration")
			
			parameterType = model.EnumerationType(enumerations[enumName].width, enumName)
			parameter = model.Parameter(name=name, uid=uid, description=description, parameterType=parameterType)
			
			self._parseShortName(parameter, node)
			
			value, valueType, valueRange = self._parseParameterValue(node)
			if valueType is not None:
				if valueType == model.Parameter.RANGE:
					raise ParserException("Invalid value definition for enumeration '%s'. Only 'fixed' or 'default' permitted" % uid)
				
				enum = enumerations[enumName]
				entry = enum.getEntryByName(value)
				if entry == None:
					raise ParserException("Value '%s' not found in enumeration '%s'." % (value, uid))
				
				parameter.value = value
				parameter.valueType = valueType
				parameter.valueRange = valueRange
			
			referenceParameters[parameter.uid] = parameter
			parameters.append(parameter)
		elif node.tag == "list":
			parameterList = self.ParameterList()
			self._parseParameters(parameterList, node, referenceParameters, enumerations, lists)
			
			lists[uid] = parameterList
			parameters = parameterList.parameters
		elif node.tag == "parameterRef":
			# The parameter needs to be copied here. Otherwise the reference
			# parameter might be changed when we later assign fixed/default
			# values to parameters in the telecommand.
			if uid in lists:
				for p in lists[uid].parameters:
					parameter = copy.deepcopy(p)
					parameters.append(parameter)
			else:
				parameter = copy.deepcopy(referenceParameters[uid])
				parameters.append(parameter)
		elif node.tag == lxml.etree.Comment:
			return None
		elif node.tag in ["description", "shortName"]:
			# Description tags are already parsed for the group tags in their
			# handler. Nothing to do here.
			return None
		elif node.tag in ["fixed", "default", "range"]:
			return None
		else:
			raise ParserException("Unknow element '%s' found. Was expecting 'parameter|group|enumerationParameter|parameterRef'" % node.tag)
		
		return parameters


	def _parseText(self, node, tag, defaultValue=None):
		""" Removes indentation from text tags """
		text = node.findtext(tag, defaultValue)
		
		if text is not None:
			toStrip = None
			lines = []
			for line in text.split('\n'):
				if toStrip is None:
					if line == '' or line.isspace():
						continue
					
					# First line which is not only whitespace
					match = re.match('^(\s*)', text)
					toStrip = match.group(1)
				
				lines.append(line.lstrip(toStrip))
			text = ("\n".join(lines)).rstrip()
		
		return text

		
	def _parseType(self, node):
		parameterType = None
		typeattrib = node.attrib.get("type")
		for base in ["uint", "int", "float"]:
			if typeattrib.startswith(base):
				typeid = {
					"uint": model.ParameterType.UNSIGNED_INTEGER,
					"int": model.ParameterType.SIGNED_INTEGER,
					"float": model.ParameterType.REAL
				}[base]
				width = int(typeattrib[len(base):])
				parameterType = model.ParameterType(typeid, width)
				break
		else:
			if typeattrib == "octet":
				typeid = model.ParameterType.OCTET_STRING
				# convert width from bytes to bits
				width = int(node.attrib.get("width", 0)) * 8
			elif typeattrib == "ascii":
				typeid = model.ParameterType.ASCII_STRING
				# convert width from bytes to bits
				width = int(node.attrib.get("width", 0)) * 8
			elif typeattrib == "time4":
				typeid = model.ParameterType.TIME
				width = 4 * 8
			elif typeattrib == "time4.2":
				typeid = model.ParameterType.TIME
				width = 6 * 8
			else:
				raise ParserException("Invalid type name '%s'" % typeattrib)
			
			parameterType = model.ParameterType(typeid, width)
		return parameterType


	def _parseParameterValues(self, tc, node, enumerations):
		parameters = tc.getParametersAsFlattenedList()
		
		for parameterNode in node.iterfind("parameterValues/parameterValue"):
			uid = parameterNode.attrib.get("uid")
			
			value, valueType, valueRange = self._parseParameterValue(parameterNode)
			if valueType is not None:
				# Find corresponding parameter and set value
				for p in parameters:
					if uid == p.uid:
						if p.type.identifier is model.ParameterType.ENUMERATION:
							enum = enumerations[p.type.enumeration]
							entry = enum.getEntryByName(value)
							if entry == None:
								raise ParserException("Value '%s' not found in enumeration '%s'." % (value, uid))
							pass
						
						p.value = value
						p.valueType = valueType
						p.valueRange = valueRange
						break
				else:
					# No matching parameter found
					raise ParserException("During value definition: Parameter '%s' not found in telecommand '%s'!" % (uid, tc.uid))
	
	def _parseParameterValue(self, node):
		value = None
		valueType = None
		valueRange = None
		
		for tag in ["fixed", "default", "range"]:
			valueNode = node.find(tag)
			if valueNode is not None:
				if valueNode.tag == "fixed":
					value = valueNode.attrib.get("value")
					valueType = model.Parameter.FIXED
				elif valueNode.tag == "default":
					value = valueNode.attrib.get("value")
					valueType = model.Parameter.DEFAULT
				elif valueNode.tag == "range":
					value = valueNode.attrib.get("default", None)
					valueType = model.Parameter.RANGE
					valueRange = model.ParameterValueRange(
									minimum=valueNode.attrib.get("min"),
									maximum=valueNode.attrib.get("min"))

		return (value, valueType, valueRange)
	

	def _parseEnumeration(self, node):
		e = model.Enumeration(name=node.attrib.get("name"),
		                      uid=node.attrib.get("uid"),
		                      width=int(node.attrib.get("width")),
		                      description=self._parseText(node, "description", ""))
		
		self._parseShortName(e, node)
		
		for entry in node.iterfind("entry"):
			e.appendEntry(self._parseEnumerationEntry(entry))
		
		return e


	def _parseEnumerationEntry(self, node):
		entry = model.EnumerationEntry(node.attrib.get("name"),
									   node.attrib.get("value"),
									   self._parseText(node, "description", ""))
		return entry


	def _parseApplicationMapping(self, node, tmtcModel):
		""" Parse an application mapping.
		
		Returns a model.ApplicationMapping class.
		"""
		application = model.ApplicationMapping(name=node.attrib.get("name"),
	             					           apid=int(node.attrib["apid"], 0),
		 		                	           description=self._parseText(node, "description", ""))

		for telemetryNode in node.iterfind("telemetries/telemetry"):
			uid, sid = self._parseMapping(telemetryNode)
			
			telemetry = tmtcModel.telemetries[uid]
			telemetryMapping = model.TelemetryMapping(sid=sid, telemetry=telemetry)
			for parameterNode in telemetryNode.findall("parameterMapping"):
				uid, sid = self._parseMapping(parameterNode)
				try:
					parameter = tmtcModel.parameters[uid]
				except KeyError as e:
					raise ParserException("Parameter '%s' not found in mapping of '%s'!" % (uid, telemetry.uid))
				telemetryMapping.appendParameter(model.ParameterMapping(sid=sid, parameter=parameter))
			
			application.appendTelemetry(telemetryMapping)
		
		for telecommandNode in node.iterfind("telecommands/telecommandMappingRef"):
			uid, sid = self._parseMapping(telecommandNode)
			telecommand = tmtcModel.telecommands[uid]
			application.appendTelecommand(model.TelecommandMapping(sid=sid, telecommand=telecommand))
		
		return application
	
	def _parseMapping(self, node):
		return node.attrib["uid"], node.attrib["sid"]

