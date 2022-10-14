會在bfx跟ftx之間找適當的利率去放貸

1.首先先創一個python環境

2.在環境下安裝所需的module: pip install -r requirements.txt

3.在api_data.py輸入BFX_API/FTX_API

4.更改order_ID
  order_ID查詢方式：做完第三步後，並執行check_order_ID.py
  ，找尋你存在ftx裡面的轉出地址ID

5.更改api_data.py的(ftx_withdraw_ID)，以及FTX的收款地址ftx_adress

6.好了之後再終端機執行 python main.py

log_rate.py是監控利率的小程式，當利率大於15%時，紀錄掛單簿上的資料到rate.txt