import dash
# For Dash 2.0:
# from dash import html, dcc
# For dash < 2.0
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import math
import numpy as np
import pandas as pd
import plotly.graph_objs as go
from textwrap import dedent

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# set page title
app.title = 'Sigmoid TBC Taxation'

server = app.server

app.config['suppress_callback_exceptions']=True

# slider/graph ranges
n_points = 100 # number of data points to be plotted for each graph

min_supply = 10000
max_supply = 1000000
supply_step = 1000

min_price = 0
max_price = 1000
price_step = 10

min_slope = 0.1e9
max_slope = 100e9
slope_step = 0.1e9

k_min = 0
k_max = 500
k_step = 10

t_min = 0
t_max = 1.0
t_step = 0.01 

# helper functions
def format_number(n):
	abbrevs = ['','k','M','B','T']
	n = float(n)
	ix = max(0,min(len(abbrevs)-1, int(math.floor(0 if n == 0 else math.log10(abs(n))/3))))
	return '{:.2f}{}'.format(n / 10**(3 * ix), abbrevs[ix])


# app layout
app.layout = html.Div([
	html.Div(
		[html.H2('Taxation of Sigmoidal Token Bonding Curves')]),
		html.Div(
			[html.P(
				['This interactive dashboard refers to the different fundraising scenarios outlined in our ',
				 html.A('Medium Post', href='https://medium.com/molecule-blog/designing-different-fundraising-scenarios-with-sigmoidal-token-bonding-curves-ceafc734ed97'),
				 ' about Sigmoidal Token Bonding Curves. Please refer to the article for more details about the mathematical functions used for plotting.',
				]),
			 html.P(
			 	['Select a ',
			 	 html.B('Token Supply'),
			 	 ', choose a ',
			 	 html.B('Scenario'),
			 	 ' and use the sliders to see how the different parameters influence the curves.',
			 	]),
			 html.P(
			 	['The parameters control the following properties:',
			 	 html.Ul(
			 	 	[html.Li(
			 	 		[html.B('a'), 
			 	 		 ': Maximum Token Price'],
			 	 		style={'margin': '10px 5px 0 0'}),
			 	 	 html.Li(
			 	 		[html.B('b'),
			 	 		 ': Curve Inflection Point'],
			 	 		style={'margin': '0 5px 0 0'}),
			 	 	 html.Li(
			 	 	 	[html.B('c'),
			 	 	 	 ': Curve Slope'],
			 	 	 	style={'margin': '0 5px 0 0'}),
			 	 	 html.Li(
			 	 	 	[html.B('k'),
			 	 	 	 ': Vertical Displacement'],
			 	 	 	style={'margin': '0 5px 0 0'}),
			 	 	 html.Li(
			 	 	 	[html.B('h'),
			 	 	 	 ': Horizontal Displacement'],
			 	 	 	style={'margin': '0 5px 0 0'}),
			 	 	 html.Li(
			 	 	 	[html.B('t'),
			 	 	 	 ': Tax Rate'],
			 	 	 	style={'margin': '0 5px 0 0'})
			 	 	],
			 	 	style={'padding-left': '50px'})
			 	 ]),
			 html.P(
			 	['''
			 	 For most scenarios, the parameters are coupled in such a way that negative taxes are not possible and the underlying scenario constraints always hold true. 
				 Choose the last dropwdown menu entry ''',
				 html.B('No Constraints'),
				 ' to be able to experiment without any enforced rules.'])
			]),
	html.Hr(),
	html.Div([
		html.Div([
			html.H3('Settings'),
			html.Div(id='supply-slider-output-container'),
			dcc.Slider(
				id='supply-slider',
				min=min_supply,
				max=max_supply,
				step=supply_step,
				value=max_supply/2
			),
			html.Div('Scenario Selection:'),
			dcc.Dropdown(
				id='scenario-dropdown',
				options=[
					{'label': 'No Taxation', 'value': 's0'},
					{'label': 'Constant Taxation', 'value': 's1'},
					{'label': 'Decreasing Taxation', 'value': 's2'},
					{'label': 'Increasing Taxation', 'value': 's3'},
					{'label': 'Bell-Shaped Taxation', 'value': 's4'},
					{'label': 'No Constraints', 'value': 's5'},
				],
				value='s0'),
			html.Hr(),
			html.Div(
				id='curve-parameter-container-1',
				children=[
					html.H5(id='curve-parameter-header-1'),
					html.Div(id='a1-slider-output-container'),
					dcc.Slider(
						id='a1-slider',
						min=min_price,
						max=max_price,
						step=price_step,
						value=max_price/2),
					html.Div(id='b1-slider-output-container'),
					dcc.Slider(
						id='b1-slider',
						min=min_supply,
						max=max_supply/2,
						value=max_supply/4,
						step=supply_step),
					html.Div(id='c1-slider-output-container'),
				 	dcc.Slider(
				 		id='c1-slider',
				 		min=min_slope,
						max=max_slope,
						step=slope_step,
						value=10e09),
				 	html.Div(
				 		id='k1-slider-container',
				 		children=[
				 			html.Div(id='k1-slider-output-container'),
				 			dcc.Slider(
				 				id='k1-slider',
				 				min=k_min,
				 				max=k_max,
				 				step=k_step,
				 				value=k_max/2)],
				 		style={'display': 'none'}),
				 	html.Div(
				 		id='t1-slider-container',
				 		children=[
				 			html.Div(id='t1-slider-output-container'),
				 			dcc.Slider(
				 				id='t1-slider',
				 				min=t_min,
				 				max=t_max,
				 				step=t_step,
				 				value=t_max/5)],
				 		style={'display': 'none'})
				],
				style={'display': 'none'}),
			html.Div(
				id='curve-parameter-container-2',
				children=[
					html.H5(id='curve-parameter-header-2'),
				 	html.Div(id='a2-slider-output-container'),
				 	dcc.Slider(
				 		id='a2-slider',
				 		min=min_price,
						max=max_price,
						step=price_step,
						value=max_price/2),
				 	html.Div(id='b2-slider-output-container'),
				 	dcc.Slider(
				 		id='b2-slider',
				 		min=min_supply,
						max=max_supply/2,
						value=max_supply/4,
						step=supply_step),
				 	html.Div(id='c2-slider-output-container'),
				 	dcc.Slider(
				 		id='c2-slider',
				 		min=min_slope,
						max=max_slope,
						step=slope_step,
						value=10e09),
				 	html.Div(
				 		id='h2-slider-container',
				 		children=[
				 			html.Div(id='h2-slider-output-container'),
				 			dcc.Slider(
				 				id='h2-slider',
				 				min=min_supply,
				 				max=max_supply,
				 				step=supply_step,
				 				value=max_supply/10)],
				 		style={'display': 'none'})
				],
				style={'display': 'none'})
		], className="two columns sidebar"),
		html.Div(
			id='graph-div',
			children=[
				html.Div([
					html.Div(
						id='price-graph-container',
						style={'display': 'none'},
						children=[
							dcc.Graph(
								id='price-graph'
							)
						]
					),
					html.Div(
						id='tax-graph-container',
						style={'display': 'none'},
						children=[
							dcc.Graph(
								id='tax-graph'
							)
						]
					)
				], className="four columns"),

				html.Div([
					html.Div(
						id='col-graph-container',
						style={'display': 'none'},
						children=[
							dcc.Graph(
								id='col-graph'
							)
						]
					),
					html.Div(
						id='fund-graph-container',
						style={'display': 'none'},
						children=[
							dcc.Graph(
								id='fund-graph'
							)
						]
					)
				], className="four columns"),
			]
		)
	])
])

