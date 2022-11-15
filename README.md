# StatBot

An algorithmic python trading bot using statistical arbitrage and Alpaca brokerage.

Theory of Execution (High Level):
	Look for cointegrated pairs on the market by comparing every ticker to every other ticker on the exchange.
	Create a list of pairs and start a thread that looks at the pair spread and decides whether to buy or not.
	Pairs that are bought are written to a list that a sell thread reads and looks at the spread to determine whether to sell or not.
