class Portfolio:

    def __init__(self, capital=100000):
        self.capital = capital
        self.positions = []

    def can_open(self, max_positions=5):
        return len(self.positions) < max_positions

    def add(self, symbol, entry, sl, tp):
        self.positions.append({
            "symbol": symbol,
            "entry": entry,
            "sl": sl,
            "tp": tp
        })

    def risk_per_trade(self):
        return self.capital * 0.02
