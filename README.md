# VTB report parser

----

The VTB report parser provides support for parcing a VTB broker XML report that
can be downloaded at https://www.olb.ru

----

## To start

Install python and python pip tool.

```
$ git clone https://github.com/antonkurbatov/vtb_report_parse.git
$ cd vtb_report_parse
$ pip install -e ./
```

## Usage

Download a VTB broker report at https://www.olb.ru using your account.
Save it to GetBrokerReport.xml.

```
$ vtb_report_parse -f ~/reports/GetBrokerReport.xml
Processing the report: /home/user/reports/GetBrokerReport.xml ...
[Period] 2019-06-01 - 2020-06-17 (382 days)
[USD price] 69.7524
---- Cash Flow ----
[Fees] -1137.85₽, -2.86$ (-1337.34₽)
[Taxes] -1026.0₽, 0$ (-1026.0₽)
[Dividends] 3646.18₽, 6.11$ (4072.37₽)
[Coupons] 7717.24₽, 63.75$ (12163.96₽)
[Credit payments] 302600.0₽, 0$ (302600.0₽)
[Write offs] -64000.0₽, -1495.0$ (-168279.84₽)
[Exhange saldo] -395898.39₽, 6074.0$ (27777.69₽)
[Securities saldo] -574310.5₽, -4334.79$ (-876672.51₽)
---- Summary ----
[Credit payments with write offs] 238600.0₽, -1495.0$ (134320.16₽)
[Total] 27590.68₽, 311.21$ (49298.32₽)
$
```
