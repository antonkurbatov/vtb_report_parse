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
usage: vtb-report-parse [-h] [--verbose] --report <report-file.xml>
                        [--usd-price <usd-price>]

optional arguments:
  -h, --help            show this help message and exit
  --verbose, -v         verbose logging
  --report <report-file.xml>
                        A VTB broker report file. This option can be used
                        multiple times to merge reports together.
  --usd-price <usd-price>
                        USD value in ₽. If not specified the value is gotten
                        form the report.
```

```
$ vtb-report-parse --report ~/reports/GetBrokerReport.xml
Processing the report(s):
- /home/akurbatov/reports/GetBrokerReport.xml ...
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

As VTB broker allows to generate a report for only one year, `-f` option
works in append mode and allows to merge VTB reports together.

```
$ vtb-report-parse --report ~/GetBrokerReport_2019.xml --report ~/GetBrokerReport_2020.xml
Processing the report(s):
- /home/akurbatov/reports/GetBrokerReport_2019.xml
- /home/akurbatov/reports/GetBrokerReport_2020.xml
[Period] 2019-01-01 - 2020-08-03 (399 days)
[USD price] 73.4261
---- Cash Flow ----
[Fees] -1331.87₽, -3.27$ (-1571.97₽)
<cut>
$
```
