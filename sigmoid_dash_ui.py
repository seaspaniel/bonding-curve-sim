import dash
from dash import html, dcc
from dash.dependencies import Input, Output, State

import plotly.graph_objs as go

import logging

import utils
#from sigmoid import Sigmoid
import sigmoid as sigmoid
import market

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

n_points = 100 # number of data points to be plotted for each graph

sigmoid_market = None

external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

app = dash.Dash(
    __name__,
    meta_tags=[{"name": "viewport", "content": "width=device-width"}],
    external_stylesheets=external_stylesheets,
    suppress_callback_exceptions=True,
)

def init_app(sigmoid):
    # set page title
    app.title = 'Sigmoid TBC Taxation'
    app.layout = html.Div([
        html.Div([
            html.Div([
                html.H2('Taxation of Sigmoidal Token Bonding Curves')
            ]),
                html.Div(
                    [html.P(
                        ['This interactive dashboard refers to the different fundraising scenarios outlined in the ',
                        html.A('Medium Post', href='https://medium.com/molecule-blog/designing-different-fundraising-scenarios-with-sigmoidal-token-bonding-curves-ceafc734ed97'),
                        ' about Sigmoidal Token Bonding Curves. Please refer to the article for more details about the mathematical functions used for plotting.',
                        ]),
                    html.Img(className="fit-picture",
                             src="assets/Molecule Buy_Sell Bonding Curve System Diagram.jpg",
                             alt="Molecule Buy and Sell Bonding Curve System Diagram"),
                #     html.P(
                #         ['Select a ',
                #         html.B('Token Supply'),
                #         ', choose a ',
                #         html.B('Scenario'),
                #         ' and use the sliders to see how the different parameters influence the curves.',
                #         ]),
                #     html.P(
                #         ['The parameters control the following properties:',
                #         html.Ul(
                #             [html.Li(
                #                 [html.B('a'), 
                #                 ': Maximum Token Price'],
                #                 style={'margin': '10px 5px 0 0'}),
                #             html.Li(
                #                 [html.B('b'),
                #                 ': Curve Inflection Point'],
                #                 style={'margin': '0 5px 0 0'}),
                #             html.Li(
                #                 [html.B('c'),
                #                 ': Curve Slope'],
                #                 style={'margin': '0 5px 0 0'}),
                #             html.Li(
                #                 [html.B('k'),
                #                 ': Vertical Displacement: Buy - Sell t(0)'],
                #                 style={'margin': '0 5px 0 0'}),
                #             html.Li(
                #                 [html.B('h'),
                #                 ': Horizontal Displacement: '],
                #                 style={'margin': '0 5px 0 0'}),
                #             html.Li(
                #                 [html.B('t'),
                #                 ': Tax Rate'],
                #                 style={'margin': '0 5px 0 0'})
                #             ],
                #             style={'padding-left': '50px'})
                #         ]),
                #     html.P(
                #         ['''
                #         For most scenarios, the parameters are coupled in such a way that negative taxes are not possible and the underlying scenario constraints always hold true. 
                #         Choose the scenario ''',
                #         html.B('No Constraints'),
                #         ' to be able to experiment without any enforced rules.'])
                    ]),
            html.Hr(),
            html.Div([
                # Side panel
                html.Div([
                    html.H3('Settings'),
                    html.Div(id='supply-slider-output-container'),
                    dcc.Slider(
                        id='supply-slider',
                        min=market.min_supply,
                        max=market.max_supply,
                        step=market.supply_step,
                        value=market.initial_supply
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
                                min=market.min_price,
                                max=market.max_price,
                                step=market.price_step,
                                value=market.max_price/2),
                            html.Div(id='b1-slider-output-container'),
                            dcc.Slider(
                                id='b1-slider',
                                min=market.min_supply,
                                max=market.max_supply/2,
                                value=market.max_supply/4,
                                step=market.supply_step),
                            html.Div(id='c1-slider-output-container'),
                            dcc.Slider(
                                id='c1-slider',
                                min=sigmoid.min_slope,
                                max=sigmoid.max_slope,
                                step=sigmoid.slope_step,
                                value=sigmoid.max_slope/10),
                            html.Div(
                                id='k1-slider-container',
                                children=[
                                    html.Div(id='k1-slider-output-container'),
                                    dcc.Slider(
                                        id='k1-slider',
                                        min=sigmoid.k_min,
                                        max=sigmoid.k_max,
                                        step=sigmoid.k_step,
                                        value=sigmoid.k_max/2)],
                                style={'display': 'none'}),
                            html.Div(
                                id='t1-slider-container',
                                children=[
                                    html.Div(id='t1-slider-output-container'),
                                    dcc.Slider(
                                        id='t1-slider',
                                        min=sigmoid.t_min,
                                        max=sigmoid.t_max,
                                        step=sigmoid.t_step,
                                        value=sigmoid.t_max/5)],
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
                                min=market.min_price,
                                max=market.max_price,
                                step=market.price_step,
                                value=market.max_price/2),
                            html.Div(id='b2-slider-output-container'),
                            dcc.Slider(
                                id='b2-slider',
                                min=market.min_supply,
                                max=market.max_supply/2,
                                value=market.max_supply/4,
                                step=market.supply_step),
                            html.Div(id='c2-slider-output-container'),
                            dcc.Slider(
                                id='c2-slider',
                                min=sigmoid.min_slope,
                                max=sigmoid.max_slope,
                                step=sigmoid.slope_step,
                                value=sigmoid.max_slope/10),
                            html.Div(
                                id='h2-slider-container',
                                children=[
                                    html.Div(id='h2-slider-output-container'),
                                    dcc.Slider(
                                        id='h2-slider',
                                        min=market.min_supply,
                                        max=market.max_supply,
                                        step=market.supply_step,
                                        value=market.max_supply/10)],
                                style={'display': 'none'})
                        ],
                        style={'display': 'none'})
                ], className="three columns sidebar"),
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
            ], className="row flex-display"),
            html.Hr(),
            html.Div([
                html.Div([
                    html.H3('Simulation '),
                    html.Button(children='Simulate', id='sim-button', n_clicks=0),
                    html.Div(id='sim-slider-output-container'),
                    dcc.Slider(
                        id='sim-slider',
                        min=market.min_supply,
                        max=market.max_supply,
                        step=market.supply_step,
                        value=market.initial_supply
                    ),
                ], className="three columns sidebar"),
                # html.Div('Market Status:'),
                html.Div([
                    html.Div(
                        # Plot of  tokens in circulation
                        id='market-circulation-graph-container',
                        style={'display': 'none'},
                        children=[
                            dcc.Graph(
                                id='market-circulation-graph'
                            )
                        ], className="four columns"
                    ),
                    html.Div(
                        # Plot of buy and sell volume
                        id='market-buysell-graph-container',
                        style={'display': 'none'},
                        children=[
                            dcc.Graph(
                                id='market-buysell-graph'
                            )
                        ], className="four columns"
                    ),
                ]),
                html.Div([
                    html.Div(
                        # TODO:  Plot prices on each iteration with 
                        # transaction volume rug
                        id='market-price-graph-container',
                        style={'display': 'none'},
                        children=[
                            dcc.Graph(
                                id='market-price-graph'
                            )
                        ], className="four columns"
                    ),
                    html.Div(
                        # Plot of funds
                        id='market-funds-graph-container',
                        style={'display': 'none'},
                        children=[
                            dcc.Graph(
                                id='market-funds-graph'
                            )
                        ], className="four columns"
                    ),
                    html.Div(
                        # Plot of capital 
                        id='market-capital-graph-container',
                        style={'display': 'none'},
                        children=[
                            dcc.Graph(
                                id='market-capital-graph'
                            )
                        ], className="four columns"
                    ),
                ]), # className="four columns"),
            ], className="row flex-display"),
            html.Div([
                # html.P('Agent Status:'),
                # TODO: Add selector for agents
                html.Div(
                    style={'display': 'inline-block'},
                    children=[
                    # Point-in-time data
                    html.Div(
                        id='pit-agent-graph-container',
                        style={'display': 'none'},
                        children=[
                            dcc.Graph(
                                id='pit-agent-graph'
                            )
                        ],
                    ),
                ]),
                html.Div([
                    html.H3('Simulation Tables'),
                    html.Div([
                        html.Div(id='sim-table-div')
                    ], style={'display': 'inline-block', 'width': '98%'}),                
                    html.H3('Token Dynamics:'),
                    html.Div([
                        html.Div(id='mkt-table-div')
                    ], style={'display': 'inline-block', 'width': '98%'}),                
                    dcc.Textarea(
                        id='sim-notes',
                        value='No Data',
                        style={'width': '100%', 'height': 300},
                    ),
                ]),
            ]),
        ]),
    ])
    return app


