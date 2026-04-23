class filter:
    def __init__(self, filter_string, aggr_string):
        self.filter_string = filter_string
        self.aggr_string = aggr_string  
        self.init()
        self.methods = [
"all",
"any",
"bfill",
"corr",
"corrwith",
"count",
"cov",
"cumcount",
"cummax",
"cummin",
"cumprod",
"cumsum",
"describe",
"ffill",
"fillna",
"first",
"head",
"idxmax",
"idxmin",
"last",
"max",
"mean",
"median",
"min",
"ngroup",
"nth",
"ohlc",
"pct_change",
"prod",
"quantile",
"rank",
"resample",
"rolling",
"sample",
"sem",
"shift",
"size",
"skew",
"std",
"sum",
"var",
"tail",
"take",
"value_counts",
"nunique"
]
    

    def init(self):
        self.columns = self.filter_string.split(",") if self.filter_string else None
        self.aggr_attr = self.aggr_string.split(",") if self.aggr_string else None
        self.aggr_method = self.aggr_attr.pop(0) if self.aggr_attr else None

    def debug(self):
        print("Filters:", self.columns)
        print("Aggregation Method:", self.aggr_method)
        print("Aggregation Attributes:", self.aggr_attr)
        print("Validation Result:", self.validate())

    def isAggregation(self):
        return self.aggr_method is not None and self.aggr_attr is not None and self.columns is not None
    def isSelection(self):
        return self.columns is not None

    def validate(self):
        global methods
        # Implement validation logic for filters and aggregation parameters
        r = True
        if not self.columns:
            r = False
        if self.aggr_attr and self.aggr_method and self.columns:
            if self.columns[:len(self.columns)-1] != self.aggr_attr: r = False
            if self.aggr_method not in self.methods: r = False
        if not self.isAggregation() and not self.isSelection():
            r = True
        return r
    
    def getColumns(self):
        return self.columns
    
    def getAggregationColumns(self):
        return self.aggr_attr
    def getAggregationMethod(self):
        return self.aggr_method