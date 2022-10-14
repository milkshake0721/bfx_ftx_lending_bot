import asyncio
from curses import noecho
from decimal import ROUND_DOWN
from pickle import TRUE
import time, requests
from tracemalloc import stop
from bfxapi.client import Client
from bfxapi.models.order import now_in_mills
from ftxclient import FtxClient
import datetime, api_data
from bfxapi.models import OrderType

log_path = "log.txt"

BFX_API_KEY = api_data.bfx["apiKey"]
BFX_API_SECRET = api_data.bfx["secret"]
FTX_API_KEY = api_data.ftx["apiKey"]
FTX_API_SECRET = api_data.ftx["secret"]
FTX_API_SUBACCOUNT = api_data.ftx["subaccount"]

FTX_WITHDRAW_SAVED_ADRESS_ID = api_data.ftx_withdraw_ID
FTX_DEPOSIT_ADRESS = api_data.ftx_adress


bfx = Client(API_KEY=BFX_API_KEY, API_SECRET=BFX_API_SECRET, logLevel="INFO")

ftx = FtxClient(
    api_key=FTX_API_KEY, api_secret=FTX_API_SECRET, subaccount_name=FTX_API_SUBACCOUNT
)


async def check_wallet(wallet, coin):
    response = await bfx.rest.get_wallets()
    res = {}
    for i in range(len(response)):
        if response[i].type == wallet:
            res[response[i].currency] = response[i].balance_available
    if res == {}:
        res[coin] = 0
        return 0
    return int(res[coin])


async def bfx_usdt_2_usd(amount):  # BFX 將USDT換成USD
    response = await bfx.rest.submit_order(
        symbol="tUSTUSD",
        amount=-amount,
        price=None,
        market_type=OrderType.EXCHANGE_MARKET,
    )
    for o in response.notify_info:
        print("Order: ", o)


async def bfx_usd_2_usdt(amount):  # BFX 將USD換成USDT
    response = await bfx.rest.submit_order(
        symbol="tUSTUSD",
        amount=amount,
        price=None,
        market_type=OrderType.EXCHANGE_MARKET,
    )
    for o in response.notify_info:
        print("Order: ", o)


async def create_funding(balance, rt, day):  # BFX 放出一項貸款
    response = await bfx.rest.submit_funding_offer("fUSD", balance, rt, day)
    print("Offer: ", response.notify_info)


async def get_funding_offer():  # 取得現在正在放的貸款
    try:
        response = await bfx.rest.get_funding_offers("fUSD")
    except:
        response = "Timeout"
    return response
    """for i in response:
    print("FundingOffer\t'{}' :\tid={}\trate={}%\tamount={}\tDay={}\tstatus='{}'".format(
              i.symbol, i.id, i.rate*100*365,round(i.amount,2), i.period, i.status))"""


async def change_to_exchange(balance):  # BFX把funding wallet 轉到exchange wallet
    response = await bfx.rest.submit_wallet_transfer(
        "funding", "exchange", "USD", "USD", balance
    )
    print("Offer: ", response)


async def change_to_funding(balance):  # BFX把exchange wallet 轉到funding wallet
    response = await bfx.rest.submit_wallet_transfer(
        "exchange", "funding", "USD", "USD", balance
    )
    print("Offer: ", response)


async def get_bfx_address():  # 取bfx exchange wallet 的usdt地址
    response = await bfx.rest.get_wallet_deposit_address("exchange", "tetherusx")
    print("Address: ", response.notify_info.address)
    return response.notify_info.address


def get_ftx_usdt():  # 取ftx錢包裡的餘額
    try:
        ftx_balance = ftx.get_balances()
    except:
        time.sleep(0.1)
        ftx_balance = ftx.get_balances()
    for i in range(len(ftx_balance)):
        if ftx_balance[i]["coin"] == "USDT":
            ftx_usdt = ftx_balance[i]["free"]
            break
    return ftx_usdt


