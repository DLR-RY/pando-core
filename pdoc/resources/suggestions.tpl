{% if parameters|length > 0 %}
  <!-- Telecommand parameter mapping -->
  <telecommandParameters>
{% for parameter in parameters %}
    <parameterMapping sid="" uid="{{ parameter }}" />
{% endfor %}
  </telecommandParameters>
{% endif %}

{% if telemetries|length > 0 %}
  <!-- Telemetry mapping -->
{% for telemetry in telemetries %}
  <application name="{{ telemetry.name }}" apid="{{ telemetry.apid }}">
    <telemetries>
      <telemetry sid="" uid="{{ telemetry.uid }}">
{% for parameter in telemetry.parameters %}
        <parameterMapping sid="{{ parameter.sid }}" uid="{{ parameter.uid }}" />
{% endfor %}
      </telemetry>
    </telemetries>
  </application>

{% endfor %}
{% endif %}
{% if telecommands|length > 0 %}
  <!-- Telecommand mapping -->
  <application>
    <telecommands>
{% for telecommand in telecommands %}
      <telecommandMappingRef sid="" uid="{{ telecommand.uid }}" />
{% endfor %}
    </telecommands>
  </application>
{% endif %}