# display supply slider value
@app.callback(
	Output('supply-slider-output-container', 'children'),
	[Input('supply-slider', 'value')])
def update_supply_slider_output(supply_value):
	return 'Token Supply: {}'.format(format_number(supply_value))


# update a2-slider ranges based on a1-value
@app.callback(
	[Output('a2-slider', 'max'),
	 Output('a2-slider', 'min'),
	 Output('a2-slider', 'value')],
	[Input('scenario-dropdown', 'value'),
	 Input('a1-slider', 'max'),
	 Input('a1-slider', 'min'),
	 Input('a1-slider', 'value')])
def adjust_a_slider(scenario_value, a1_max, a1_min, a1_value):
	if scenario_value in ['s1', 's2', 's3', 's4', 's5']:
		return [
			a1_max,
			a1_min,
			a1_value
		]

	else:
		return [0, 0, 0]


# update b1-slider ranges based on selected supply
@app.callback(
	[Output('b1-slider', 'max'),
	 Output('b1-slider', 'value')],
	[Input('supply-slider', 'value')])
def adjust_b1_slider(supply_value):
	return [
		supply_value,
		supply_value/2
		]

# update b2-slider ranges based on b1-value
@app.callback(
	[Output('b2-slider', 'max'),
	 Output('b2-slider', 'min'),
	 Output('b2-slider', 'value')
	 ],
	[Input('scenario-dropdown', 'value'),
	 Input('b1-slider', 'max'),
	 Input('b1-slider', 'min'),
	 Input('b1-slider', 'value')])