async def cancle_two_days_ago_offers():  # 刪除兩天以上的掛單
    try:
        loan_offfer = await get_funding_offer()
        if loan_offfer == []:
            return
        for j in loan_offfer:
            tie = j.mts_updated
            if now_in_mills() - tie > 172800000:
                print("刪除超過兩天的掛單...")
                await bfx.rest.submit_cancel_funding_offer(j.id)
    except:
        print("刪掉掛了兩天的單，但有點問題，等等再試試")
        time.sleep(3)


async def bfx_withdraw2_ftx(amoun):  # 將BFX的usdt轉到ftx
    # tetheruse = Tether (ERC20)
    response = await bfx.rest.submit_wallet_withdraw(
        "exchange", "USX", amoun, FTX_DEPOSIT_ADRESS
    )
    # ["UDC","USDc"],["USDTBCH","USDt (BCH)"],["USDTKSM","USDTKSM"],["USDTSOL","USDt (SOL)"],["USE","USDt (ETH)"],["USO","USDt (Omni)"],
    # ["USS","USDt (EOS)"],["UST","Tether USDt"],["USX","USDt (Tron)"]
    print("Address: ", response.notify_info)


async def is_there_loan_running():  # 抓現在正在放的貸款並加總
    loan_run = await bfx.rest.get_funding_credits("fUSD")
    total_usd = 0
    total_rate = 0
    for i in loan_run:
        print(
            "FundingLoan\t'{}' :\tid={}\trate={}%\tamount={}\tDay={}\tstatus='{}'".format(
                i.symbol,
                i.id,
                round((i.rate * 100 * 365), 2),
                round(i.amount, 2),
                i.period,
                i.status,
            )
        )
        total_usd += i.amount
        total_rate += i.rate * i.amount
    total_rate = total_rate / total_usd * 100 * 365
    return "總共貸出:{} usd(平均利率{}%)".format(round(total_usd, 2), round(total_rate, 2))


def get_ftx_usd_loan():  # 取ftx的放貸利率
    ftx_url = "http://ftx.com/api/spot_margin/lending_rates"
    ftx_r = requests.get(ftx_url)
    sel = ftx_r.json()["result"]
    for i in range(len(sel)):
        if sel[i]["coin"] == "USD":
            spot = sel[i]
            break
    rate = round((spot["estimate"] * 24 * 365 * 100), 2)
    return rate


def get_ftx_usdt_loan():  # 取ftx的放貸利率，來做比較
    ftx_url = "http://ftx.com/api/spot_margin/lending_rates"
    ftx_r = requests.get(ftx_url)
    sel = ftx_r.json()["result"]
    for i in range(len(sel)):
        if sel[i]["coin"] == "USDT":
            spot = sel[i]
            break
    rate = round((spot["estimate"] * 24 * 365 * 100), 2)
    return rate


async def slide_offer_rate(slide):  # 計算要使用的RATE
    stats = await bfx.rest.get_public_funding_stats("fUSD")
    loan_run = await bfx.rest.get_funding_credits("fUSD")
    amount, famount, present_day_profit, offer_day_profit = 0, 0, 0, 0
    running_rate, rate_list, offer_rate, offer_amount, running_amount = (
        [],
        [],
        [],
        [],
        [],
    )
    hope_day_profit_rate = stats[0][3] * 365 - 0.0005  # 最佳情況 減去0.0005
    for i in range(len(loan_run)):
        running_rate.append(loan_run[i].rate)
        running_amount.append(loan_run[i].amount)
        present_day_profit += loan_run[i].rate * loan_run[i].amount
        amount += loan_run[i].amount
    if present_day_profit == 0:
        present_day_profit = 0.04  # 還未開單的話 打底14.6%
    offer = await bfx.rest.get_funding_offers("fUSD")
    for k in range(len(offer)):
        offer_rate.append(offer[k].rate)
        offer_amount.append(offer[k].amount)
        offer_day_profit += offer[k].rate * offer[k].amount
        famount += offer[k].amount
    all_profit_rate = (offer_day_profit + present_day_profit) / (famount + amount)
    top = hope_day_profit_rate - all_profit_rate + hope_day_profit_rate
    bottom = all_profit_rate - (hope_day_profit_rate - all_profit_rate)
    if top - bottom < 0:
        top = all_profit_rate - (hope_day_profit_rate - all_profit_rate)
        bottom = hope_day_profit_rate - all_profit_rate + hope_day_profit_rate
    bottom = 0.0003
    a_slide = (top - bottom) / (slide)
    for i in range(slide):
        top -= a_slide
        rate_list.append(round(top, 6))
    if slide > 9:
        rate_list[slide - 1] = rate_list[slide - 1]   # 幹價單
    print(rate_list)
    return rate_list


