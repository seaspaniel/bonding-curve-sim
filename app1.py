# For Dash 2.0:
from dash import dash_table
from dash.dash_table import FormatTemplate
from dash.dash_table.Format import Format, Align
from dash.dependencies import Input, Output
from dash.long_callback import DiskcacheLongCallbackManager
## Diskcache
import diskcache

# For dash < 2.0
# import dash_core_components as dcc
# import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
import time

import numpy as np
import pandas as pd
import logging

from cadCAD.configuration import Experiment
from cadCAD.engine import ExecutionMode, ExecutionContext, Executor
from cadCAD.configuration.utils import config_sim

import utils
import sigmoid as sigmoid
import sigmoid_dash_ui as sigmoid_ui

import market
from token_user import TokenUser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

cache = diskcache.Cache("./cache")
long_callback_manager = DiskcacheLongCallbackManager(cache)

sigmoid.k_max = market.max_price / 2
sigmoid.min_slope = market.max_supply / 2
sigmoid.max_slope = market.max_supply * 1e3
sigmoid.slope_step = (sigmoid.max_slope - sigmoid.min_slope) * .1

sigmoid_market = market.Market(
    sigmoid.Sigmoid(market.min_supply, 
                    market.initial_supply, 
                    market.max_price/2))
sigmoid_ui.sigmoid_market = sigmoid_market

token_user = TokenUser(0, 100000.0)

# Initialize Dash UI components 
app = sigmoid_ui.init_app(sigmoid)
server = app.server
app.config['suppress_callback_exceptions']=True

# May want to configure this through UI
# sim_duration = 1000  # 100
simulation_parameters = {
    # Length of simulation
    'T': range(int(sigmoid_market.supply)),
    # Number of monte carlo runs
    'N': 1,
    # System parameters to sweep
    # 'M': {
    #     "max_price": sigmoid_market.max_price
    # }
}

#
# Initialize agent and market
#
def bootstrap_simulation():
    buy_price = sigmoid_market.buy_price()
    sell_price = sigmoid_market.sell_price()
    initial_conditions = {
        'token_price': buy_price,
        'agent_txn': {'action': '',
                      'amount': 0,
                      'fee': 0,
                      'tokens': 0},
        'market_state': {'tokens_circulation': 0,
                        'tokens_bought': 0, 
                        'tokens_sold': 0,
                        'fund_balance': 0,
                        'collateral_balance': 0,
                        'buy_price': buy_price,
                        'sell_price': sell_price},
        'agent_state': {'capital': token_user.capital,
                         'tokens': token_user.tokens}
    }
    logger.info(f'bootstrap_simulation duration T {simulation_parameters["T"]}')
    return initial_conditions, config_sim(simulation_parameters)

def s_timestamp(params, substep, state_history, previous_state, policy_input):
    value = policy_input['timestamp']
    return ('timestamp', value)

#
# Wrapping the call to the market object since cadcad seems to 
# have a problem calling class methods.
def transact(params, substep, history, prev_state, input):
    # logger.info(f'\n>> transact\nparams:\n{params}\nstep:\n{substep}\nhistory:\n{history}\nstate:\n{prev_state}\ninput:\n{input}')
    action = input['action']
    number_of_tokens = input['number_of_tokens']
    if action == 'Buy':
        number_of_tokens, amount, fee = sigmoid_market.buy_tokens(number_of_tokens)
    elif action == 'Sell':
        number_of_tokens, amount, fee = sigmoid_market.sell_tokens(number_of_tokens)
    else:
        action = ''
        number_of_tokens = 0
        amount = 0
        fee = 0

    # logger.info(f'transact action {action} amount {amount} fee {fee} tokens {number_of_tokens}')
    agent_txn = {'action': action,
                 'amount': amount,
                 'fee': fee,
                 'tokens': number_of_tokens}
 
    return ('agent_txn', agent_txn)

def market_state(params, substep, history, prev_state, input):
    buy_price = sigmoid_market.buy_price()
    sell_price = sigmoid_market.sell_price()
    market_state = {'tokens_circulation': sigmoid_market.tokens_circulation,
                    'tokens_bought': sigmoid_market.tokens_bought, 
                    'tokens_sold': sigmoid_market.tokens_sold,
                    'fund_balance': sigmoid_market.fund_balance,
                    'collateral_balance': sigmoid_market.collateral_balance,
                    'buy_price': buy_price,
                    'sell_price': sell_price}
    # logger.info(f'market state {market_state}')
    
    return ('market_state', market_state)