def adjust_b2_slider(scenario_value, b1_max, b1_min, b1_value):
	if scenario_value in ['s1', 's2', 's3', 's4', 's5']:
		return [
			b1_max,
			b1_min,
			b1_value
			]

	else:
		return [0, 0, 0]

# update c2-slider ranges based on c1-value
@app.callback(
	[Output('c2-slider', 'max'),
	 Output('c2-slider', 'min'),
	 Output('c2-slider', 'value')
	],
	[Input('scenario-dropdown', 'value'),
	 Input('c1-slider', 'max'),
	 Input('c1-slider', 'min'),
	 Input('c1-slider', 'value')])
def adjust_c2_slider(scenario_value, c1_max, c1_min, c1_value):
	if scenario_value in ['s1', 's2', 's3', 's4', 's5']:
		return [
			c1_max,
			c1_min,
			c1_value
			]

	else:
		return [0, 0, 0]


# update k1-slider range
@app.callback(
	[Output('k1-slider', 'value')],
	[Input('scenario-dropdown', 'value')],
	[State('k1-slider', 'value')])
def adjust_k1_slider(scenario_value, k1_value):
	if scenario_value in [None, 's0', 's1', 's2', 's3', 's4']:
		return [
			k_max/2
			]
	elif scenario_value == 's5':
		return [
			0
			]


# update h2-slider range
@app.callback(
	[Output('h2-slider', 'max'),
	 Output('h2-slider', 'value')],
	[Input('scenario-dropdown', 'value'),
	 Input('b1-slider', 'max'),
	 Input('b1-slider', 'value')],
	[State('h2-slider', 'value')])
def adjust_h2_slider(scenario_value, b1_max, b1_value, h2_value):
	
	# inflection point of sell curve needs to lie within supply range
	h2_max = (b1_max - b1_value)

	# only reduce h value if it exceeds new max
	if h2_value > h2_max:
		h2_value = h2_max

	if scenario_value in [None, 's0', 's1', 's2', 's3', 's4']:
		return [
			h2_max,
			h2_value
			]
	elif scenario_value == 's5':
		return [
			h2_max,
			0
			]


# adjust available curve parameter sections & sliders
@app.callback(
	[Output('curve-parameter-container-1', 'style'),
	 Output('curve-parameter-header-1', 'children'),
	 Output('k1-slider-container', 'style'),
	 Output('t1-slider-container', 'style'),
	 Output('curve-parameter-container-2', 'style'),
	 Output('curve-parameter-header-2', 'children'),
	 Output('h2-slider-container', 'style'),
	 Output('a2-slider', 'disabled'),
	 Output('b2-slider', 'disabled'),
	 Output('c2-slider', 'disabled')],
	[Input('scenario-dropdown', 'value')])
