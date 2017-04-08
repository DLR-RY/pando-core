{#-
Copyright (c) 2015-2017, German Aerospace Center (DLR)

This file is part of the development version of the pando library.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Authors:
- 2015-2017, Fabian Greif (DLR RY-AVS)
-#}
<?xml version="1.0" encoding="UTF-8"?>
<!-- Generated at {{ time }} -->
<svg width="{{ width * 2 }}" height="{{ height * 2 }}">
  <defs>
    <style type="text/css"><![CDATA[
      rect {
        fill-opacity:1;
        stroke:#000000;
        stroke-width:0.2mm;
        stroke-miterlimit:4;
        stroke-opacity:1;
        stroke-dasharray:none;
        stroke-dashoffset:0
      }
      
      rect.id {
      	fill:#fce94f;
      }
      
      rect.size {
      	fill:#ffffff;
      }
      
      text {
      	font-size:12px;
      	font-style:normal;
      	font-variant:normal;
      	font-weight:300;
      	line-height:150%;
      	letter-spacing:0px;
      	word-spacing:0px;
      	fill:#000000;
      	fill-opacity:1;
      	stroke:none;
      	font-family:Frutiger;
      }
      
      text.size {
        font-size:10px;
      }
      
      text.sizeback {
        font-size:10px;
        fill:none;
        fill-opacity:1;
        stroke:#FFFFFF;
        stroke-width:3;
        stroke-linecap:butt;
        stroke-linejoin:miter;
        stroke-opacity:1;
      }
      
      path {
        color:#000000;
        fill:none;
        stroke:#000000;
        stroke-width:0.4mm;
        stroke-linecap:butt;
        stroke-linejoin:miter;
        stroke-miterlimit:4;
        stroke-opacity:1;
        stroke-dasharray:none;
        stroke-dashoffset:0;
        marker:none;
        visibility:visible;
        display:inline;
        overflow:visible;
        enable-background:accumulate;
      }
    ]]></style>
  </defs>

<!--<rect x="0" y="0" width="{{ width * 2 }}" height="{{ height * 2 }}" style="fill:#ffffff;fill-opacity:1" />-->

<g transform="scale(2 2)">
<g transform="translate({{ xOffset }},{{ yOffset }})">
{% for element in elements %}
{% if element.type == "element" %}
<g transform="translate({{ element.x }},0)">
  <rect x="0" y="0" width="{{ element.width }}" height="40" class="id" />

  {% for e in element.parameterName %}
  <text x="{{ element.width / 2 }}" y="{{ e.y }}" text-anchor="middle" xml:space="preserve">{{ e.text }}</text>
  {% endfor %}
  <rect x="0" y="40" width="{{ element.width }}" height="30" class="size" />
  <text x="{{ element.width / 2 }}" y="52" text-anchor="middle" class="size">{{ element.parameterType }}</text>
  <text x="{{ element.width / 2 }}" y="63" text-anchor="middle" class="size">{% if element.parameterWidth == 0 %}variable{% elif element.parameterType == "Octet String" or element.parameterType == "ASCII String" %}{{ element.parameterWidth // 8 }} Byte{% else %}{{ element.parameterWidth }} Bit{% endif %}</text>
</g>
{% elif element.type == "repeaterStart" %}
<g transform="translate({{ element.x }},0)">
  <path d="m 10,-{{ element.depth * 5 }} -5,0 0,{{ 85 - 20 + element.depth * 20 }} 5,0" />
</g>
{% elif element.type == "repeaterEnd" %}
<g transform="translate({{ element.x }},0)">
  <path d="m 0,-{{ element.depth * 5 }} 5,0 0,{{ 85 - 20 + element.depth * 20 }} -5,0" />
</g>
<text x="{{ element.textposition }}" y="{{ 85 - 15 + element.depth * 15 - 2 }}" text-anchor="middle" class="sizeback">{{ element.repeaterRepeatText }}</text>
<text x="{{ element.textposition }}" y="{{ 85 - 15 + element.depth * 15 - 2 }}" text-anchor="middle" class="size">{{ element.repeaterRepeatText }}</text>
{% endif %}
{% endfor %}
</g>
</g>
</svg>