def agent_choices(params, substep, history, state) -> dict:
    """Save the action as an array so that it can be added to our buffer.

    Parameters
    ----------
    params: dict
        System parameters that can be swept.
    substep: int
        The sub-timestep in which the updated states of agents don't
        affect other agents.
    history: list[list[dict]]
        The history of states.
    state: dict
        The current state of the system.
    actions: dict
        Actions of the agents.

    Returns
    -------
    name: str
        "pursuer_action"
    value: np.ndarray
        The pursuer's action as an array.
    """
    # logger.debug(f'get_transaction\nparams:\n{params}\nstep:\n{substep}\nhistory:\n{history}\nstate:\n{state}')
    action, number_of_tokens = token_user.get_transaction(state['market_state']['buy_price'])
    return {'action': action, 'number_of_tokens': number_of_tokens}
            
def update_agents(params, substep, history, prev_state, input):
    # logger.debug(f'\n>> update_agents\nparams:\n{params}\nstep:\n{substep}\nhistory:\n{history}\nstate:\n{prev_state}\ninput:\n{input}')
    action = input.get('action', 'Undefined')
    tokens = prev_state['agent_txn']['tokens']
    amount = prev_state['agent_txn']['amount']
    fee = prev_state['agent_txn']['fee']
    # logger.info(f'update_capital amount {amount} fee {fee} prev_state {prev_state[y]}')
    capital, tokens = token_user.transaction_update(action, tokens, amount, fee)
    agent_state = {'capital': capital, 
                   'tokens': tokens}
    # logger.debug(f'agent_state {agent_state}')

    return ('agent_state', agent_state) 

# cadacad simulation
def run_simulation():
    '''
    Definition:
    Run simulation
    '''
    # initialize market and agent
    sigmoid_market.reset()
    token_user.reset()
    
    exp = Experiment()
    initial_conditions, sim_params = bootstrap_simulation()

    partial_state_update_blocks = [
        { 
            'label': 'Agent and Market Update',
            'policies': {
                # Get agent actions
                'transaction': agent_choices,
            },
            'variables': {
                # Execute transactions
                'agent_txn': transact,
                # Update market state after transactions
                'market_state': market_state,
                # Update agent state after transactions
                'agent_state': update_agents,
            }
        },
    ]
    exp.append_model(
        model_id="sigmoid-bonding-curve",
        initial_state=initial_conditions,
        partial_state_update_blocks=partial_state_update_blocks,
        sim_configs=sim_params
    )
    logger.info('Run Simulation')
    logger.info(sim_params)
    exec_mode = ExecutionMode()
    local_proc_ctx = ExecutionContext(context=exec_mode.local_mode)
    run = Executor(exec_context=local_proc_ctx, configs=exp.configs)
    raw_result, tensor_fields, _ = run.execute()
    result = pd.DataFrame(raw_result)
    return result


# display supply slider value
@app.callback(
    Output('sim-slider-output-container', 'children'),
    [Input('sim-slider', 'value')])
def update_sim_slider_output(sim_steps):
    simulation_parameters["T"] = range(int(sim_steps))
    logger.info(f'update_sim_slider_output {sim_steps} T {simulation_parameters["T"]}')
    return f'Simulation Times: {int(sim_steps)}'
    
    