def display_curve_parameter_sections(scenario_value):
	if scenario_value == 's0':
		return [
			{'display': 'block'},
			'Curve Parameters',
			{'display': 'none'},
			{'display': 'none'},
			{'display': 'none'},
			None,
			{'display': 'none'},
			True,
			True,
			True]

	elif scenario_value == 's1':
		return [
			{'display': 'block'},
			'Buy Curve Parameters',
			{'display': 'block'},
			{'display': 'none'},
			{'display': 'block'},
			'Sell Curve Parameters',
			{'display': 'none'},
			True,
			True,
			True]

	elif scenario_value == 's2':
		return [
			{'display': 'block'},
			'Buy Curve Parameters',
			{'display': 'block'},
			{'display': 'none'},
			{'display': 'block'},
			'Sell Curve Parameters',
			{'display': 'none'},
			True,
			True,
			True]

	elif scenario_value == 's3':
		return [
			{'display': 'block'},
			'Buy Curve Parameters',
			{'display': 'none'},
			{'display': 'block'},
			{'display': 'block'},
			'Sell Curve Parameters',
			{'display': 'none'},
			True,
			True,
			True]

	elif scenario_value == 's4':
		return [
			{'display': 'block'},
			'Buy Curve Parameters',
			{'display': 'none'},
			{'display': 'none'},
			{'display': 'block'},
			'Sell Curve Parameters',
			{'display': 'block'},
			True,
			True,
			True]

	elif scenario_value == 's5':
		return [
			{'display': 'block'},
			'Buy Curve Parameters',
			{'display': 'block'},
			{'display': 'none'},
			{'display': 'block'},
			'Sell Curve Parameters',
			{'display': 'block'},
			False,
			False,
			False]

	else:
		return [
			{'display': 'none'},
			None,
			{'display': 'none'},
			{'display': 'none'},
			{'display': 'none'},
			None,
			{'display': 'none'},
			True,
			True,
			True]


# display curve parameter slider values
@app.callback(
	[Output('a1-slider-output-container', 'children'),
 	 Output('b1-slider-output-container', 'children'),
 	 Output('c1-slider-output-container', 'children'),
 	 Output('k1-slider-output-container', 'children'),
 	 Output('t1-slider-output-container', 'children'),
 	 Output('a2-slider-output-container', 'children'),
 	 Output('b2-slider-output-container', 'children'),
 	 Output('c2-slider-output-container', 'children'),
 	 Output('h2-slider-output-container', 'children')],
 	[Input('a1-slider', 'value'),
 	 Input('b1-slider', 'value'),
 	 Input('c1-slider', 'value'),
 	 Input('k1-slider', 'value'),
 	 Input('t1-slider', 'value'),
 	 Input('a2-slider', 'value'),
 	 Input('b2-slider', 'value'),
 	 Input('c2-slider', 'value'),
 	 Input('h2-slider', 'value')])
def update_slider_outputs(a1_value, b1_value, c1_value, k1_value, t1_value,
						  a2_value, b2_value, c2_value, h2_value):
 	return ('a: {}'.format(a1_value),
 			'b: {}'.format(b1_value),
 			'c: {}'.format(format_number(c1_value)),
 			'k: {}'.format(k1_value),
 			't: {}'.format(t1_value),
 			'a: {}'.format(a2_value),
 			'b: {}'.format(b2_value),
 			'c: {}'.format(format_number(c2_value)),
 			'h: {}'.format(h2_value))


@app.callback(
	[Output('price-graph-container', 'style'),
	 Output('price-graph', 'figure'),
	 Output('col-graph-container', 'style'),
	 Output('col-graph', 'figure'),
	 Output('tax-graph-container', 'style'),
	 Output('tax-graph', 'figure'),
	 Output('fund-graph-container', 'style'),
	 Output('fund-graph', 'figure')],
	[Input('scenario-dropdown', 'value'),
	 Input('supply-slider', 'value'),
	 Input('a1-slider', 'value'),
	 Input('b1-slider', 'value'),
	 Input('c1-slider', 'value'),
	 Input('k1-slider', 'value'),
	 Input('t1-slider', 'value'),
	 Input('a2-slider', 'value'),
	 Input('b2-slider', 'value'),
	 Input('c2-slider', 'value'),
	 Input('h2-slider', 'value')])
