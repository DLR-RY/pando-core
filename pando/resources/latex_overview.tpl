<#-
Copyright (c) 2015, 2017, German Aerospace Center (DLR)

This file is part of the development version of the pando library.

This Source Code Form is subject to the terms of the Mozilla Public
License, v. 2.0. If a copy of the MPL was not distributed with this
file, You can obtain one at http://mozilla.org/MPL/2.0/.

Authors:
- 2015, 2017, Fabian Greif (DLR RY-AVS)
-#>
\begin{tabular}{<% for heading in headings %>c<% endfor %>l}
\toprule
<% for heading in headings %>
\textbf{<< heading >>} &
<%- endfor %> \textbf{Name} \\
\midrule
<% for row in entries %>
<% for column in row %>
<< column >> <% if not loop.last %> & <% endif %>
<%- endfor %> \\
<% endfor %>
\bottomrule
\end{tabular}