# display supply slider value
@app.callback(
    Output('supply-slider-output-container', 'children'),
    [Input('supply-slider', 'value')])
def update_supply_slider_output(supply_value):
    return f'Max Token Supply: {utils.format_number(supply_value)}'

    
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
    return sigmoid.get_buy_slider_range(scenario_value, a1_max, a1_min, a1_value)


# update b1-slider (inflection point) ranges based on selected supply
@app.callback(
    [Output('b1-slider', 'max'),
     Output('b1-slider', 'value')],
    [Input('supply-slider', 'value')])
def adjust_b1_slider(supply_value):
    return sigmoid.get_buy_inflection_point_range(supply_value)


# update sell inflection point ranges based on b1-value
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
    return sigmoid.get_sell_inflection_point_range(scenario_value, b1_max, b1_min, b1_value)


# update sell slope slider ranges based on buy slope value
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
    return sigmoid.get_sell_slope_ranges(scenario_value, c1_max, c1_min, c1_value)


# update vertical displacement (buy - sell at t(0)) slider range
@app.callback(
    [Output('k1-slider', 'value')],
    [Input('scenario-dropdown', 'value'),
     Input('k1-slider', 'max')],
    [State('k1-slider', 'value')])
def adjust_k1_slider(scenario_value, k1_max, k1_value):
    return sigmoid.get_vertical_displacement_range(scenario_value, k1_max)


