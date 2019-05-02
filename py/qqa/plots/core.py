"""
Core shared routines for plotting
"""

import bokeh

#- Default CSS to embed in every HTML file, to keep them standalone
#- instead of using a .css file in same directory
default_css = """
h1, h2, h3, h4, h5, p {
    font-family: Helvetica, Arial, sans-serif;
}

table {
  font-family: arial, sans-serif;
  border-collapse: collapse;
}

td, th {
  border: 1px solid #eeee;
  text-align: left;
  padding: 8px;
}

th {
  background-color: #cccccc;
}

tr:nth-child(even) {
  background-color: #eeeeee;
}


"""

bokeh_html_preamble = '''
<!DOCTYPE html>
<html lang="en-US">

<link
    href="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.css"
    rel="stylesheet" type="text/css"
>
<link
    href="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.css"
    rel="stylesheet" type="text/css"
>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-{version}.min.js"></script>
<script src="https://cdn.pydata.org/bokeh/release/bokeh-tables-{version}.min.js"></script>

<head>
<style>
{default_css}
</style>
</head>
'''.format(version=bokeh.__version__, default_css=default_css)

