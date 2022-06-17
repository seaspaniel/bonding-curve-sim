# Sigmoid Bonding Curve Simulator

## Description
This interactive dashboard and simulation is based on the different fundraising 
scenarios outlined in this <a href="https://medium.com/molecule-blog/designing-different-fundraising-scenarios-with-sigmoidal-token-bonding-curves-ceafc734ed97"> Medium Post</a> about Sigmoidal Token Bonding Curves. It was implemented as part of a learning journey with cadCAD's system modeling framework to pair an interesting bonding curve structure with a simple simulation.

The <a href="https://github.com/ttsteiger/sigmoid-tbc-app">original dashboard code</a> was refactored and the <a href="https://github.com/cadCAD-org/cadCAD">cadcad 0.4.28</a> framework was added for simulating interactions between agents and the market.

<img src="assets/Molecule Buy_Sell Bonding Curve System Diagram.jpg">

The simulation utilizes a single agent for purposes of validating and exploring the properties of sigmoidal buy and sell curves.  The agent starts with an initial capital allocation and will buy one token at each time step until it no longer has enough capital.  When the agent lacks enough capital to buy a token, it will sell one token.  This provides something like a unit test for the simulation of the bonding curves defined by the parameter settings.  Adding more agents with varied types of behavior is planned.

In the Settings section of the app, parameters of the buy and sell curves can be adjusted under different scenarios.  Based on the parameters, four graphs display as a function of token supply:
1. Token buy and sell prices 
2. Network collateral
3. Tax rates and amounts 
4. Fund rates and amounts.  

Below the Settings section, the Simulation section contains graphs of the market and the agent as a function of time.  When the curve parameters are changed, press the Simulate button to run the simulation and update the market and agent graphs.  

## Installation
```git clone https://github.com/seaspaniel/bonding-curve-sim.git```

## Running the app
```python app1.py```

The terminal output will indicate where the app is running locally.  For example, 

```Dash is running on http://127.0.0.1:8050/```

Open a browser window with the URL provided in the terminal. 

## Things to Try
- Compare taxation and funding under different scenarios for the bonding curves.  How would different scenarios impact business strategies?
- Increase the token supply and run the simulation.  How do the market graphs change as a result?  What causes this change?
- Increase the token supply to the maximum value and run the simulation.  What happens to the agent capital and token curves?  Why is the token curve declining towards the end of the simulation?  Drag the mouse over the end of the token curve to zoom in and see more transaction detail.  Double-click on the graph to zoom back out.