# update horizontal displacement (buy - sell at t(0)) slider range
@app.callback(
    [Output('h2-slider', 'max'),
     Output('h2-slider', 'value')],
    [Input('scenario-dropdown', 'value'),
     Input('b1-slider', 'max'),
     Input('b1-slider', 'value')],
    [State('h2-slider', 'value')])
def adjust_h2_slider(scenario_value, b1_max, b1_value, h2_value):
    return sigmoid.get_horizontal_displacement_range(scenario_value, b1_max, b1_value, h2_value)

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
    return sigmoid.format_slider_outputs(a1_value, b1_value, c1_value, 
                          k1_value, t1_value,
                          a2_value, b2_value, c2_value, h2_value)


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
    
    curve_parameters = {
        'scenario': scenario_value,
        'supply': supply_value,
        'buy_price': a1_value,
        'buy_supply': b1_value,
        'buy_slope': c1_value,
        'vertical_displacement': k1_value,
        'tax': t1_value,
        'sell_price': a2_value,
        'sell_supply': b2_value,
        'sell_slope': c2_value,
        'horizontal_displacement': h2_value,
    }

    if scenario_value is None or sigmoid_market is None:
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
    else:
        # df = sigmoid.get_scenario_data(scenario_value, supply_value, a1_value, b1_value, c1_value, 
        #     k1_value, t1_value, a2_value, b2_value, c2_value, h2_value, n_points)
        df = sigmoid_market.update_token_dynamics(supply_value, curve_parameters)
        if scenario_value == 's0':
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
        else:
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
                    legend={'xanchor': 'left', 'yanchor': 'top'})
                    # legend={'orientation': 'h'})
                },
                {'display': 'block'},
                {'data': [col_trace1, col_trace2],
                'layout': go.Layout(
                    title='Collateral Graph',
                    xaxis={'title': 'Supply'},
                    yaxis={
                        'title': 'Collateral',
                        'rangemode': 'nonnegative'},
                    legend={'xanchor': 'left', 'yanchor': 'top'})
                    # legend={'orientation': 'h'})
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
                    # legend={'xanchor': 'left', 'yanchor': 'top'}
                    legend={'x': 0.25, 'yanchor': 'top'}
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
                    # legend={'xanchor': 'left', 'yanchor': 'top'}
                    legend={'x': 0.25, 'yanchor': 'top'}
                    )}
            ]