async def USDT_to_USD_and_exchange_to_funding():  # usdt換成usd然後轉到funding
    try:
        time.sleep(0.1)
        bfx_exchange_usdt_liq = await check_wallet("exchange", "UST")
        if bfx_exchange_usdt_liq > 150:
            await bfx_usdt_2_usd(bfx_exchange_usdt_liq)  # usdt轉成usd
            time.sleep(0.1)
        time.sleep(0.1)
        bfx_exchange_usd_liq = await check_wallet("exchange", "USD")  # 取usd餘額
        if bfx_exchange_usd_liq > 150:
            print("Exchange_USD有 : {}".format(bfx_exchange_usd_liq))
            time.sleep(0.1)
            await change_to_funding(bfx_exchange_usd_liq)  # usd轉到Funding帳戶
    except:
        print("USDT_to_USD_and_exchange_to_funding()  Timeout")
        time.sleep(2)


async def transfer2ftx():
    bfx_funding_liq = await check_wallet("funding", "USD")
    await change_to_exchange(bfx_funding_liq)
    time.sleep(0.1)
    await bfx_usd_2_usdt(bfx_funding_liq)
    time.sleep(0.1)
    bfx_exchange_usdt_liq = await check_wallet("exchange", "UST")
    await bfx_withdraw2_ftx(bfx_exchange_usdt_liq)


