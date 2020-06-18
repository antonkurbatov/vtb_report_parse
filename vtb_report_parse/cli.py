# -*- coding: utf-8 -*-
import argparse
import logging

from vtb_report_parse import report as vtb_report

OperationType = vtb_report.OperationType
LOG = logging.getLogger()


def dump_cash_flow(report, tag, operation_types=None):
    rur = 0
    usd = 0
    if operation_types:
        result = report.cash_flow.filter_by_type(operation_types)
    else:
        result = report.cash_flow

    for item in result:
        if item.currency == 'RUR':
            rur += item.value
        elif item.currency == 'USD':
            usd += item.value
        else:
            raise Exception('Unknown currency: %s' % item.currency)
    LOG.info('[%s] %s₽, %s$ (%s₽)',
             tag, rur, usd, round(rur + usd * report.usd_price, 2))


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verbose', '-v',
                        action='count',
                        help='verbose logging')
    parser.add_argument('--file', '-f',
                        default='GetBrokerReport.xml',
                        help='broker report file, default: '
                             'GetBrokerReport.xml')
    parser.add_argument('--usd-price',
                        help='USD value in Rubles. If not specified the '
                             'value is gottem form the report')

    return parser.parse_args()


def main():
    parsed_args = parse_args()

    logging_map = {
        0: logging.WARNING,
        1: logging.INFO,
        2: logging.DEBUG,
    }

    LOG.setLevel(logging_map.get(parsed_args.verbose, logging.DEBUG))
    logging.basicConfig(format='%(message)s')

    LOG.info('Processing the report: %s ...', parsed_args.file)
    report = vtb_report.VTBReport(parsed_args.file)

    start_date, end_date = report.report_date
    usd_price = parsed_args.usd_price or report.usd_price
    LOG.info('[Period] %s - %s (%s days)',
             start_date.date(), end_date.date(),
             (end_date - start_date).days)

    usd_price = parsed_args.usd_price or report.usd_price
    LOG.info("[USD price] %s", usd_price)

    LOG.info('---- Cash Flow ----')
    dump_cash_flow(report, 'Fees', OperationType.fees)
    dump_cash_flow(report, 'Taxes', OperationType.taxes)
    dump_cash_flow(report, 'Dividends', OperationType.dividends)
    dump_cash_flow(report, 'Coupons', OperationType.coupons)
    dump_cash_flow(report, 'Credit payments', OperationType.credit_payments)
    dump_cash_flow(report, 'Write offs', OperationType.write_offs)
    dump_cash_flow(report, 'Exhange saldo', OperationType.exhange_saldo)
    dump_cash_flow(report, 'Securities saldo', OperationType.securities_saldo)

    LOG.info('---- Summary ----')
    dump_cash_flow(report, 'Credit payments with write offs',
                   [OperationType.credit_payments, OperationType.write_offs])
    dump_cash_flow(report, 'Total')


if __name__ == '__main__':
    main()
