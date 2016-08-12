## if parameters|length > 0
  <!-- Telecommand parameter mapping -->
  <telecommandParameters>
## for parameter in parameters
    <parameterMapping sid="" uid="{{ parameter }}" />
## endfor
  </telecommandParameters>

## endif

## if events|length > 0
  <!-- Event mapping -->
## for event in events
  <application name="{{ event.name }}" apid="{{ event.apid }}">
    <events>
      <event sid="" uid="{{ event.uid }}">
## for parameter in event.parameters
        <parameterMapping sid="{{ parameter.sid }}" uid="{{ parameter.uid }}" />
## endfor
      </event>
    </events>
  </application>

## endfor
## endif
## if telemetries|length > 0
  <!-- Telemetry mapping -->
## for telemetry in telemetries
  <application name="{{ telemetry.name }}" apid="{{ telemetry.apid }}">
    <telemetries>
      <telemetry sid="" uid="{{ telemetry.uid }}">
## for parameter in telemetry.parameters
        <parameterMapping sid="{{ parameter.sid }}" uid="{{ parameter.uid }}" />
## endfor
      </telemetry>
    </telemetries>
  </application>

## endfor
## endif
## if telecommands|length > 0
  <!-- Telecommand mapping -->
  <application>
    <telecommands>
## for telecommand in telecommands
      <telecommandMappingRef sid="" uid="{{ telecommand.uid }}" />
## endfor
    </telecommands>
  </application>
## endif