async def main():
    while True:
        ftxt = open(log_path, "a", encoding="utf-8")
        print(
            "===========================================================\n",
            datetime.datetime.now(),
        )
        fUSD_url = "https://api-pub.bitfinex.com/v2/book/fUSD/P2"
        time.sleep(0.1)
        bfx_r = requests.get(fUSD_url)
        time.sleep(0.1)
        # loan_offfer = await get_funding_offer()
        latest = bfx_r.json()[0][0]
        ftx_usdt = get_ftx_usdt()
        # print('\n當前BFX掛單借入利率:{}%'.format(latest*365*100))
        # print('當前BFX掛單貸出利率:{}%\n'.format(bfx_r.json()[25][0]*365*100))
        # print('當前FTX_usd利率:{}%'.format(get_ftx_usd_loan()))
        # print('當前FTX_usdt利率:{}%\n'.format(get_ftx_usdt_loan()))

        if bfx_r.json()[25][0] * 365 * 100 < 4:  # 看要不要轉到ftx
            start_time = time.time()
            while bfx_r.json()[25][0] * 365 * 100 < 4:
                now_time = time.time()
                if now_time - start_time > 260000:
                    print("利率低於4%,持續三天了要把餘額傳到ftx囉")
                    try:
                        transfer2ftx()
                    except:
                        time.sleep(1)
                    break
                else:
                    ho = round((now_time - start_time) / 60 / 60, 3)
                    print("利率小於4% , 持續{}小時了".format(ho))
                    time.sleep(5)
                    bfx_r = requests.get(fUSD_url)

        await cancle_two_days_ago_offers()
        try:
            bfx_exchange_usdt_liq = await check_wallet(
                "exchange", "UST"
            )  # 取exchange_usdt餘額
            time.sleep(0.1)
            bfx_exchange_usd_liq = await check_wallet(
                "exchange", "USD"
            )  # 取exchange_usd餘額
            time.sleep(0.1)
            bfx_funding_liq = await check_wallet("funding", "USD")  # 取funding_usd錢包餘額
        except:
            time.sleep(3)
            continue

        if bfx_funding_liq < 150:
            print("BFX USD餘額 : {}".format(bfx_funding_liq))
            print("FTX USDT餘額 : {}".format(ftx_usdt))
            print()
            if latest < 0.000181:
                print("u放在ftx不用動")
                time.sleep(3)
                continue
            if ftx_usdt > 150:  # FTX有錢錢，提出來
                print("開始轉帳....從ftx轉到bfx...共 {} usdt".format(ftx_usdt))
                try:
                    ftx.submit_withdrawal(
                        "USDT", ftx_usdt, FTX_WITHDRAW_SAVED_ADRESS_ID
                    )
                    wtthdraw_info = ftx.get_withdrawals()[0]  # 取提款資料
                    while wtthdraw_info["txid"] == None:  # 等txid出來再繼續下一步
                        print("傳輸中...")
                        time.sleep(10)
                        wtthdraw_info = ftx.get_withdrawals()[0]
                    bfx_exchange_usdt_liq = await check_wallet("exchange", "UST")
                    print("BFX USDt餘額 : {}".format(bfx_exchange_usdt_liq))
                    while bfx_exchange_usdt_liq < 150:  # 確認到帳後繼續下一步
                        print("BFX確認到帳中...")
                        time.sleep(30)
                        bfx_exchange_usdt_liq = await check_wallet("exchange", "UST")
                        print("BFX_exchange USDt :{}".format(bfx_exchange_usdt_liq))
                    await bfx_usdt_2_usd(bfx_exchange_usdt_liq)  # usdt轉成usd
                    time.sleep(1)
                    bfx_exchange_usd_liq = await check_wallet(
                        "exchange", "USD"
                    )  # 更新[bfx_exchange_usd_liq]
                    await change_to_funding(
                        bfx_exchange_usd_liq
                    )  # 把usd從exchange轉到Funding帳戶
                except:
                    print("轉帳有點問題")
            else:
                try:
                    print("現在正在跑...")
                    time.sleep(0.1)
                    # loan_list = await is_there_loan_running()
                    # print(loan_list)
                    # ftxt.write('{}\n\t現在正在跑的有\n\t{}\n'.format(datetime.datetime.now(),loan_list))
                    # if loan_offfer!=[]:
                    #   print('\n正在掛的單有...')
                    #   for i in loan_offfer:
                    #     print("FundingOffer\t'{}' :\tid={}\trate={}%\tamount={}\tDay={}\tstatus='{}'".format(
                    #       i.symbol, i.id, round((i.rate*100*365),2),round(i.amount,2), i.period, i.status))
                    #     a = "FundingOffer\t'{}' :\tid={}\trate={}%\tamount={}\tDay={}\tstatus='{}'\n".format(
                    #       i.symbol, i.id, round((i.rate*100*365),2),round(i.amount,2), i.period, i.status)
                    #     ftxt.write(a)
                except:
                    print("Post Error or Format Error")

            await USDT_to_USD_and_exchange_to_funding()  # usdt換成usd然後轉到funding，

            time.sleep(2)
            print()
            continue
        bfx_funding_liq = await check_wallet("funding", "USD")
        if bfx_funding_liq > 150:
            slice = int(bfx_funding_liq / 200)
            if slice == 0:
                slice = 1
            if slice > 20:
                slice = 20
            USD_will_set = int(bfx_funding_liq / slice)
            rate_will_be = await slide_offer_rate(slice)
            for j in rate_will_be:
                if j <= 0.0003:
                    await create_funding(USD_will_set, j, 7)
                elif j<=0.0005:
                    await create_funding(USD_will_set, j, 30)
                else:
                    await create_funding(USD_will_set, j, 120)
                print("掛單 : {} USD @ {}%".format(USD_will_set, j))
                time.sleep(0.1)

        ftxt.close
        time.sleep(2)


t = asyncio.ensure_future(main())
asyncio.get_event_loop().run_until_complete(t)
