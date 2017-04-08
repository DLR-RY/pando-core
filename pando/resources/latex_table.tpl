<#-
Copyright (c) 2015-2017, German Aerospace Center (DLR)

This file is part of the development version of the pando library.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Authors:
- 2015-2017, Fabian Greif (DLR RY-AVS)
-#>
\begin{longtable}{p{.97\textwidth}}
%\caption{}
\label{tab:<< identifier >>}\\
\toprule
\textbf{Name:} << packet.name >> \\
\endfirsthead
\multicolumn{1}{r}{continued from previous page} \\
\midrule
\endhead
\multicolumn{1}{r}{continued on next page} \\
\endfoot
\endlastfoot

## if packet.critical
\midrule
\textbf{Critical command:} << packet.critical >> \\
## endif

## if packet.designators
	\midrule
	\textbf{Designators:}\newline
	\begin{tabular}{@{\hskip .3cm}ll@{}}
    ## for designator in packet.designators
		\emph{<< designator.name >>} & << designator.value >> \\
    ## endfor
	\end{tabular}\\
## endif

\midrule
\textbf{Parameter:}<% if not parameters %> No parameters<% else %>\setlength{\parskip}{6pt}

## if image
	\includegraphics[width=150mm]{<< image >>}
	\textbf{Parameter Description:}
### The following empty line is important to force Latex to generate a paragraph 

## endif
## if useMinMax
		\begin{tabular}{@{\hskip .3cm}lllllll@{}}
		\textbf{Name} & \textbf{Type} & \textbf{Width} & \textbf{Unit} & \textbf{Min} & \textbf{Max} & \textbf{Description} \\
		## for parameter in parameters
			\emph{<< parameter.name >>} & << parameter.type >> & <% if parameter.width == 0 %>variable<% else %><< parameter.width >> Bit<% endif %> & << parameter.unit >> & <<parameter.min >> & << parameter.max >> & << parameter.description >> \\
		## endfor
		\end{tabular}
## else
		\begin{tabular}{@{\hskip .3cm}llll@{}}
		\textbf{Name} & \textbf{Type} & \textbf{Width} & \textbf{Description} \\
		## for parameter in parameters
			\emph{<< parameter.name >>} & << parameter.type >> & <% if parameter.width == 0 %>variable<% else %><< parameter.width >> Bit<% endif %> & << parameter.description >> \\
		## endfor
		\end{tabular}
## endif
<% endif %> \\

## if packet.relevantTelemetry|length > 0
\midrule
\textbf{Expected Response:}\setlength{\parskip}{6pt}

    ## for tm in packet.relevantTelemetry
~~~\llap{\textbullet}~~<< tm.name >> \\
    ## endfor
## endif
## if packet.description
    \midrule
    \textbf{Description:}\setlength{\parskip}{6pt}

    << packet.description >>\\
    ## endif
## for heading, text in packet.additional
    ## if text
	\midrule
	\textbf{<< heading >>:}\setlength{\parskip}{6pt}

	<< text >>\\
	## endif
## endfor

\bottomrule
\end{longtable}
