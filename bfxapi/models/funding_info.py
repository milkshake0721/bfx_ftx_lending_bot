"""
Module used to describe all of the different data types
"""


class FundingInfoModel:
    """
    Enum used to index the location of each value in a raw array
    """

    SYMBOL = 1
    YIELD_LOAN = 0
    YIELD_LEND = 1
    DURATION_LOAN = 2
    DURATION_LEND = 3


class FundingInfo:
    """ """

    def __init__(self, symbol, yield_loan, yield_lend, duration_loan, duration_lend):
        # pylint: disable=invalid-name
        self.symbol = symbol
        self.yield_loan = yield_loan
        self.yield_lend = yield_lend
        self.duration_loan = duration_loan
        self.duration_lend = duration_lend

    @staticmethod
    def from_raw_info(raw_loan):
        """
        Parse a raw funding load into a FundingInfo object

        @return FundingInfo
        """
        symbol = raw_loan[FundingInfoModel.SYMBOL]
        yield_loan = raw_loan[2][FundingInfoModel.YIELD_LOAN]
        yield_lend = raw_loan[2][FundingInfoModel.YIELD_LEND]
        duration_loan = raw_loan[2][FundingInfoModel.DURATION_LOAN]
        duration_lend = raw_loan[2][FundingInfoModel.DURATION_LEND]

        return FundingInfo(symbol, yield_loan, yield_lend, duration_loan, duration_lend)

    def __str__(self):
        return "FundingInfo : <symbol={} yield_loan={} yield_lend={} duration_loan={} duration_lend='{}'>".format(
            self.symbol,
            self.yield_loan,
            self.yield_lend,
            self.duration_loan,
            self.duration_lend,
        )