def update_graphs(scenario_value, supply_value, a1_value, b1_value, c1_value, 
	k1_value, t1_value, a2_value, b2_value, c2_value, h2_value):

	# supply vector
	s = np.arange(0., supply_value + 1, supply_value/n_points)

	# s0
	def buy_price(x, a, b, c):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
	def buy_collateral(x, a, b, c):
		return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - (a*np.sqrt(b**2 + c))

	# s1
	def buy_price_const(x, a, b, c, k):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1) + k
	def sell_price_const(x, a, b, c):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
	def buy_collateral_const(x, a, b, c, k):
		return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) + (k - a*np.sqrt(b**2 + c)) + k*x
	def sell_collateral_const(x, a, b, c):
		return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - (a*np.sqrt(b**2 + c))

	# s2
	def buy_price_dec(x, a, b, c, k):
		return (a - k/2) * ((x - b) / np.sqrt(c + (x - b)**2) + 1) + k
	def sell_price_dec(x, a, b, c):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
	def buy_collateral_dec(x, a, b, c, k):
		return (a - k/2)*(np.sqrt(b**2 - 2 * b * x + c + x**2) + x) + (k - (a - k/2)*np.sqrt(b**2 + c)) + k*x
	def sell_collateral_dec(x, a, b, c):
		return a*(np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - a*np.sqrt(b**2 + c)

	# s3
	def buy_price_inc(x, a, b, c, t):
		return (a/(1 - t)) * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
	def sell_price_inc(x, a, b, c):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
	def buy_collateral_inc(x, a, b, c, t):
		return (a/(1 - t)) * (np.sqrt((b - x)**2 + c) + x) - (a/(1 - t)) * np.sqrt(b**2 + c)
	def sell_collateral_inc(x, a, b, c):
		return a * (np.sqrt(b**2 - 2*b*x + c + x**2) + x) - a*np.sqrt(b**2 + c)

	# s4
	def buy_price_bell(x, a, b, c):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1)
	def sell_price_bell(x, a, b, c, h):
		return a * ((x - h - b) / np.sqrt(c + (x - h - b)**2) + 1)
	def buy_collateral_bell(x, a, b, c):
		return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) - a*np.sqrt(b**2 + c)
	def sell_collateral_bell(x, a, b, c, h):
		return a * (np.sqrt((b + h - x)**2 + c) + x) - (a*np.sqrt((b + h)**2 + c))

	# s5
	def buy_price_no(x, a, b, c, k):
		return a * ((x - b) / np.sqrt(c + (x - b)**2) + 1) + k
	def sell_price_no(x, a, b, c, h):
		return a * ((x - h - b) / np.sqrt(c + (x - h - b)**2) + 1)
	def buy_collateral_no(x, a, b, c, k):
		return a * (np.sqrt(b**2 - 2 * b * x + c + x**2) + x) + (k - a*np.sqrt(b**2 + c)) + k*x
	def sell_collateral_no(x, a, b, c, h):
		return a * (np.sqrt((b + h - x)**2 + c) + x) - (a*np.sqrt((b + h)**2 + c))



	# create graphs
	if scenario_value is None:
		return [
			{'display': 'none'},
			{},
			{'display': 'none'},
			{},
			{'display': 'none'},
			{},
			{'display': 'none'},
			{}
		]

	elif scenario_value == 's0':
		# data
		d = {'supply': s,
			 'buy_price': buy_price(s, a1_value, b1_value, c1_value),
			 'buy_col': buy_collateral(s, a1_value, b1_value, c1_value)}
		df = pd.DataFrame(data=d)
		df['buy_col_text'] = df['buy_col'].apply(format_number) # hover labels

		return [
			{'display': 'block'},
			{'data': [
				go.Scatter(
					x=df['supply'],
					y=df['buy_price'],
					mode='lines')],
			 'layout': go.Layout(
			 	title='Price Graph',
			 	xaxis={'title': 'Supply'},
			 	yaxis={
          			'title': 'Price',
          			'rangemode': 'nonnegative',
          			'hoverformat': '.2f'
          		})
			},
			{'display': 'block'},
			{'data': [
				go.Scatter(
					x=df['supply'],
					y=df['buy_col'],
					text=df['buy_col_text'],
					mode='lines',
					hoverinfo='text')
			],
			 'layout': go.Layout(
			 	title='Collateral Graph',
			 	xaxis={'title': 'Supply'},
			 	yaxis={
			 		'title': 'Collateral',
			 		'rangemode': 'nonnegative'})
			},
			{'display': 'none'},
			{},
			{'display': 'none'},
			{}
			]
	elif scenario_value == 's1':
		# data
		d = {'supply': s,
			 'buy_price': buy_price_const(s, a1_value, b1_value, c1_value, k1_value),
			 'sell_price': sell_price_const(s, a2_value, b2_value, c2_value),
			 'buy_col': buy_collateral_const(s, a1_value, b1_value, c1_value, k1_value),
			 'sell_col': sell_collateral_const(s, a2_value, b2_value, c2_value)}

	elif scenario_value == 's2':
		# data
		d = {'supply': s,
			 'buy_price': buy_price_dec(s, a1_value, b1_value, c1_value, k1_value),
			 'sell_price': sell_price_dec(s, a2_value, b2_value, c2_value),
			 'buy_col': buy_collateral_dec(s, a1_value, b1_value, c1_value, k1_value),
			 'sell_col': sell_collateral_dec(s, a2_value, b2_value, c2_value)}

	elif scenario_value == 's3':
		d = {'supply': s,
			 'buy_price': buy_price_inc(s, a1_value, b1_value, c1_value, t1_value),
			 'sell_price': sell_price_inc(s, a2_value, b2_value, c2_value),
			 'buy_col': buy_collateral_inc(s, a1_value, b1_value, c1_value, t1_value),
			 'sell_col': sell_collateral_inc(s, a2_value, b2_value, c2_value)}

	elif scenario_value == 's4':
		d = {'supply': s,
			 'buy_price': buy_price_bell(s, a1_value, b1_value, c1_value),
			 'sell_price': sell_price_bell(s, a2_value, b2_value, c2_value, h2_value),
			 'buy_col': buy_collateral_bell(s, a1_value, b1_value, c1_value),
			 'sell_col': sell_collateral_bell(s, a2_value, b2_value, c2_value, h2_value)}

	elif scenario_value == 's5':
		d = {'supply': s,
			 'buy_price': buy_price_no(s, a1_value, b1_value, c1_value, k1_value),
			 'sell_price': sell_price_no(s, a2_value, b2_value, c2_value, h2_value),
			 'buy_col': buy_collateral_no(s, a1_value, b1_value, c1_value, k1_value),
			 'sell_col': sell_collateral_no(s, a2_value, b2_value, c2_value, h2_value)}

	# convert to pandas dataframe
	df = pd.DataFrame(data=d)

	# compute tax and fund metrics
	df['tax_rate'] = np.around(1 - df['sell_price']/df['buy_price'], decimals=4)
	df['tax_amount'] = np.around(df['buy_price'] - df['sell_price'], decimals=4)
	df['fund_rate'] = np.around(1 - df['sell_col']/df['buy_col'], decimals=4)
	df['fund_amount'] = np.around(df['buy_col'] - df['sell_col'], decimals=4)

	# hover labels
	df['buy_col_text'] = df['buy_col'].apply(format_number)
	df['sell_col_text'] = df['sell_col'].apply(format_number)
	df['fund_rate_text'] = np.around(df['fund_rate'], decimals=2).map('{:.2f}'.format)
	df['fund_amount_text'] = df['fund_amount'].apply(format_number)

	# create graphs
	price_trace1 = go.Scatter(
		x=df['supply'],
		y=df['buy_price'],
		mode='lines',
		name='Buy')

	price_trace2 = go.Scatter(
		x=df['supply'],
		y=df['sell_price'],
		mode='lines',
		name='Sell')

	col_trace1 = go.Scatter(
		x=df['supply'],
		y=df['buy_col'],
		mode='lines',
		name='Buy',
		text=df['buy_col_text'],
		hoverinfo='text')

	col_trace2 = go.Scatter(
		x=df['supply'],
		y=df['sell_col'],
		mode='lines',
		name='Sell',
		text=df['sell_col_text'],
		hoverinfo='text')

	tax_rate_trace = go.Scatter(
		x=df['supply'],
		y=df['tax_rate'],
		mode='lines',
		line = {'color': '#2ca02c'},
		name='Tax Rate')

	tax_amount_trace = go.Scatter(
		x=df['supply'],
		y=df['tax_amount'],
		yaxis='y2',
		mode='lines',
		line = {'color': '#d62728'},
		name='Tax Amount')

	fund_rate_trace = go.Scatter(
		x=df['supply'],
		y=df['fund_rate'],
		mode='lines',
		line = {'color': '#2ca02c'},
		name='Fund Rate',
		text=df['fund_rate_text'],
		hoverinfo='text')

	fund_amount_trace = go.Scatter(
		x=df['supply'],
		y=df['fund_amount'],
		yaxis='y2',
		mode='lines',
		line = {'color': '#d62728'},
		name='Fund Amount',
		text=df['fund_amount_text'],
		hoverinfo='text')

	return [
		{'display': 'block'},
		{'data': [price_trace1, price_trace2],
		 'layout': go.Layout(
		 	title='Price Graph',
		 	xaxis={'title': 'Supply'},
          	yaxis={
          		'title': 'Price',
          		'rangemode': 'nonnegative',
          		'hoverformat': '.2f'},
          	legend={'orientation': 'h'})
		},
		{'display': 'block'},
		{'data': [col_trace1, col_trace2],
		 'layout': go.Layout(
		 	title='Collateral Graph',
		 	xaxis={'title': 'Supply'},
          	yaxis={
          		'title': 'Collateral',
          		'rangemode': 'nonnegative'},
          	legend={'orientation': 'h'})
		},
		{'display': 'block'},
		{'data': [tax_rate_trace, tax_amount_trace],
		 'layout': go.Layout(
		 	title='Tax Graph',
		 	xaxis={'title': 'Supply'},
          	yaxis={
          		'title': 'Rate',
          		'range': [0.0, 1.0],
          		'rangemode': 'nonnegative',
          		'hoverformat': '.2f',
          		'titlefont': {'color': '#2ca02c'},
    			'tickfont': {'color': '#2ca02c'}},
          	yaxis2={
          		'title': 'Amount',
          		'rangemode': 'nonnegative',
          		'hoverformat': '.2f',
          		'overlaying': 'y',
    			'side': 'right',
    			'showline': True,
    			'titlefont': {'color': '#d62728'},
    			'tickfont': {'color': '#d62728'}},
    		legend={'orientation': 'h'}
    		)},
		{'display': 'block'},
		{'data': [fund_rate_trace, fund_amount_trace],
		 'layout': go.Layout(
		 	title='Fund Graph',
		 	xaxis={'title': 'Supply'},
          	yaxis={
          		'title': 'Rate',
          		'range': [0.0, 1.0],
          		'rangemode': 'nonnegative',
          		'titlefont': {'color': '#2ca02c'},
    			'tickfont': {'color': '#2ca02c'}},
          	yaxis2={
          		'title': 'Amount',
          		'rangemode': 'nonnegative',
          		'overlaying': 'y',
    			'side': 'right',
    			'showline': True,
    			'titlefont': {'color': '#d62728'},
    			'tickfont': {'color': '#d62728'}
    			},
    		legend={'orientation': 'h'}
    		)}
	]

[Output('price-graph-container', 'style'),
 Output('price-graph', 'figure'),
 Output('col-graph-container', 'style'),
 Output('col-graph', 'figure'),
 Output('tax-graph-container', 'style'),
 Output('tax-graph', 'figure'),
 Output('fund-graph-container', 'style'),
 Output('fund-graph', 'figure')]


if __name__ == '__main__':
	port = int(os.environ.get("PORT"))
	app.run_server(debug=False, host='0.0.0.0', port=port)
