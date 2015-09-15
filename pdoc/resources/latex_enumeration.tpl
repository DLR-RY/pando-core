\begin{tabular}{lcl}
\toprule
\textbf{Name} & \textbf{Value} & \textbf{Description} \\
\midrule
<% for entry in enumeration.entries %>
<< entry.name >> & << entry.value >> & << entry.description >> \\
<% endfor %>
\bottomrule
\end{tabular}