def sim_table(data):
    money = FormatTemplate.money(2)
    # Unpack market_state and agent_txn dict objects into multi-line records
    def unpack(d):
        return [f'{k}: {v}' for k ,v in d.items()]  
    data['market_state'] = data['market_state'].apply(lambda x: '\\\n'.join(unpack(x)))
    data['agent_txn'] = data['agent_txn'].apply(lambda x: '\\\n'.join(unpack(x)))

    tbl_cols = [
        dict(id='timestep', name='Timestep'),
        # dict(id='date', name='Date', type='datetime'),
        dict(id='substep', name='Substep'),
        dict(id='capital_text', name='Agent Capital', format=money),
        dict(id='tokens_text', name='Agent Tokens', format=Format().align(Align.left)),
        dict(id='market_state', name='Market State', format=Format().align(Align.left), presentation='markdown'),
        dict(id='agent_txn', name='Agent Transaction', format=Format().align(Align.left), presentation='markdown')
    ]
    # logger.info(f'Table\n{dff.head()}')
    return dash_table.DataTable(
        id='crossfilter-table',
        sort_action='native',
        filter_action='native',
        columns=tbl_cols,  # [{"name": i, "id": i} for i in dff.columns],
        data=data.to_dict('records'),
        style_header={
            'padding': '15px',
            'textAlign': 'left',
            'backgroundColor': 'black',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_cell={'padding': '5px','fontSize': 12, 'textAlign': 'right'},
        # Use conditional formatting for multi-line columns 
        style_cell_conditional=[
        {
            'if': {'column_id': ['market_state', 'agent_txn']},
            'textAlign': 'left'
        }],
        style_table={'height': '300px', 'overflowY': 'auto'}
    )

@app.long_callback(
    [Output('market-circulation-graph-container', 'style'),
     Output('market-circulation-graph', 'figure'),
     Output('market-buysell-graph-container', 'style'),
     Output('market-buysell-graph', 'figure'),
     Output('market-price-graph-container', 'style'),
     Output('market-price-graph', 'figure'),
     Output('market-funds-graph-container', 'style'),
     Output('market-funds-graph', 'figure'),
     Output('market-capital-graph-container', 'style'),
     Output('market-capital-graph', 'figure'),
     Output('pit-agent-graph-container', 'style'),
     Output('pit-agent-graph', 'figure'),
     Output('sim-table-div', 'children'),
     Output('mkt-table-div', 'children'),
     Output("sim-notes", "value")],
    [Input("sim-button", "n_clicks")],
    manager=long_callback_manager,
    running=[
        (Output('sim-button', 'disabled'), True, False),
        (Output('sim-button', 'children'), 'Running...', 'Simulate'),
    ],)
def on_simulation(n_clicks):
    logger.info('Run Simulation')

    start_time = time.time()
    sim_df = run_simulation()
    logger.info("--- Sim ran in %s seconds ---" % (time.time() - start_time))

    start_time = time.time()

    logger.debug(f'on_simulation1 market state {sim_df["market_state"].apply(pd.Series)}')
    market_state = pd.DataFrame(sim_df['market_state'].to_list())
    agent_state = pd.DataFrame(sim_df['agent_state'].to_list())
    logger.debug(f'agent state {agent_state}')
    agent_state['capital_text'] = agent_state['capital'].apply(utils.format_number)
    agent_state['tokens_text'] = agent_state['tokens'].apply(utils.format_number)

    sim_df = pd.concat([sim_df, agent_state], axis=1)
 
    token_dynamics_tbl = dash_table.DataTable(
        id='crossfilter-table',
        sort_action='native',
        filter_action='native',
        columns=[{"name": i, "id": i} for i in sigmoid_market.token_dynamics.columns],
        data=sigmoid_market.token_dynamics.to_dict('records'),
        style_header={
            'padding': '15px',
            'textAlign': 'left',
            'backgroundColor': 'black',
            'color': 'white',
            'fontWeight': 'bold'
        },
        style_cell={'padding': '5px','fontSize': 12, 'textAlign': 'right'},
        style_table={'height': '300px', 'overflowY': 'auto'}
    )

    market_circulation_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['tokens_circulation'],
        mode='lines',
        line = {'color': '#2ca02c'},
        name='Circulation',
        text=market_state['tokens_circulation'],
        hoverinfo='text')

    market_funds_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['fund_balance'],
        mode='lines',
        line = {'color': '#2ca02c'},
        name='Fund Balance')

    market_vault_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['collateral_balance'],
        mode='lines',
        line = {'color': '#2ca02c'},
        name='Vault Balance')

    market_buy_price_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['buy_price'],
        mode='lines',
        line = {'color': '#2ca02c'},
        name='Buy Price')

    market_sell_price_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['sell_price'],
        mode='lines',
        line = {'color': '#d62728'},
        name='Sell Price')

    market_buy_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['tokens_bought'],
        mode='lines',
        line = {'color': '#2ca02c'},
        name='Tokens Bought')

    market_sell_trace = go.Scatter(
        x=sim_df['timestep'],
        y=market_state['tokens_sold'],
        mode='lines',
        line = {'color': '#d62728'},
        name='Tokens Sold',
        text=market_state['tokens_sold'],
        hoverinfo='text')

    agent_capital_trace = go.Scatter(
        x=sim_df['timestep'],
        y=agent_state['capital'],
        mode='lines',
        line = {'color': '#2ca02c'},
        name='Capital')

    agent_token_trace = go.Scatter(
        x=sim_df['timestep'],
        y=agent_state['tokens'],
        yaxis='y2',
        mode='lines',
        line = {'color': '#d62728'},
        name='Tokens')
            
    viz = [
        # Market graphs
        {'display': 'inline-block'},
        {'data': [market_circulation_trace],
        'layout': go.Layout(
            title='Market Circulation',
            xaxis={'title': 'Time'},
            yaxis={
                'title': 'Tokens',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'titlefont': {'color': '#2ca02c'},
                'tickfont': {'color': '#2ca02c'}},
            # yaxis2={
            #     'title': 'Tokens',
            #     'rangemode': 'nonnegative',
            #     'overlaying': 'y',
            #     'side': 'right',
            #     'showline': True,
            #     'titlefont': {'color': '#d62728'},
            #     'tickfont': {'color': '#d62728'}
            #     },
            legend={'x': 0.25, 'yanchor': 'top'}
            )},
        {'display': 'inline-block'},
        {'data': [market_buy_trace, market_sell_trace],
        'layout': go.Layout(
            title='Buy/Sell Tokens',
            xaxis={'title': 'Time'},
            yaxis={
                'title': 'Tokens',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'titlefont': {'color': '#2ca02c'},
                'tickfont': {'color': '#2ca02c'}},
            yaxis2={
                'title': 'Tokens',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'overlaying': 'y',
                'side': 'right',
                'showline': True,
                'titlefont': {'color': '#d62728'},
                'tickfont': {'color': '#d62728'}
                },
            legend={'x': 0.25, 'yanchor': 'top'}
            )},
        {'display': 'inline-block'},
        {'data': [market_buy_price_trace, market_sell_price_trace],
        'layout': go.Layout(
            title='Buy/Sell Price',
            xaxis={'title': 'Time'},
            yaxis={
                'title': 'Price',
                'rangemode': 'nonnegative',
                'titlefont': {'color': '#2ca02c'},
                'tickfont': {'color': '#2ca02c'}},
            yaxis2={
                'title': 'Price',
                'rangemode': 'nonnegative',
                'overlaying': 'y',
                'side': 'right',
                'showline': True,
                'titlefont': {'color': '#d62728'},
                'tickfont': {'color': '#d62728'}
                },
            legend={'x': 0.25, 'yanchor': 'top'}
            )},
        {'display': 'inline-block'},
        {'data': [market_funds_trace],
        'layout': go.Layout(
            title='Market Funds Balance',
            xaxis={'title': 'Time'},
            yaxis={
                'title': 'Amount',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'titlefont': {'color': '#2ca02c'},
                'tickfont': {'color': '#2ca02c'}},
            legend={'x': 0.25, 'yanchor': 'top'}
            )},
        {'display': 'inline-block'},
        {'data': [market_vault_trace],
        'layout': go.Layout(
            title='Market Collateral Balance',
            xaxis={'title': 'Time'},
            yaxis={
                'title': 'Amount',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'titlefont': {'color': '#2ca02c'},
                'tickfont': {'color': '#2ca02c'}},
            legend={'x': 0.25, 'yanchor': 'top'}
            )},
        # Agent graphs
        {'display': 'inline-block'},
        {'data': [agent_capital_trace, agent_token_trace],
        'layout': go.Layout(
            title='Agent Point-in-Time',
            xaxis={'title': 'Time'},
            yaxis={
                'title': 'Capital',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'titlefont': {'color': '#2ca02c'},
                'tickfont': {'color': '#2ca02c'}},
            yaxis2={
                'title': 'Tokens',
                'rangemode': 'nonnegative',
                'hoverformat': '.2f',
                'overlaying': 'y',
                'side': 'right',
                'showline': True,
                'titlefont': {'color': '#d62728'},
                'tickfont': {'color': '#d62728'}
                },
            legend={'x': 0.25, 'yanchor': 'top'}
            )},
        # {'display': 'inline-block'},
        # # TODO: Replace cumulative capital with token value
        # # {'data': [cum_agent_capital_trace, cum_agent_token_trace],
        # {'data': [cum_agent_token_trace],
        # 'layout': go.Layout(
        #     title='Agent Cumulative Graph',
        #     xaxis={'title': 'Time'},
        #     # yaxis={
        #     #     'title': 'Capital',
        #     #     'rangemode': 'nonnegative',
        #     #     'titlefont': {'color': '#2ca02c'},
        #     #     'tickfont': {'color': '#2ca02c'}},
        #     yaxis={
        #         'title': 'Tokens',
        #         'rangemode': 'nonnegative',
        #         # 'overlaying': 'y',
        #         # 'side': 'right',
        #         # 'showline': True,
        #         'titlefont': {'color': '#d62728'},
        #         'tickfont': {'color': '#d62728'}
        #         },
        #     legend={'x': 0.25, 'yanchor': 'top'}
        #     )},
        sim_table(sim_df),
        token_dynamics_tbl,
        f'{sim_df.columns}\nSimulation results:\n{sigmoid_market.token_dynamics.head(10)}',
    ]
    logger.info("--- Viz ran in %s seconds ---" % (time.time() - start_time))
    return viz

#
# main
#
if __name__ == '__main__':
    app.run_server(debug=True)
