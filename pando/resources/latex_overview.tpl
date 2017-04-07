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

